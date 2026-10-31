"""
Structured append-only audit log — JSON Lines format.

Each record supports the automatic event logging that EU AI Act Article 12 requires
of high-risk AI systems (see the README's Design Rationale for when this system would be one):

Field            Purpose (Article 12 logging)
-----------      ----------------------------
timestamp        when the event occurred
session_id       links all steps of a single query to one run
agent            identifies the AI component responsible
input_data       inputs that triggered the decision/action
output_data      outputs and intermediate decisions produced
tool_calls       tools/capabilities invoked (traceability of actions)
sources          provenance of information used (data lineage)
confidence       evidence-strength score shown to the operator (heuristic, not calibrated)
notes            supplementary human-readable context

Retention (Article 19 / 26(6)) and tamper-evidence are not implemented in this prototype.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", "audit_log.jsonl"))

# One session ID per process invocation — ties all agent steps to a single query.
SESSION_ID = str(uuid.uuid4())


def log_step(
    agent: str,
    input_data: dict[str, Any],
    output_data: dict[str, Any],
    tool_calls: list[str],
    sources: list[str],
    confidence: float,
    notes: str = "",
) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": SESSION_ID,
        "agent": agent,
        "input_data": input_data,
        "output_data": output_data,
        "tool_calls": tool_calls,
        "sources": sources,
        "confidence": round(confidence, 4),
        "notes": notes,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def log_human_decision(decision: str, original: str, edited: str | None) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": SESSION_ID,
        "agent": "human_checkpoint",
        "input_data": {"candidate_recommendation": original},
        "output_data": {"decision": decision, "edited_text": edited},
        "tool_calls": [],
        "sources": ["human"],
        "confidence": 1.0,
        "notes": "Human-in-the-loop gate; no recommendation finalised without approval.",
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
