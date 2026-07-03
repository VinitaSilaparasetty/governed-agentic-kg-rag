"""
Demo runner: executes the full pipeline with a stubbed Neo4j connection
so the pipeline can run without a live database.

Usage: python scripts/demo_run.py
This is for demonstration/screenshot purposes only.
Real usage: python -m src.main "Why is Pump-14 vibrating?"
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock

MOCK_KG_ROWS = [
    {
        "equipment": "Pump-14",
        "component": "Bearing-P14-DE",
        "fault": "Bearing Wear",
        "symptoms": ["excessive vibration", "high temperature", "noise"],
        "severity": "HIGH",
        "procedure": "Bearing Replacement",
        "steps": [
            "Issue LOTO permit",
            "Remove coupling guard",
            "Extract bearing with puller",
            "Inspect shaft journal",
            "Press new bearing",
            "Reassemble and grease",
            "Align and test",
        ],
        "estimated_time": "4h",
        "skill_level": "Technician",
    },
    {
        "equipment": "Pump-14",
        "component": "Coupling-P14",
        "fault": "Misalignment",
        "symptoms": ["vibration", "coupling heat", "axial thrust"],
        "severity": "MEDIUM",
        "procedure": "Laser Alignment",
        "steps": [
            "Attach alignment targets",
            "Rotate shaft",
            "Record offset/angularity",
            "Adjust shims",
            "Repeat until within 0.05mm",
        ],
        "estimated_time": "3h",
        "skill_level": "Technician",
    },
]


def _mock_kg_client(*args, **kwargs):
    client = MagicMock()
    client.run_cypher.return_value = MOCK_KG_ROWS
    client.close.return_value = None
    return client


# Auto-approve so demo runs non-interactively
def _auto_approve(state):
    from src.agents.schemas import FinalOutput
    synthesis = state.synthesis
    final = FinalOutput(
        user_query=state.user_query,
        diagnosis=synthesis.diagnosis,
        recommended_action=synthesis.recommended_action,
        confidence=synthesis.confidence,
        evidence_sources=synthesis.evidence_sources,
        reasoning=synthesis.reasoning,
        human_approved=True,
    )
    from src.governance.audit_log import log_human_decision
    log_human_decision("approved", synthesis.recommended_action, None)
    return state.model_copy(update={"final": final})


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    query = "Why is Pump-14 vibrating?"
    print(f"\nQuery: {query}")
    print("Running pipeline...\n")

    with patch("src.agents.kg_agent.KGClient", side_effect=_mock_kg_client), \
         patch("src.agents.graph_workflow.run_human_checkpoint", side_effect=_auto_approve):

        from src.agents.graph_workflow import run_pipeline
        final_state = run_pipeline(query)

    if final_state.final:
        f = final_state.final
        print("\n" + "═" * 60)
        print("  FINAL OUTPUT (human-approved)")
        print("═" * 60)
        print(f"\n  DIAGNOSIS:\n  {f.diagnosis}")
        print(f"\n  RECOMMENDED ACTION:\n  {f.recommended_action}")
        print(f"\n  Confidence  : {f.confidence:.0%}")
        print(f"  Sources     : {', '.join(f.evidence_sources)}")
        from src.governance.audit_log import LOG_PATH
        print(f"\n  Audit log   : {LOG_PATH.resolve()}")
        print("═" * 60)
