"""
KG Retrieval agent: translates planner sub-tasks into Cypher and queries Neo4j.
"""
from .schemas import AgentState, KGAgentOutput, KGResult
from ..graph.kg_client import KGClient
from ..governance.audit_log import log_step


def _build_cypher(equipment_name: str | None, fault_hint: str | None) -> tuple[str, dict]:
    if equipment_name and fault_hint:
        cypher = """
        MATCH (e:Equipment {name: $equip})-[:HAS_COMPONENT]->(c:Component)
              -[:CAN_EXHIBIT]->(f:FaultType)
        WHERE toLower(f.name) CONTAINS toLower($fault)
           OR any(s IN f.symptoms WHERE toLower(s) CONTAINS toLower($fault))
        OPTIONAL MATCH (f)-[:RESOLVED_BY]->(p:MaintenanceProcedure)
        RETURN e.name AS equipment, c.name AS component,
               f.name AS fault, f.symptoms AS symptoms, f.severity AS severity,
               p.name AS procedure, p.steps AS steps,
               p.estimated_time AS estimated_time, p.skill_level AS skill_level
        """
        return cypher, {"equip": equipment_name, "fault": fault_hint}

    if equipment_name:
        cypher = """
        MATCH (e:Equipment {name: $equip})-[:HAS_COMPONENT]->(c:Component)
              -[:CAN_EXHIBIT]->(f:FaultType)
        OPTIONAL MATCH (f)-[:RESOLVED_BY]->(p:MaintenanceProcedure)
        RETURN e.name AS equipment, c.name AS component,
               f.name AS fault, f.symptoms AS symptoms, f.severity AS severity,
               p.name AS procedure, p.steps AS steps,
               p.estimated_time AS estimated_time, p.skill_level AS skill_level
        """
        return cypher, {"equip": equipment_name}

    if fault_hint:
        cypher = """
        MATCH (f:FaultType)
        WHERE toLower(f.name) CONTAINS toLower($fault)
           OR any(s IN f.symptoms WHERE toLower(s) CONTAINS toLower($fault))
        OPTIONAL MATCH (f)-[:RESOLVED_BY]->(p:MaintenanceProcedure)
        RETURN null AS equipment, null AS component,
               f.name AS fault, f.symptoms AS symptoms, f.severity AS severity,
               p.name AS procedure, p.steps AS steps,
               p.estimated_time AS estimated_time, p.skill_level AS skill_level
        """
        return cypher, {"fault": fault_hint}

    cypher = """
    MATCH (f:FaultType)
    OPTIONAL MATCH (f)-[:RESOLVED_BY]->(p:MaintenanceProcedure)
    RETURN null AS equipment, null AS component,
           f.name AS fault, f.symptoms AS symptoms, f.severity AS severity,
           p.name AS procedure, p.steps AS steps,
           p.estimated_time AS estimated_time, p.skill_level AS skill_level
    LIMIT 10
    """
    return cypher, {}


def run_kg_agent(state: AgentState) -> AgentState:
    if not state.plan:
        return state.model_copy(update={"error": "KG agent: no plan available"})

    kg_sub_tasks = [t for t in state.plan.sub_tasks if t.target in ("kg", "both")]
    if not kg_sub_tasks:
        return state

    client = KGClient()
    all_results: list[KGResult] = []
    fallback_used = False
    cyphers_used: list[str] = []
    primary_question = kg_sub_tasks[0].question

    try:
        for sub_task in kg_sub_tasks:
            cypher, params = _build_cypher(sub_task.equipment_name, sub_task.fault_hint)
            rows = client.run_cypher(cypher, params)
            cyphers_used.append(cypher.strip())

            if not rows and sub_task.equipment_name:
                # fallback: broaden to symptom-only search
                fallback_cypher = """
                MATCH (f:FaultType)
                WHERE any(s IN f.symptoms WHERE toLower(s) CONTAINS 'vibrat')
                OPTIONAL MATCH (f)-[:RESOLVED_BY]->(p:MaintenanceProcedure)
                RETURN null AS equipment, null AS component,
                       f.name AS fault, f.symptoms AS symptoms, f.severity AS severity,
                       p.name AS procedure, p.steps AS steps,
                       p.estimated_time AS estimated_time, p.skill_level AS skill_level
                """
                rows = client.run_cypher(fallback_cypher)
                cyphers_used.append(fallback_cypher.strip())
                fallback_used = True

            for row in rows:
                all_results.append(KGResult(
                    equipment=row.get("equipment"),
                    component=row.get("component"),
                    fault=row.get("fault"),
                    symptoms=row.get("symptoms") or [],
                    severity=row.get("severity"),
                    procedure=row.get("procedure"),
                    steps=row.get("steps") or [],
                    estimated_time=row.get("estimated_time"),
                    skill_level=row.get("skill_level"),
                    cypher_used=cypher.strip(),
                    rows_returned=len(rows),
                ))
    finally:
        client.close()

    output = KGAgentOutput(
        sub_task_question=primary_question,
        results=all_results,
        fallback_used=fallback_used,
    )

    log_step(
        agent="kg_agent",
        input_data={"sub_tasks": [t.model_dump() for t in kg_sub_tasks]},
        output_data=output.model_dump(),
        tool_calls=["neo4j.run_cypher"] * len(cyphers_used),
        sources=["Neo4j KG"],
        confidence=0.85 if all_results else 0.2,
        notes=f"fallback_used={fallback_used}; {len(all_results)} results",
    )

    return state.model_copy(update={"kg_output": output})
