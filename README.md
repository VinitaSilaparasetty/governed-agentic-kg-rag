# Governed KG-Integrated Multi-Agent RAG System

Portfolio project demonstrating agentic AI system design with structured governance.  
Domain: industrial equipment fault diagnosis and maintenance recommendation.  
Built for PhD application context: Agentic AI and Multi-Agent Systems.

---

## Problem Statement

A maintenance engineer asks: *"Why is Pump-14 vibrating?"*  
A naive LLM-based chatbot would guess or hallucinate. This system instead:

1. Queries a **knowledge graph** (Neo4j) for structured facts — what components Pump-14 has, what fault types those components can exhibit, what procedures resolve each fault.
2. Retrieves **relevant passages** from maintenance manuals (RAG over Chroma) for procedural detail.
3. **Synthesises** both into a candidate diagnosis with a confidence score.
4. Gates the result through a **human-in-the-loop checkpoint** — no recommendation is finalised without operator approval.
5. Writes a **structured audit log** (JSON Lines) at every step, designed to satisfy EU AI Act Article 50 transparency requirements.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Query                           │
│             "Why is Pump-14 vibrating?"                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                ┌────────▼────────┐
                │  Planner Agent   │  decomposes query into
                │  (rule-based)    │  sub-tasks for KG + RAG
                └────────┬────────┘
           ┌─────────────┴──────────────┐
           │                            │
  ┌────────▼────────┐          ┌────────▼────────┐
  │  KG Retrieval   │          │   RAG Agent      │
  │  Agent (Cypher) │          │ (vector search   │
  │  → Neo4j        │          │  over manuals)   │
  │  structured     │          │  unstructured    │
  │  facts          │          │  procedure text  │
  └────────┬────────┘          └────────┬────────┘
           │                            │
           └─────────────┬──────────────┘
                         │
                ┌────────▼────────┐
                │ Synthesis Agent  │  combines KG facts +
                │                  │  RAG text → diagnosis
                │                  │  + confidence score
                └────────┬────────┘
                         │
                ┌────────▼────────┐
                │ HUMAN-IN-LOOP   │◄──── governance gate
                │ Checkpoint       │      approve / reject / edit
                │ (CLI)            │      before any rec. is final
                └────────┬────────┘
                         │
                ┌────────▼────────┐
                │  Audit Log       │◄──── Art. 50 transparency
                │  (JSON Lines)    │      every step logged:
                │                  │      agent, input, output,
                │                  │      sources, confidence,
                │                  │      timestamp, session_id
                └─────────────────┘
```

Orchestrated by a **LangGraph state machine** with conditional edges (e.g. KG returns empty → fallback broadens search scope before routing to RAG).

---

## Repo Structure

```
governed-agentic-kg-rag/
├── data/
│   ├── kg_seed.cypher           # Neo4j seed: 5 equipment, 15 components, 10 faults, 10 procedures
│   └── manuals/                 # 5 maintenance manual text chunks for RAG
├── src/
│   ├── graph/
│   │   ├── schema.py            # Node / relationship type enums
│   │   └── kg_client.py         # Neo4j driver + Cypher helpers
│   ├── rag/
│   │   ├── ingest.py            # Chunk + embed manuals → Chroma
│   │   └── retriever.py         # Vector similarity search
│   ├── agents/
│   │   ├── schemas.py           # Pydantic I/O schemas + AgentState
│   │   ├── planner.py           # Query decomposition
│   │   ├── kg_agent.py          # Cypher generation + Neo4j execution
│   │   ├── rag_agent.py         # Embedding + retrieval
│   │   ├── synthesis_agent.py   # Evidence combination + confidence
│   │   └── graph_workflow.py    # LangGraph graph definition
│   ├── governance/
│   │   ├── audit_log.py         # Append-only JSON Lines log
│   │   └── human_checkpoint.py  # CLI approve/reject/edit gate
│   └── main.py                  # CLI entrypoint
└── tests/
    └── test_agents.py           # Unit tests with mocked Neo4j + Chroma
```

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Docker (for Neo4j)

### 2. Start Neo4j

```bash
docker run -d \
  --name neo4j-kg \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5
```

Browser UI available at http://localhost:7474 (neo4j / password).

### 3. Install dependencies

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env if your Neo4j credentials differ from defaults
```

### 5. Seed the knowledge graph

```bash
python -m src.main --seed
```

### 6. Ingest maintenance manuals

