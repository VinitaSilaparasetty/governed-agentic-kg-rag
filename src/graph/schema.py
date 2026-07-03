"""
Node and relationship type definitions for the industrial equipment KG.
"""
from enum import Enum


class NodeLabel(str, Enum):
    EQUIPMENT = "Equipment"
    COMPONENT = "Component"
    FAULT = "FaultType"
    PROCEDURE = "MaintenanceProcedure"


class RelType(str, Enum):
    HAS_COMPONENT = "HAS_COMPONENT"
    CAN_EXHIBIT = "CAN_EXHIBIT"
    CAUSED_BY = "CAUSED_BY"
    RESOLVED_BY = "RESOLVED_BY"
    REQUIRES = "REQUIRES"
