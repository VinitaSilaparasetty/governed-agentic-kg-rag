"""
Basic tests for agent functions with mocked Neo4j / Chroma calls.
"""
import pytest
from unittest.mock import patch, MagicMock

from src.agents.schemas import AgentState, PlannerOutput, SubTask, KGResult, RAGChunk
from src.agents.planner import run_planner
from src.agents.kg_agent import run_kg_agent
from src.agents.rag_agent import run_rag_agent
from src.agents.synthesis_agent import run_synthesis_agent


# ── Planner ────────────────────────────────────────────────────────────────

def test_planner_detects_equipment_and_fault():
    state = AgentState(user_query="Why is Pump-14 vibrating?")
    with patch("src.agents.planner.log_step"):
        result = run_planner(state)

    assert result.plan is not None
    kg_tasks = [t for t in result.plan.sub_tasks if t.target == "kg"]
    assert len(kg_tasks) >= 1
    assert any(t.equipment_name == "Pump-14" for t in kg_tasks)
    assert any(t.fault_hint is not None for t in result.plan.sub_tasks)


def test_planner_generic_query_includes_rag():
    state = AgentState(user_query="What maintenance procedures exist?")
    with patch("src.agents.planner.log_step"):
        result = run_planner(state)

    rag_tasks = [t for t in result.plan.sub_tasks if t.target == "rag"]
    assert len(rag_tasks) >= 1


def test_planner_no_equipment_uses_fallback_kg_task():
    state = AgentState(user_query="bearing noise problem")
    with patch("src.agents.planner.log_step"):
        result = run_planner(state)

    assert result.plan is not None
    # Should still produce at least one KG sub-task (fault_hint-driven)
    kg_tasks = [t for t in result.plan.sub_tasks if t.target == "kg"]
    assert len(kg_tasks) >= 1


# ── KG Agent ───────────────────────────────────────────────────────────────

def _make_plan(equipment="Pump-14", fault_hint="vibration"):
    return PlannerOutput(
        original_query="Why is Pump-14 vibrating?",
        sub_tasks=[
            SubTask(target="kg", question="KG sub-task", equipment_name=equipment, fault_hint=fault_hint)
        ],
    )


MOCK_KG_ROW = {
    "equipment": "Pump-14",
    "component": "Bearing-P14-DE",
    "fault": "Bearing Wear",
    "symptoms": ["excessive vibration", "high temperature"],
    "severity": "HIGH",
    "procedure": "Bearing Replacement",
    "steps": ["Isolate", "Remove", "Replace"],
    "estimated_time": "4h",
    "skill_level": "Technician",
}


@patch("src.agents.kg_agent.KGClient")
@patch("src.agents.kg_agent.log_step")
def test_kg_agent_returns_results(mock_log, mock_kg_cls):
    mock_client = MagicMock()
    mock_client.run_cypher.return_value = [MOCK_KG_ROW]
    mock_kg_cls.return_value = mock_client

    state = AgentState(user_query="Why is Pump-14 vibrating?", plan=_make_plan())
    result = run_kg_agent(state)

    assert result.kg_output is not None
    assert len(result.kg_output.results) == 1
    assert result.kg_output.results[0].fault == "Bearing Wear"
    assert result.kg_output.fallback_used is False


@patch("src.agents.kg_agent.KGClient")
@patch("src.agents.kg_agent.log_step")
def test_kg_agent_triggers_fallback_on_empty(mock_log, mock_kg_cls):
    mock_client = MagicMock()
    # First call returns empty; second (fallback) returns data
    mock_client.run_cypher.side_effect = [[],  [MOCK_KG_ROW]]
    mock_kg_cls.return_value = mock_client

    state = AgentState(user_query="Why is Pump-14 vibrating?", plan=_make_plan())
    result = run_kg_agent(state)

    assert result.kg_output is not None
    assert result.kg_output.fallback_used is True
    assert len(result.kg_output.results) >= 1


# ── RAG Agent ──────────────────────────────────────────────────────────────

MOCK_CHUNK = MagicMock()
MOCK_CHUNK.content = "Bearing wear causes vibration at 1x RPM..."
MOCK_CHUNK.source_file = "bearing_wear.txt"
MOCK_CHUNK.score = 0.82


@patch("src.agents.rag_agent.ManualRetriever")
@patch("src.agents.rag_agent.log_step")
def test_rag_agent_returns_chunks(mock_log, mock_retriever_cls):
    mock_retriever = MagicMock()
    mock_retriever.search.return_value = [MOCK_CHUNK]
    mock_retriever_cls.return_value = mock_retriever

    plan = PlannerOutput(
        original_query="pump vibration",
        sub_tasks=[SubTask(target="rag", question="pump vibration")]
    )
    state = AgentState(user_query="pump vibration", plan=plan)
    result = run_rag_agent(state)

    assert result.rag_output is not None
    assert len(result.rag_output.chunks) == 1
    assert result.rag_output.chunks[0].source_file == "bearing_wear.txt"