```bash
python -m src.main --ingest
```
This embeds the manual chunks into a local Chroma vector store (`.chroma_db/`).  
Uses `all-MiniLM-L6-v2` by default — no API key required.  
To swap to OpenAI or Anthropic embeddings, set `EMBEDDING_PROVIDER` in `.env`.

### 7. Run a query

```bash
python -m src.main "Why is Pump-14 vibrating?"
```

The pipeline will print a **candidate recommendation** and prompt you to approve, reject, or edit it before the final result is returned.

### 8. Run tests

```bash
pytest tests/ -v
```

---

## Embedding Provider Swap

The system defaults to `sentence-transformers/all-MiniLM-L6-v2` (free, runs locally).  
To use a paid model, set `EMBEDDING_PROVIDER` in `.env`:

| Provider     | `EMBEDDING_PROVIDER` | Extra env vars needed          |
|--------------|----------------------|--------------------------------|
| HuggingFace  | `huggingface`        | none                           |
| OpenAI       | `openai`             | `OPENAI_API_KEY`               |
| Anthropic    | `anthropic`          | `ANTHROPIC_API_KEY`            |

---

## Design Rationale: Connecting Governance to EU AI Act Article 50

Article 50 of the EU AI Act imposes transparency and logging obligations on providers of AI systems that interact with humans or make consequential decisions. This project implements those requirements as first-class architectural features, not afterthoughts:

### Article 50(1)(a) — Record when and how AI was used

Every audit log entry carries `timestamp` (UTC ISO 8601) and `session_id` (UUID per query). This allows an auditor to reconstruct the exact sequence of processing for any query.

### Article 50(1)(b) — Identify the AI system involved

The `agent` field names the specific component that produced each log record (`planner`, `kg_agent`, `rag_agent`, `synthesis_agent`, `human_checkpoint`). Each has a defined, bounded responsibility — auditability requires decomposition.

### Article 50(1)(c) — Record inputs and outputs

`input_data` and `output_data` are logged at every step as structured JSON. This makes it possible to replay any step independently and verify that the output was consistent with the inputs at the time.

### Article 50(1)(d) — Traceability of actions taken

`tool_calls` records every external capability invoked (Cypher query, Chroma similarity search). For the KG agent, the exact Cypher string used is stored inside the output, enabling post-hoc verification that the query was correctly scoped.

### Article 50(1)(e) — Data and knowledge sources used

`sources` records the provenance of all retrieved information — Neo4j node labels and manual filenames. This implements data lineage at the retrieval layer, not just at the output.

### Article 50(2) — Degree of AI confidence

The `confidence` field (0–1) is computed from a combination of KG fault severity and RAG retrieval relevance score. It is logged and displayed to the human operator at the checkpoint, enabling informed human oversight rather than blind acceptance.

### Article 50(3) — Human oversight before consequential output

The `human_checkpoint` node in the LangGraph graph is a **hard gate**: no `FinalOutput` is produced without an explicit human decision (approve / reject / edit). The human's decision and any edit are also logged. This is not optional and cannot be bypassed by the pipeline.

### Design choice: rule-based planner over LLM planner

The Planner uses deterministic keyword matching rather than an LLM. This was deliberate: it makes the planning step fully auditable (no probabilistic intermediate reasoning) and avoids hallucinated sub-tasks. The trade-off is lower generalisation; in a production system, an LLM planner with structured output validation would replace this.

---

## Sample Audit Log Entry

```json
{
  "timestamp": "2026-07-03T09:14:22.341Z",
  "session_id": "c3a1f8d0-...",
  "agent": "kg_agent",
  "input_data": {"sub_tasks": [{"target": "kg", "question": "...", "equipment_name": "Pump-14", "fault_hint": "vibration"}]},
  "output_data": {"results": [{"fault": "Bearing Wear", "severity": "HIGH", ...}], "fallback_used": false},
  "tool_calls": ["neo4j.run_cypher"],
  "sources": ["Neo4j KG"],
  "confidence": 0.85,
  "notes": "fallback_used=False; 3 results"
}
```

---

## Knowledge Graph Schema

```
(:Equipment)-[:HAS_COMPONENT]->(:Component)
(:Component)-[:CAN_EXHIBIT]->(:FaultType)
(:FaultType)-[:RESOLVED_BY]->(:MaintenanceProcedure)
```

Seed data covers: Pump-14, Pump-22, Comp-07, Motor-03, Valve-09 — 15 components, 10 fault types, 10 maintenance procedures.
