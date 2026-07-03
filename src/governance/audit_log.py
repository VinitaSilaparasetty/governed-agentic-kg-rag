"""
Structured append-only audit log — JSON Lines format.

Each record captures sufficient information to satisfy EU AI Act Article 50
transparency and traceability requirements for agentic AI systems:

Field            Article 50 mapping
-----------      ------------------
timestamp        Art. 50(1)(a) — record of when processing occurred
agent            Art. 50(1)(b) — identifies the AI component responsible
input_data       Art. 50(1)(c) — inputs that triggered the decision/action
output_data      Art. 50(1)(c) — outputs and intermediate decisions produced
tool_calls       Art. 50(1)(d) — tools/capabilities invoked (traceability of actions)
sources          Art. 50(1)(e) — provenance of information used (data lineage)
confidence       Art. 50(2)    — degree of certainty; enables meaningful human review
notes            Art. 50(1)(f) — supplementary human-readable context
session_id       Art. 50(1)(a) — links all steps of a single query to one run
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
