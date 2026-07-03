"""
Planner agent: decomposes the user query into sub-tasks for KG and RAG agents.
"""
import re

from .schemas import AgentState, PlannerOutput, SubTask
from ..governance.audit_log import log_step


_EQUIPMENT_NAMES = [
    "Pump-14", "Pump-22", "Comp-07", "Motor-03", "Valve-09"
]


def _detect_equipment(query: str) -> str | None:
    for name in _EQUIPMENT_NAMES:
        if name.lower() in query.lower():
            return name
    return None


def _detect_fault_hint(query: str) -> str | None:
    fault_keywords = {
        "vibrat": "vibration",
        "noise": "noise",
        "leak": "Seal Leakage",
        "cavitat": "Impeller Cavitation",
        "bearing": "Bearing Wear",
        "align": "Misalignment",
        "overheating": "Stator Winding Fault",
        "pressure": "Piston Ring Wear",
        "filter": "Filter Fouling",
        "actuator": "Actuator Sticking",
        "valve": "Valve Seat Erosion",
    }
    lower = query.lower()
    for kw, hint in fault_keywords.items():
        if kw in lower:
            return hint
    return None


def run_planner(state: AgentState) -> AgentState:
    query = state.user_query
    equipment = _detect_equipment(query)
    fault_hint = _detect_fault_hint(query)

    sub_tasks: list[SubTask] = []

    if equipment:
        sub_tasks.append(SubTask(
            target="kg",
            question=f"What faults and maintenance procedures are associated with {equipment}?",
            equipment_name=equipment,
            fault_hint=fault_hint,
        ))

    if fault_hint:
        sub_tasks.append(SubTask(
            target="kg",
            question=f"What are the known causes and procedures for '{fault_hint}'?",
            equipment_name=equipment,
            fault_hint=fault_hint,
        ))

    sub_tasks.append(SubTask(
        target="rag",
        question=query,
        equipment_name=equipment,
        fault_hint=fault_hint,
    ))

    if not equipment and not fault_hint:
        sub_tasks.insert(0, SubTask(
            target="kg",
            question="List all equipment and their known fault types.",
            equipment_name=None,
            fault_hint=None,
        ))

    plan = PlannerOutput(original_query=query, sub_tasks=sub_tasks)

    log_step(
        agent="planner",
        input_data={"query": query},
        output_data=plan.model_dump(),
        tool_calls=["_detect_equipment", "_detect_fault_hint"],
        sources=[],
        confidence=0.9,
        notes="Rule-based decomposition; no LLM call.",
    )

    return state.model_copy(update={"plan": plan})
