#!/usr/bin/env python3
"""
CLI entrypoint — runs a user query through the full governed multi-agent pipeline.

Usage:
    python -m src.main "Why is Pump-14 vibrating?"
    python -m src.main --seed          # seed Neo4j from data/kg_seed.cypher
    python -m src.main --ingest        # (re-)ingest manuals into Chroma
    python -m src.main --health        # check Neo4j connectivity
"""
import argparse
import json
import sys
from pathlib import Path


def cmd_health():
    from .graph.kg_client import KGClient
    client = KGClient()
    ok = client.health_check()
    client.close()
    if ok:
        print("[OK] Neo4j connection healthy.")
    else:
        print("[FAIL] Cannot reach Neo4j. Check NEO4J_URI / credentials.")
        sys.exit(1)


def cmd_seed():
    from .graph.kg_client import KGClient
    seed_path = Path(__file__).parents[1] / "data" / "kg_seed.cypher"
    client = KGClient()
    print(f"Seeding from {seed_path} ...")
    client.seed(str(seed_path))
    client.close()
    print("Done.")


def cmd_ingest():
    from .rag.ingest import ingest_manuals
    import shutil
    chroma_dir = Path(__file__).parents[1] / ".chroma_db"
    if chroma_dir.exists():
        shutil.rmtree(chroma_dir)
        print("Cleared existing Chroma store.")
    store = ingest_manuals()
    print(f"Ingested manuals into {chroma_dir}.")


def cmd_query(query: str):
    from .agents.graph_workflow import run_pipeline
    from .governance.audit_log import LOG_PATH

    print(f"\nQuery: {query}")
    print("Running pipeline...\n")

    final_state = run_pipeline(query)

    if final_state.final:
        f = final_state.final
        print("\n" + "═" * 60)
        if f.human_approved:
            print("  FINAL OUTPUT (human-approved)")
            print("═" * 60)
            print(f"\n  DIAGNOSIS:\n  {f.diagnosis}")
            print(f"\n  RECOMMENDED ACTION:\n  {f.recommended_action}")
            if f.human_edit:
                print("  [Human-edited recommendation]")
        else:
            print("  OUTPUT REJECTED — no action taken.")
        print(f"\n  Confidence  : {f.confidence:.0%}")
        print(f"  Sources     : {', '.join(f.evidence_sources)}")
        print(f"\n  Audit log   : {LOG_PATH.resolve()}")
        print("═" * 60)
    elif final_state.error:
        print(f"\n[ERROR] {final_state.error}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Governed KG-Integrated Multi-Agent RAG")
    parser.add_argument("query", nargs="?", help="Diagnostic query to run")
    parser.add_argument("--seed", action="store_true", help="Seed Neo4j with sample data")
    parser.add_argument("--ingest", action="store_true", help="(Re-)ingest manuals into Chroma")
    parser.add_argument("--health", action="store_true", help="Check Neo4j connectivity")

    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    if args.health:
        cmd_health()
    elif args.seed:
        cmd_seed()
    elif args.ingest:
        cmd_ingest()
    elif args.query:
        cmd_query(args.query)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
