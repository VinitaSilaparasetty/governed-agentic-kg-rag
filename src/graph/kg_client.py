"""
Neo4j connection and Cypher query helpers.
"""
import os
from typing import Any

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable


class KGClient:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def query(self, cypher: str, params: dict | None = None) -> list[dict[str, Any]]:
        params = params or {}
        with self._driver.session() as session:
            result = session.run(cypher, params)
            return [record.data() for record in result]

    def health_check(self) -> bool:
        try:
            self.query("RETURN 1 AS ok")
            return True
        except ServiceUnavailable:
            return False

    def seed(self, cypher_path: str):
        with open(cypher_path) as f:
            statements = [s.strip() for s in f.read().split(";") if s.strip()]
        with self._driver.session() as session:
            for stmt in statements:
                session.run(stmt)

    # ---------- domain helpers ----------

    def get_equipment_faults(self, equipment_name: str) -> list[dict]:
        cypher = """
        MATCH (e:Equipment {name: $name})-[:HAS_COMPONENT]->(c:Component)
              -[:CAN_EXHIBIT]->(f:FaultType)
        RETURN e.name AS equipment,
               c.name AS component,
               f.name AS fault,
               f.symptoms AS symptoms,
               f.severity AS severity
        """
        return self.query(cypher, {"name": equipment_name})

    def get_fault_procedures(self, fault_name: str) -> list[dict]:
        cypher = """
        MATCH (f:FaultType {name: $name})-[:RESOLVED_BY]->(p:MaintenanceProcedure)
        RETURN f.name AS fault,
               p.name AS procedure,
               p.steps AS steps,
               p.estimated_time AS estimated_time,
               p.skill_level AS skill_level
        """
        return self.query(cypher, {"name": fault_name})

    def get_component_faults(self, component_name: str) -> list[dict]:
        cypher = """
        MATCH (c:Component {name: $name})-[:CAN_EXHIBIT]->(f:FaultType)
        OPTIONAL MATCH (f)-[:RESOLVED_BY]->(p:MaintenanceProcedure)
        RETURN c.name AS component,
               f.name AS fault,
               f.symptoms AS symptoms,
               collect(p.name) AS procedures
        """
        return self.query(cypher, {"name": component_name})

    def run_cypher(self, cypher: str, params: dict | None = None) -> list[dict]:
        """Execute arbitrary Cypher (used by the KG agent)."""
        return self.query(cypher, params)