# ── Synthesis Agent ─────────────────────────────────────────────────────────

@patch("src.agents.synthesis_agent._get_llm")
@patch("src.agents.synthesis_agent.log_step")
def test_synthesis_produces_output(mock_log, mock_get_llm):
    from src.agents.schemas import KGAgentOutput, RAGAgentOutput

    # Mock the Ollama LLM to avoid requiring a running Ollama server in tests
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = (
        "DIAGNOSIS: Bearing Wear detected on Pump-14 bearing Bearing-P14-DE due to excessive vibration.\n"
        "RECOMMENDED ACTION: Perform Bearing Replacement procedure: issue LOTO permit, extract and replace bearing, realign and test."
    )
    mock_llm.invoke.return_value = mock_response
    mock_get_llm.return_value = mock_llm

    plan = PlannerOutput(
        original_query="Why is Pump-14 vibrating?",
        sub_tasks=[SubTask(target="both", question="...", equipment_name="Pump-14", fault_hint="vibration")]
    )
    kg_output = KGAgentOutput(
        sub_task_question="KG q",
        results=[KGResult(
            equipment="Pump-14", component="Bearing-P14-DE",
            fault="Bearing Wear", symptoms=["vibration", "heat"],
            severity="HIGH", procedure="Bearing Replacement",
            steps=["Step 1", "Step 2"], estimated_time="4h", skill_level="Technician"
        )],
    )
    rag_output = RAGAgentOutput(
        sub_task_question="pump vibration",
        chunks=[RAGChunk(content="Bearing wear...", source_file="bearing_wear.txt", score=0.85)]
    )

    state = AgentState(
        user_query="Why is Pump-14 vibrating?",
        plan=plan,
        kg_output=kg_output,
        rag_output=rag_output,
    )
    result = run_synthesis_agent(state)

    assert result.synthesis is not None
    assert "Bearing Wear" in result.synthesis.diagnosis
    assert 0.0 <= result.synthesis.confidence <= 1.0
    assert result.synthesis.recommended_action != ""
    mock_llm.invoke.assert_called_once()


@patch("src.agents.synthesis_agent.log_step")
def test_synthesis_heuristic_fallback_when_llm_unavailable(mock_log):
    """Synthesis must produce valid output even when Ollama is unreachable."""
    from src.agents.schemas import KGAgentOutput, RAGAgentOutput

    plan = PlannerOutput(
        original_query="Why is Motor-03 overheating?",
        sub_tasks=[SubTask(target="both", question="...", equipment_name="Motor-03", fault_hint="overheating")]
    )
    kg_output = KGAgentOutput(
        sub_task_question="KG q",
        results=[KGResult(
            equipment="Motor-03", component="Stator-M03",
            fault="Stator Winding Fault", symptoms=["overheating", "burning smell"],
            severity="CRITICAL", procedure="Stator Rewinding",
            steps=["Step 1"], estimated_time="24h", skill_level="Specialist"
        )],
    )
    rag_output = RAGAgentOutput(sub_task_question="motor overheating", chunks=[])

    state = AgentState(
        user_query="Why is Motor-03 overheating?",
        plan=plan, kg_output=kg_output, rag_output=rag_output,
    )

    with patch("src.agents.synthesis_agent._get_llm", side_effect=Exception("Ollama unavailable")):
        result = run_synthesis_agent(state)

    assert result.synthesis is not None
    assert result.synthesis.diagnosis != ""
    assert result.synthesis.recommended_action != ""
    assert 0.0 <= result.synthesis.confidence <= 1.0


def test_confidence_bounded_for_all_severity_levels():
    """Confidence formula must stay in [0, 1] for every severity × RAG score combination."""
    from src.agents.synthesis_agent import _severity_weight

    for severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW", None):
        for rag_score in (0.0, 0.5, 1.0):
            kg_conf = _severity_weight(severity) * 0.8
            rag_conf = rag_score * 0.6
            confidence = round(min((kg_conf + rag_conf) / 1.4, 1.0), 3)
            assert 0.0 <= confidence <= 1.0, (
                f"Confidence out of bounds for severity={severity}, rag_score={rag_score}: {confidence}"
            )


def test_planner_detects_burn_symptom():
    """'burning smell' / 'overheating' keywords must route to the Stator Winding Fault hint."""
    state = AgentState(user_query="Motor-03 is overheating and smells of burning")
    with patch("src.agents.planner.log_step"):
        result = run_planner(state)

    fault_hints = [t.fault_hint for t in result.plan.sub_tasks if t.fault_hint]
    assert any("Stator" in h for h in fault_hints), (
        f"Expected Stator Winding Fault hint; got: {fault_hints}"
    )
