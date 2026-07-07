"""
LangGraph state machine wiring all agents together.

Graph topology:
  planner → [kg_agent, rag_agent] (parallel) → synthesis → human_checkpoint → END
  kg_agent: if KG empty → fallback still runs, flag set
  Any node that sets state.error → routed to error_handler → END
"""
from langgraph.graph import StateGraph, END

from .schemas import AgentState
from .planner import run_planner
from .kg_agent import run_kg_agent
from .rag_agent import run_rag_agent
from .synthesis_agent import run_synthesis_agent
from ..governance.human_checkpoint import run_human_checkpoint
from ..governance.audit_log import log_step


def _error_handler(state: AgentState) -> AgentState:
    log_step(
        agent="error_handler",
        input_data={"error": state.error},
        output_data={},
        tool_calls=[],
        sources=[],
        confidence=0.0,
        notes="Pipeline terminated due to error.",
    )
    print(f"\n[ERROR] Pipeline halted: {state.error}")
    return state


def _route_after_planner(state: AgentState) -> str:
    if state.error:
        return "error_handler"
    return "kg_agent"


def _route_after_kg(state: AgentState) -> str:
    if state.error:
        return "error_handler"
    return "rag_agent"


def _route_after_rag(state: AgentState) -> str:
    if state.error:
        return "error_handler"
    return "synthesis"


def _route_after_synthesis(state: AgentState) -> str:
    if state.error:
        return "error_handler"
    return "human_checkpoint"


def _route_after_checkpoint(state: AgentState) -> str:
    if state.error:
        return "error_handler"
    return END


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("planner", run_planner)
    graph.add_node("kg_agent", run_kg_agent)
    graph.add_node("rag_agent", run_rag_agent)
    graph.add_node("synthesis", run_synthesis_agent)
    graph.add_node("human_checkpoint", run_human_checkpoint)
    graph.add_node("error_handler", _error_handler)

    graph.set_entry_point("planner")

    graph.add_conditional_edges("planner", _route_after_planner,
                                {"kg_agent": "kg_agent", "error_handler": "error_handler"})
    graph.add_conditional_edges("kg_agent", _route_after_kg,
                                {"rag_agent": "rag_agent", "error_handler": "error_handler"})
    graph.add_conditional_edges("rag_agent", _route_after_rag,
                                {"synthesis": "synthesis", "error_handler": "error_handler"})
    graph.add_conditional_edges("synthesis", _route_after_synthesis,
                                {"human_checkpoint": "human_checkpoint", "error_handler": "error_handler"})
    graph.add_conditional_edges("human_checkpoint", _route_after_checkpoint,
                                {END: END, "error_handler": "error_handler"})
    graph.add_edge("error_handler", END)

    return graph.compile()


def run_pipeline(user_query: str) -> AgentState:
    app = build_graph()
    initial = AgentState(user_query=user_query)
    final_state = app.invoke(initial)
    return AgentState(**final_state)


def run_pipeline_mode(user_query: str, mode: str = "full") -> AgentState:
    """Run the pipeline without the HITL checkpoint, for ablation comparisons.

    mode: "full" | "kg_only" | "rag_only"
      kg_only  — RAG chunks are suppressed before synthesis
      rag_only — KG results are suppressed before synthesis
    """
    graph = StateGraph(AgentState)
    graph.add_node("planner", run_planner)
    graph.add_node("kg_agent", run_kg_agent)
    graph.add_node("rag_agent", run_rag_agent)
    graph.add_node("synthesis", run_synthesis_agent)
    graph.add_node("error_handler", _error_handler)

    graph.set_entry_point("planner")
    graph.add_conditional_edges("planner", _route_after_planner,
                                {"kg_agent": "kg_agent", "error_handler": "error_handler"})
    graph.add_conditional_edges("kg_agent", _route_after_kg,
                                {"rag_agent": "rag_agent", "error_handler": "error_handler"})
    graph.add_conditional_edges("rag_agent", _route_after_rag,
                                {"synthesis": "synthesis", "error_handler": "error_handler"})
    graph.add_edge("synthesis", END)
    graph.add_edge("error_handler", END)

    app = graph.compile()
    initial = AgentState(user_query=user_query, mode=mode)
    final_state = app.invoke(initial)
    return AgentState(**final_state)
