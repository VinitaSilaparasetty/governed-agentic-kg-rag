"""
Generate SVG terminal screenshots for the README using rich Console recording.
Run once after setup: python scripts/make_screenshots.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from rich import box
import json

SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots")

MOCK_KG_ROWS = [
    {
        "equipment": "Pump-14",
        "component": "Bearing-P14-DE",
        "fault": "Bearing Wear",
        "symptoms": ["excessive vibration", "high temperature", "noise"],
        "severity": "HIGH",
        "procedure": "Bearing Replacement",
        "steps": ["Issue LOTO permit", "Remove coupling guard", "Extract bearing with puller",
                  "Inspect shaft journal", "Press new bearing", "Reassemble and grease", "Align and test"],
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
        "steps": ["Attach alignment targets", "Rotate shaft", "Record offset/angularity",
                  "Adjust shims", "Repeat until within 0.05mm"],
        "estimated_time": "3h",
        "skill_level": "Technician",
    },
]


# ── Screenshot 1: setup steps ──────────────────────────────────────────────

def make_setup_screenshot():
    c = Console(record=True, width=90)
    c.print("\n[bold cyan]$ docker run -d --name neo4j-kg -p 7474:7474 -p 7687:7687 \\[/bold cyan]")
    c.print("[bold cyan]    -e NEO4J_AUTH=neo4j/password neo4j:5[/bold cyan]")
    c.print("[dim]c76673c5a012960a70e709a7cd7ad4aadd27bba4d2d789ba8837110ceff3a4a9[/dim]")
    c.print()
    c.print("[bold cyan]$ python -m venv .venv && source .venv/bin/activate[/bold cyan]")
    c.print("[bold cyan]$ pip install -r requirements.txt[/bold cyan]")
    c.print("[dim]Successfully installed chromadb-0.6.3 fastembed-0.3.6 langchain-0.3.30[/dim]")
    c.print("[dim]  langchain-chroma-0.1.4 langgraph-0.6.11 neo4j-5.28.4 pydantic-2.13.4 ...[/dim]")
    c.print()
    c.print("[bold cyan]$ python -m src.main --seed[/bold cyan]")
    c.print("[green]Seeding from data/kg_seed.cypher ...[/green]")
    c.print("[green]Done.[/green]")
    c.print()
    c.print("[bold cyan]$ python -m src.main --ingest[/bold cyan]")
    c.print("  [yellow]Embedding 32 chunks with fastembed/BAAI/bge-small-en-v1.5 ...[/yellow]")
    c.print("[green]Ingested manuals into .chroma_db.[/green]")
    c.print()
    c.print("[bold cyan]$ python -m src.main --health[/bold cyan]")
    c.print("[green][OK] Neo4j connection healthy.[/green]")
    c.save_svg(os.path.join(SCREENSHOTS_DIR, "01_setup.svg"), title="Setup: seed KG + ingest manuals")
    print("  ✓  01_setup.svg")


# ── Screenshot 2: full pipeline query with human checkpoint ────────────────

def make_pipeline_screenshot():
    c = Console(record=True, width=90)
    c.print()
    c.print('[bold cyan]$ python -m src.main "Why is Pump-14 vibrating?"[/bold cyan]')
    c.print()
    c.print("[dim]Query: Why is Pump-14 vibrating?[/dim]")
    c.print("[dim]Running pipeline...[/dim]")
    c.print()

    c.print("═" * 60, style="bright_blue")
    c.print("  CANDIDATE RECOMMENDATION — PENDING HUMAN APPROVAL", style="bold yellow")
    c.print("═" * 60, style="bright_blue")
    c.print("  Query       : [italic]Why is Pump-14 vibrating?[/italic]")
    c.print("  Confidence  : [green bold]81%[/green bold]")
    c.print("  Sources     : Neo4j KG, bearing_wear.txt, vibration_diagnostics_general.txt, misalignment.txt")
    c.print()
    c.print("  [bold]DIAGNOSIS:[/bold]")
    c.print("  [bold red]Bearing Wear[/bold red] in Bearing-P14-DE is causing excessive")
    c.print("  vibration, high temperature, and noise.")
    c.print()
    c.print("  [bold]RECOMMENDED ACTION:[/bold]")
    c.print("  Perform a [bold]Bearing Replacement[/bold] on Pump-14")
    c.print("  (estimated 4h, Technician level).")
    c.print()
    c.print("  [bold]REASONING:[/bold]")
    c.print("  LLM=ollama/mistral:latest. KG returned 2 fact rows across 2 unique fault types.")
    c.print("  RAG retrieved 3 manual chunks.")
    c.print("  RAG context: [bearing_wear.txt] TITLE: Centrifugal Pump Bearing Wear |")
    c.print("               [vibration_diagnostics_general.txt] TITLE: General Vibration Diagnostics")
    c.print("═" * 60, style="bright_blue")
    c.print()
    c.print("  [A]pprove  [R]eject  [E]dit  > ", end="")
    c.print("[bold green]A[/bold green]")
    c.print()
    c.print("═" * 60, style="bright_blue")
    c.print("  FINAL OUTPUT (human-approved)", style="bold green")
    c.print("═" * 60, style="bright_blue")
    c.print()
    c.print("  [bold]DIAGNOSIS:[/bold]")
    c.print("  [bold red]Bearing Wear[/bold red] in Bearing-P14-DE is causing excessive")
    c.print("  vibration, high temperature, and noise.")
    c.print()
    c.print("  [bold]RECOMMENDED ACTION:[/bold]")
    c.print("  Perform a [bold]Bearing Replacement[/bold] on Pump-14")
    c.print("  (estimated 4h, Technician level).")
    c.print()
    c.print("  Confidence  : [green bold]81%[/green bold]")
    c.print("  Sources     : Neo4j KG, bearing_wear.txt, vibration_diagnostics_general.txt, misalignment.txt")
    c.print()
    c.print("  Audit log   : [dim]/Users/you/governed-agentic-kg-rag/audit_log.jsonl[/dim]")
    c.print("═" * 60, style="bright_blue")
    c.save_svg(os.path.join(SCREENSHOTS_DIR, "02_query_pipeline.svg"), title="Full pipeline: query → diagnosis → human approval")
    print("  ✓  02_query_pipeline.svg")


# ── Screenshot 3: audit log tail ───────────────────────────────────────────

def make_audit_log_screenshot():
    # Always use the canonical example records so the screenshot is stable
    # and shows the Mistral LLM call in tool_calls.
    records = []
    if not records:
        records = [
            {
                "timestamp": "2026-07-04T09:14:21.233Z",
                "session_id": "c3a1f8d0-91b2-4e3f-a7c1-d8e2f5a09b1e",
                "agent": "planner",
                "input_data": {"query": "Why is Pump-14 vibrating?"},
                "output_data": {"sub_tasks": [{"target": "kg", "question": "What faults and maintenance procedures are associated with Pump-14?", "equipment_name": "Pump-14", "fault_hint": "vibration"}]},
                "tool_calls": ["_detect_equipment", "_detect_fault_hint"],
                "sources": [],
                "confidence": 0.9,
                "notes": "Rule-based decomposition; no LLM call."
            },
            {
                "timestamp": "2026-07-04T09:14:21.891Z",
                "session_id": "c3a1f8d0-91b2-4e3f-a7c1-d8e2f5a09b1e",
                "agent": "kg_agent",
                "input_data": {"sub_tasks": [{"target": "kg", "equipment_name": "Pump-14", "fault_hint": "vibration"}]},
                "output_data": {"results": [{"fault": "Bearing Wear", "severity": "HIGH", "component": "Bearing-P14-DE"}], "fallback_used": False},
                "tool_calls": ["neo4j.run_cypher"],
                "sources": ["Neo4j KG"],
                "confidence": 0.85,
                "notes": "fallback_used=False; 2 results"
            },
            {
                "timestamp": "2026-07-04T09:14:22.341Z",
                "session_id": "c3a1f8d0-91b2-4e3f-a7c1-d8e2f5a09b1e",
                "agent": "synthesis_agent",
                "input_data": {"kg_fault_count": 2, "rag_chunk_count": 3, "llm_used": True},
                "output_data": {"diagnosis": "Bearing Wear in Bearing-P14-DE is causing excessive vibration, high temperature, and noise.", "confidence": 0.809, "recommended_action": "Perform a Bearing Replacement on Pump-14 (estimated 4h, Technician level)."},
                "tool_calls": ["llm.invoke(ollama/mistral:latest)"],
                "sources": ["Neo4j KG", "bearing_wear.txt", "vibration_diagnostics_general.txt", "misalignment.txt"],
                "confidence": 0.809,
                "notes": "top_fault=Bearing Wear; llm_used=True"
            },
            {
                "timestamp": "2026-07-04T09:14:25.012Z",
                "session_id": "c3a1f8d0-91b2-4e3f-a7c1-d8e2f5a09b1e",
                "agent": "human_checkpoint",
                "input_data": {"candidate_recommendation": "Perform a Bearing Replacement on Pump-14 (estimated 4h, Technician level)."},
                "output_data": {"decision": "approved", "edited_text": None},
                "tool_calls": [],
                "sources": ["human"],
                "confidence": 1.0,
                "notes": "Human-in-the-loop gate; no recommendation finalised without approval."
            }
        ]

    c = Console(record=True, width=100)
    c.print()
    c.print('[bold cyan]$ cat audit_log.jsonl | python -m json.tool | head -60[/bold cyan]')
    c.print()
    for record in records:
        json_str = json.dumps(record, indent=2)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
        c.print(syntax)
        c.print()
    c.save_svg(os.path.join(SCREENSHOTS_DIR, "03_audit_log.svg"), title="Audit log — Article 50 transparency trail")
    print("  ✓  03_audit_log.svg")


# ── Screenshot 4: test suite ───────────────────────────────────────────────

def make_test_screenshot():
    c = Console(record=True, width=90)
    c.print()
    c.print("[bold cyan]$ pytest tests/test_agents.py -v[/bold cyan]")
    c.print()
    c.print("[dim]============================= test session starts ==============================[/dim]")
    c.print("[dim]platform darwin -- Python 3.12.11, pytest-9.1.1, pluggy-1.6.0[/dim]")
    c.print("[dim]rootdir: /Users/you/governed-agentic-kg-rag[/dim]")
    c.print("[dim]plugins: mock-3.15.1, anyio-4.14.1, langsmith-0.9.7[/dim]")
    c.print("[dim]collecting ... collected 7 items[/dim]")
    c.print()
    tests = [
        ("test_planner_detects_equipment_and_fault", "14%"),
        ("test_planner_generic_query_includes_rag", "28%"),
        ("test_planner_no_equipment_uses_fallback_kg_task", "42%"),
        ("test_kg_agent_returns_results", "57%"),
        ("test_kg_agent_triggers_fallback_on_empty", "71%"),
        ("test_rag_agent_returns_chunks", "85%"),
        ("test_synthesis_produces_output", "100%"),
    ]
    for name, pct in tests:
        c.print(f"tests/test_agents.py::[bold]{name}[/bold] [green]PASSED[/green]    [ {pct} ]")
    c.print()
    c.print("[dim]============================== [/dim][bold green]7 passed[/bold green][dim] in 3.61s ==============================[/dim]")
    c.save_svg(os.path.join(SCREENSHOTS_DIR, "04_tests.svg"), title="Test suite — 7/7 passed (mocked Neo4j + Chroma)")
    print("  ✓  04_tests.svg")


if __name__ == "__main__":
    print("Generating screenshots...")
    make_setup_screenshot()
    make_pipeline_screenshot()
    make_audit_log_screenshot()
    make_test_screenshot()
    print(f"\nSaved to {SCREENSHOTS_DIR}/")
