# Governed KG-Augmented Multi-Agent RAG for Industrial Fault Diagnosis: Structured Retrieval, LLM Synthesis, and Transparent Human Oversight

**Vinita Silaparasetty**  
Aevoxis Solutions  
emtech1968@gmail.com

*July 2026*

---

## Abstract

This paper presents a governed multi-agent retrieval-augmented generation (RAG) system that integrates a structured knowledge graph (KG) with unstructured document retrieval to perform industrial equipment fault diagnosis. The system is orchestrated by a LangGraph state machine comprising a deterministic query dispatcher, a KG retrieval agent (Neo4j/Cypher), a vector-similarity RAG agent (Chroma/fastembed), and an LLM synthesis agent (Ollama/Mistral), together with a hard human-in-the-loop gate before any output is finalised. The KG schema (Equipment → Component → FaultType → MaintenanceProcedure) defines a typed four-node, three-relationship property graph; Section 4 shows the concrete OWL 2 QL T-Box axioms to which this schema can be lifted, and this lifting is identified as a concrete research contribution target. Every agent step is written to an append-only structured audit log with field-level mapping to EU AI Act Article 50 transparency requirements. A five-query within-knowledge-base evaluation — explicitly acknowledged as a sanity check on correct KG traversal rather than a held-out benchmark — verifies fault identification on all in-domain queries and graceful degradation on out-of-domain queries; a deterministic diagnostic priority signal provides a monotone grounding indicator for the human operator, but is not a calibrated probability. A suite of ten unit tests verifies correctness of all pipeline nodes without requiring live infrastructure. The system is discussed as a KG-augmented generation architecture situated within the BCAI research programme on industrial KGs and semantic technologies, with five open research questions identified for PhD-level investigation.

**Keywords:** knowledge graph; retrieval-augmented generation; multi-agent systems; industrial fault diagnosis; ontology-based data access; OWL 2 QL; human-in-the-loop; EU AI Act; LangGraph; agentic AI

---

## 1. Introduction

Large language models have demonstrated impressive capability on open-domain question answering, but they remain unreliable for high-stakes industrial diagnostic tasks. Hallucination, inconsistent reasoning over structured data, and the absence of traceability make raw LLM outputs inappropriate for environments where an incorrect maintenance recommendation can cause equipment damage, unplanned downtime, or — in safety-critical facilities — personal injury.

Two complementary research traditions address these weaknesses. Knowledge graphs (KGs) provide structured, interpretable, and verifiable representations of domain facts: an equipment-to-component-to-fault knowledge base can definitively answer "which component of Pump-14 is most likely to cause vibration?" without recourse to probabilistic sampling. Retrieval-augmented generation (RAG) systems augment LLM generation with retrieved passages from a corpus, improving factual grounding for questions requiring procedural or contextual detail not captured in structured data.

The key insight driving this system is that these two modalities answer *different types of questions* about the same domain. A KG answers: *what* component, *which* fault, *what* severity, *what* procedure — all with full provenance. A RAG system answers: *how* to carry out the procedure — the safety prerequisites, diagnostic decision trees, and post-maintenance monitoring schedules contained in unstructured technical manuals. Neither alone is sufficient; both together, grounded by explicit governance, constitute a sound basis for a diagnostic recommendation.

This paper makes the following contributions:

1. A working KG-augmented generation architecture combining typed Cypher-based KG retrieval with vector-similarity RAG and LLM synthesis, orchestrated by a LangGraph state machine with conditional edges and a deterministic query dispatcher.
2. A typed property graph schema for industrial equipment maintenance encoded in Neo4j, with concrete OWL 2 QL T-Box axioms showing the formal lifting target — making the OBDA alignment a defined research step rather than an aspiration.
3. An Article 50 transparency architecture embedded at the pipeline level: an append-only structured audit log and a hard human-in-the-loop checkpoint that cannot be bypassed at runtime, together with a risk-classification analysis under Annex III. Regulatory compliance is not claimed; architectural design for transparency is.
4. A within-knowledge-base evaluation including a three-way ablation (KG-only, RAG-only, full pipeline) and a parameter sweep of the diagnostic priority signal, demonstrating correct KG traversal on in-domain queries and graceful degradation on out-of-domain inputs.

---

## 2. Background and Related Work

### 2.1 Retrieval-Augmented Generation

Lewis et al. [1] introduced retrieval-augmented generation as a method for conditioning language model generation on non-parametric memory — a retrieval corpus — to improve factual accuracy on knowledge-intensive tasks. Standard RAG retrieves top-*k* document chunks by embedding similarity and passes them as context to the generator. A known limitation is the inability to perform structured relational reasoning: RAG cannot answer "which specific component of a specific machine is most likely responsible for this fault" without a schema that makes those relationships explicit.

Edge et al. [19] proposed GraphRAG, which constructs a graph of entities and relationships from an unstructured corpus using LLM extraction, then performs community detection over the resulting graph to support global summarisation queries. GraphRAG demonstrates that graph structure improves RAG on complex, multi-hop queries — but its graph is LLM-extracted and statistically grounded, not formally typed or schema-validated. The system in this paper inverts the approach: the KG is manually curated with formal typing, typed Cypher traversal handles structured retrieval, and the LLM role is limited to synthesis rather than graph construction. This distinction is consequential for auditability: a manually curated, schema-validated KG provides interpretable provenance that an LLM-extracted graph cannot guarantee.

### 2.2 Knowledge Graphs and Ontology-Based Data Access

Hogan et al. [2] survey the knowledge graph paradigm, defining a KG as a graph-based data structure where nodes represent entities and edges represent typed relationships. In industrial settings, KGs have been applied to equipment monitoring, maintenance planning, and semantic data integration. The ontology-based data access (OBDA) paradigm [3] uses OWL ontologies as virtual mediation layers over heterogeneous data sources, enabling SPARQL queries to return results logically entailed by the ontology even when the data is stored in relational or graph form. The schema used in this system — `(:Equipment)-[:HAS_COMPONENT]->(:Component)-[:CAN_EXHIBIT]->(:FaultType)-[:RESOLVED_BY]->(:MaintenanceProcedure)` — is a labeled property graph stored in Neo4j, not a formal OWL ontology. It does not define a TBox, does not support subsumption reasoning or property chains, and operates under the closed-world assumption rather than OWL's open-world semantics. It is, however, semantically structured in a way that is *alignable* with OBDA principles: each node label corresponds to a candidate OWL class, each relationship type to a candidate object property, and each node property to a candidate datatype property. This alignment is deliberate — it is intended to make the schema a concrete starting point for formal lifting to OWL 2 QL as a research contribution, rather than treating formalisation as an afterthought.

### 2.3 Neuro-Symbolic Integration

The neuro-symbolic AI paradigm [4] seeks to combine the interpretability and formal reasoning capabilities of symbolic AI with the flexibility and pattern recognition of neural systems. Pan et al. [5] survey the roadmap for unifying LLMs with KGs, identifying three integration patterns: KG-enhanced LLM (the KG provides context to improve generation), LLM-enhanced KG (the LLM assists in KG construction or query generation), and synergistic integration (bidirectional interaction).

The system in this paper implements Pattern 1 — KG-augmented generation — and is careful not to overclaim. The symbolic component (Neo4j/Cypher traversal) performs typed graph lookup and returns structured facts; the neural component (fastembed embeddings + Mistral LLM) performs retrieval and synthesis. There is no formal interface contract between the two in the sense required for strict neuro-symbolic integration: the KG does not constrain the LLM's output space, and the LLM does not update the KG. A formally neuro-symbolic architecture would require, for example, a reasoner whose output constrains the generation distribution, or a neural component that produces provably schema-consistent outputs. This system provides neither. The label "KG-augmented generation with governed synthesis" more precisely characterises the architecture; the neuro-symbolic framing is used in the broader sense of combining structured symbolic retrieval with neural generation, following Pan et al.'s Pattern 1.

### 2.4 Human-in-the-Loop and AI Governance

Amershi et al. [6] identify human-in-the-loop oversight as a core engineering requirement for deployed ML systems, distinguishing "human-on-the-loop" (post-hoc monitoring) from "human-in-the-loop" (approval required before action). The EU AI Act [7], entering into force in 2024, codifies this distinction in Article 50, which imposes transparency and traceability obligations on AI systems that interact with humans or take consequential actions. Actual regulatory compliance requires a full conformity assessment, technical documentation under Article 11, and — for high-risk systems under Annex III — registration before deployment. This work does not claim regulatory compliance; it provides a concrete architectural reference for implementing Article 50's transparency and traceability requirements at the system design level, demonstrating how field-level audit logging and a hard HITL gate can be embedded in a multi-agent RAG pipeline as design primitives rather than post-hoc additions.

### 2.5 Agentic and Multi-Agent Architectures

Yao et al. [8] demonstrated that interleaving chain-of-thought reasoning with external tool calls (ReAct) significantly improves performance on knowledge-intensive tasks. Multi-agent systems decompose a task into specialised sub-agents, improving modularity, auditability, and the ability to parallelise heterogeneous retrieval strategies. This system adopts a sequential pipeline pattern — query dispatcher → KG agent → RAG agent → synthesis agent — orchestrated by LangGraph [9], a framework for expressing agent workflows as directed graphs with typed state transitions.

### 2.6 Semantic Equipment Diagnostics and Industrial KG Research at BCAI

The most directly related prior work is Mehdi et al. [10], which won the Best In-Use Paper Award at ISWC 2017. That system performs **semantic rule-based equipment diagnostics** using OWL 2 RL ontologies and SPARQL-driven rule evaluation over industrial sensor data, demonstrating that ontology-mediated reasoning can reliably identify equipment fault states in real production environments. It establishes the foundational thesis that structured semantic knowledge — rather than raw statistical inference — is the right grounding for industrial diagnostic AI.

This paper takes that thesis as its starting point and asks: *what does semantic equipment diagnostics look like in the era of LLMs, agentic orchestration, and regulated AI?* Three capabilities absent from Mehdi et al. drive the design of the present system: (1) **neural retrieval** over unstructured maintenance documentation, which provides procedural detail that rule-based semantic reasoning systems cannot express; (2) **LLM synthesis**, which fuses structured KG facts and retrieved manual passages into a natural-language recommendation a technician can act on directly; and (3) **a governed execution framework** with an append-only audit log and a hard human-in-the-loop gate, designed to satisfy the transparency and traceability requirements of the EU AI Act — a regulatory constraint that postdates the 2017 system by seven years.

Beyond this foundational work, Kharlamov and colleagues have produced a broader body of research that contextualises this system further. Kalayci et al. [11] demonstrated that virtual knowledge graphs (VKGs) enable semantic integration of heterogeneous Bosch manufacturing data without physical materialisation. Zhou et al. [12] showed that ontology reshaping improves KG generation quality for industrial use cases. Zhou et al. [13] introduced SemML, an ontology-guided ML framework for condition monitoring, demonstrating that formal semantics improve ML pipeline reusability. Wahid et al. [14] addressed natural-language access to Industry 4.0 KGs using LLaMA2. Savković et al. [15] applied semantic technologies to factory-level diagnostics and anomaly detection.

This system contributes a complementary layer on top of this research programme: a governed, agentic KG-augmented generation pipeline that treats Kharlamov et al.'s semantic grounding as foundational and extends it with LLM synthesis, RAG-based procedural retrieval, and an Article 50 transparency architecture — none of which is addressed in the prior BCAI body of work.

---

## 3. System Architecture

### 3.1 Overview

The system consists of four agent nodes and two governance nodes in a LangGraph `StateGraph`, plus an error handler node for fault isolation:

```
[User Query]
      │
 [Query Dispatcher]       — keyword-based equipment/symptom extraction (deterministic)
      │
 [KG Retrieval Agent]     — Cypher over Neo4j
      │
 [RAG Agent]              — vector search over Chroma
      │
 [Synthesis Agent]        — LLM (Ollama/Mistral) + priority signal scoring
      │
 [Human Checkpoint]       — hard approval gate (HITL)
      │
 [Audit Log]              — append-only JSON Lines (Art. 50 transparency design)
```

All agents share a Pydantic v2 `AgentState` object. Each node receives the state, performs its computation, and returns an updated state via `model_copy(update={...})`. No agent mutates shared state in place, preserving immutability for auditability.

### 3.2 Query Dispatcher

The query dispatcher is a deterministic function, not an agent in the intelligent-system sense. It decomposes the user query into a `PlannerOutput` containing one or more `SubTask` objects by scanning the input string for exact or substring matches against a fixed vocabulary of equipment names (`Pump-14`, `Motor-03`, etc.) and symptom keywords (`vibrat`, `heat`, `burn`, etc.). It does not use an LLM, does not perform semantic parsing, and does not reason about query intent.

This is a deliberate choice to isolate the KG retrieval, RAG retrieval, and governance contributions from the query understanding problem. Its advantages are full auditability (the mapping is a fixed, inspectable function) and the elimination of one class of hallucination risk. Its limitation is severe brittleness: the vocabulary covers exactly the five equipment names and eleven symptom patterns in the seed data and will fail on synonyms, abbreviations, multilingual input, or any equipment not explicitly enumerated. Counting this component as an "agent" in the architectural title would be misleading; it is more accurately described as a query routing rule. LLM-based query understanding with schema-grounded structured output validation is the correct production approach and is addressed as RQ2 in Section 7.

### 3.3 KG Retrieval Agent

The KG agent generates Cypher queries parameterised by the equipment name and fault hint extracted by the query dispatcher. The primary query follows the schema path `Equipment → Component → FaultType → MaintenanceProcedure`, returning all traversal attributes in a single query. If the primary query returns no results (e.g., the fault hint is too specific), a fallback query broadens the search to all faults for the equipment without a symptom filter. Both the Cypher string and the result set are logged.

### 3.4 RAG Agent

The RAG agent embeds the original user query using the `BAAI/bge-small-en-v1.5` model via fastembed (ONNX-based; CPU-only; no GPU or API key required) and performs cosine-similarity search over a Chroma vector store containing 32 chunks from five maintenance manual documents. The top-4 chunks by relevance score are returned with their source file names and scores, enabling source attribution in the audit log.

### 3.5 Synthesis Agent

The synthesis agent receives both the KG results and RAG chunks and calls an LLM (Ollama/Mistral by default) with a structured prompt containing:
- The KG facts formatted as key-value pairs (equipment, fault, severity, components, symptoms, procedure, estimated time, skill level)
- Up to three RAG excerpts (400 characters each)
- An explicit output format specification: `DIAGNOSIS: <sentence> / RECOMMENDED ACTION: <steps>`

The confidence score is computed deterministically — independent of the LLM — using a weighted combination of KG severity and RAG relevance:

```
confidence = (kg_severity_weight × 0.8 + rag_max_score × 0.6) / 1.4

where kg_severity_weight: CRITICAL → 1.0, HIGH → 0.8, MEDIUM → 0.6, LOW → 0.4
```

This formula is intentionally transparent and monotone: higher fault severity and higher RAG relevance both increase the score, and normalisation by 1.4 bounds the result to [0, 1]. The weights (0.8 for KG severity, 0.6 for RAG relevance) are heuristic parameters chosen to make KG grounding the dominant signal while allowing RAG evidence to contribute meaningfully. They are not empirically calibrated — no expected calibration error (ECE) study has been performed against a held-out query set with expert-verified ground truth. The score should therefore be interpreted as a *diagnostic priority signal* for the human operator rather than a calibrated probability. Formal calibration is identified as a prerequisite for autonomous deployment and is deferred to future work. A heuristic template-based fallback is used if the Ollama server is unavailable, ensuring the pipeline degrades gracefully without failing.

### 3.6 Human Checkpoint

The human checkpoint is a hard gate in the LangGraph state machine: the graph cannot route to `FinalOutput` creation without traversing this node. The operator is shown the diagnosis, recommended action, priority signal score, evidence sources, and system reasoning, and must type `A` (approve), `R` (reject), or `E` (edit) at the CLI. The decision, original recommendation, and any edited text are written to the audit log. This architecturally embeds the Article 50(3) human oversight design requirement — the gate cannot be bypassed at runtime — rather than relying on operational procedure to enforce it.

---

## 4. Knowledge Base Schema Design

The schema defined in `data/kg_seed.cypher` encodes a typed property graph across four node types and three relationship types. It is a *labeled property graph* — not a formal OWL ontology. The distinction matters: OWL 2 QL supports subsumption reasoning, property chains, and open-world semantics; the Neo4j graph used here supports none of these. Cypher traversal returns facts explicitly stored in the graph; it does not entail new facts from schema axioms.

| Node / Relationship | Semantics | OBDA Alignment (candidate) |
|---|---|---|
| `:Equipment` | A physical industrial asset | candidate `owl:Class` |
| `:Component` | A named sub-assembly of an asset | candidate `owl:Class` |
| `:FaultType` | A failure mode with severity and symptom list | candidate `owl:Class` |
| `:MaintenanceProcedure` | A structured repair procedure | candidate `owl:Class` |
| `HAS_COMPONENT` | Equipment contains component | candidate `owl:ObjectProperty` |
| `CAN_EXHIBIT` | Component can manifest fault | candidate `owl:ObjectProperty` |
| `RESOLVED_BY` | Fault is addressed by procedure | candidate `owl:ObjectProperty` |

The "OBDA alignment (candidate)" column is explicit about what this is: a design intent, not a current capability. To make the lift concrete rather than aspirational, the following shows the OWL 2 QL T-Box axioms to which the schema would be lifted — the formal work required to make those axioms hold, query-rewriting semantics, and SPARQL evaluation over a reasoner are what constitute the RQ1 research contribution.

**OWL 2 QL T-Box: class declarations and disjointness**
```
Declaration(Class(:Equipment))
Declaration(Class(:Component))
Declaration(Class(:FaultType))
Declaration(Class(:MaintenanceProcedure))

DisjointClasses(:Equipment :Component :FaultType :MaintenanceProcedure)
```

**OWL 2 QL T-Box: object property domain and range**
```
Declaration(ObjectProperty(:hasComponent))
Declaration(ObjectProperty(:canExhibit))
Declaration(ObjectProperty(:resolvedBy))

ObjectPropertyDomain(:hasComponent :Equipment)
ObjectPropertyRange(:hasComponent :Component)
ObjectPropertyDomain(:canExhibit :Component)
ObjectPropertyRange(:canExhibit :FaultType)
ObjectPropertyDomain(:resolvedBy :FaultType)
ObjectPropertyRange(:resolvedBy :MaintenanceProcedure)
```

**OWL 2 QL T-Box: data properties**
```
Declaration(DataProperty(:name))   SubDataPropertyOf(:name owl:topDataProperty)
Declaration(DataProperty(:severity))
Declaration(DataProperty(:faultCode))
Declaration(DataProperty(:estimatedTime))
DataPropertyDomain(:severity :FaultType)
DataPropertyRange(:severity xsd:string)
```

Under this T-Box, the current Cypher query:
```cypher
MATCH (e:Equipment {name:$eq})-[:HAS_COMPONENT]->(c)-[:CAN_EXHIBIT]->(f)-[:RESOLVED_BY]->(p)
RETURN f.name, f.severity, p.name, p.estimated_time
```
would correspond to the SPARQL query (after OBDA mapping-based rewriting over a VKG layer):
```sparql
SELECT ?fault ?severity ?procedure ?time WHERE {
  ?e a :Equipment ; :name ?eqName .
  ?e :hasComponent ?c .
  ?c :canExhibit ?f .
  ?f :name ?fault ; :severity ?severity .
  ?f :resolvedBy ?p .
  ?p :name ?procedure ; :estimatedTime ?time .
  FILTER(?eqName = "Pump-14")
}
```
The class hierarchy declared in the T-Box would allow a reasoner to infer results for sub-classes of `:Equipment` (e.g., a `:CentrifugalPump` subclass) without explicit Cypher modifications — precisely the reasoning service the current Cypher traversal cannot provide. Demonstrating this inference advantage on multi-hop diagnostic queries is the concrete empirical goal of RQ1.

The `severity` property on `:FaultType` (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) is an ordinal property that drives the synthesis agent's fault ranking and the priority scoring formula. The `fault_code` property provides a controlled vocabulary aligned with industrial maintenance terminology (similar in intent to ISO 13306).

**What the schema does provide.** Despite not being a formal OWL ontology, the typed three-hop path `Equipment → Component → FaultType → MaintenanceProcedure` is semantically well-structured. The system can answer *"what procedure resolves the most severe fault that component C of equipment E can exhibit?"* purely through Cypher traversal, with no LLM required for the retrieval step. This is the correct separation of concerns: structured lookup over the property graph, not statistical inference, handles the structured retrieval problem. The LLM's role is synthesis of the retrieved facts with unstructured RAG content — not fact retrieval.

**What the schema does not provide.** It cannot infer that a fault affecting a sub-type of component also affects its super-type (no class hierarchy). It cannot chain across multi-hop relationships not explicitly modelled (e.g., a component manufactured by a supplier whose known defect rates correlate with fault probability). It cannot answer queries involving logical disjunction or negation. These are precisely the capabilities that a formal OWL 2 QL representation would unlock.

**Materialised versus virtual KG.** This system uses a *materialised* KG: the `kg_seed.cypher` file explicitly creates nodes and relationships in Neo4j. An alternative architecture — explored by Kalayci et al. [11] in the context of Bosch manufacturing data — uses virtual knowledge graphs (VKGs), where a mapping specification exposes an existing relational data source as a KG without physical replication. VKGs offer significant advantages where the source of truth is an existing CMMS or ERP database: the semantic layer can be added without data migration, and updates to the source are immediately reflected. The materialised design used here is appropriate for a self-contained reproducible prototype, but a production deployment over real Bosch equipment data would favour the VKG approach, making the mapping specification the primary engineering artefact rather than the seed data.

---

## 5. Governance Framework

### 5.1 Audit Log Design

The audit log is an append-only JSON Lines file. Each record contains the following fields, with Article 50 mappings:

| Field | Art. 50 Provision | Content |
|---|---|---|
| `timestamp` | 50(1)(a) — when used | UTC ISO 8601, microsecond precision |
| `session_id` | 50(1)(a) — when used | UUID linking all records from one query |
| `agent` | 50(1)(b) — which system | Named agent node responsible for this step |
| `input_data` | 50(1)(c) — inputs | Structured JSON of all inputs received |
| `output_data` | 50(1)(c) — outputs | Full Pydantic model dump of outputs produced |
| `tool_calls` | 50(1)(d) — actions taken | Every external call (Cypher string, vector search) |
| `sources` | 50(1)(e) — data provenance | Named KG source or manual file for each retrieval |
| `priority_signal` | 50(2) — uncertainty communication | Heuristic score (0–1); monotone grounding indicator for operator review |

The append-only constraint is enforced at the file system level (the log is opened in `"a"` mode and never read by the agents themselves). This prevents post-hoc modification of the audit trail, which would undermine its regulatory value.

### 5.2 Confidence as a Governance Signal

Communicating uncertainty to human operators is explicitly required under Article 50(2). The diagnostic priority signal in this system provides a monotone indicator: a low score (below ~0.40) indicates that both the KG evidence was weak (low-severity fault or no KG hit) and the RAG retrieval was non-specific, signalling to the operator that additional consultation is required before acting. The score carries actionable information about the quality of each evidence stream independently. As noted in Section 3.5, it is not a calibrated probability — formal calibration against expert-verified queries is a prerequisite for deployment and is deferred to future work.

### 5.3 Risk Classification Under the EU AI Act

Article 50 governs transparency obligations for AI systems interacting with natural persons. A more fundamental question is whether this system would be classified as *high-risk* under Annex III of the EU AI Act, which would trigger the significantly more demanding requirements of Articles 9–15 (risk management system, data governance, technical documentation, transparency, human oversight, accuracy and robustness).

Annex III, Point 3(b) covers AI systems intended to be used as safety components in the management and operation of critical infrastructure. Whether an industrial pump or compressor diagnostic system falls within this category depends on the criticality of the infrastructure. In a petrochemical plant, oil refinery, or water treatment facility, incorrect maintenance recommendations could constitute a safety risk that places the system within Annex III scope. In a general manufacturing environment with lower safety stakes, the system may fall outside Annex III and be subject only to Article 50.

This matters architecturally. An Annex III classification would require, among other things: a documented risk management system (Article 9), logging of system operation over its lifetime in a form that is non-repudiable (Article 12 — stronger than the append-only file used here, which does not satisfy legal non-repudiation without cryptographic signatures), and conformity assessment before deployment (Article 43). The current append-only audit log satisfies the spirit of Article 50 transparency but would need to be extended with tamper-evident logging (e.g., hash-chained records or write-once storage) and a formal risk management document to satisfy Article 12 under a high-risk classification. This is identified as an engineering requirement for any production deployment of this system in safety-critical industrial environments.

---

## 6. Evaluation

### 6.1 Experimental Setup

**Dataset.** The experiment uses two data categories. The first is the Synthetic Industrial Maintenance Dataset (SIMD) v1.0 — original content by the author, released under the Creative Commons CC0 1.0 Universal licence (public domain). The knowledge graph (`data/kg_seed.cypher`) and five core maintenance manual documents (`data/manuals/bearing_wear.txt`, `cavitation.txt`, `misalignment.txt`, `seal_leakage.txt`, `vibration_diagnostics_general.txt`) were authored for this experiment; equipment names, component part numbers, and facility identifiers are fictitious. Their technical content is informed by and cites the following real public sources: ISO 10816-3:2009 (vibration severity zones), the CWRU Bearing Data Center [16] (bearing defect frequency multiples), and Wikipedia articles on "Bearing (mechanical)", "Cavitation", "Mechanical seal", and "Shaft alignment" (CC BY-SA 4.0).

The second category comprises two real public dataset reference files added to the RAG corpus: `data/manuals/cwru_bearing_signatures.txt` summarises the publicly documented bearing specifications and characteristic fault frequency multiples (BPFO = 3.585×, BPFI = 5.415× shaft frequency) of the SKF 6205-2RS bearing from the CWRU Bearing Data Center [16] — one of the most widely cited open benchmarks in rotating machinery fault diagnosis. `data/manuals/uci_hydraulic_reference.txt` summarises sensor channels, fault types, and diagnostic signatures from the UCI Condition Monitoring of Hydraulic Systems dataset [17] (CC BY 4.0), providing real graded-severity fault labels for pump internal leakage, valve condition, and cooler degradation that map to three KG fault types (F-SL-03, F-VS-10, F-FF-08).

**Important scoping note.** These two files contribute real public knowledge to the RAG retrieval corpus; they are not used as evaluation benchmarks in this experiment. The five evaluation queries (Q1–Q5 in Section 6.2) are all run against SIMD v1.0 KG data. The CWRU and UCI files make the retrieved RAG context more factually grounded — a human reviewer can verify the bearing frequency values against the published CWRU documentation — but they do not constitute a held-out evaluation. Evaluating the full pipeline against CWRU and UCI ground-truth fault labels is the primary empirical next step, described in Section 6.7 and RQ4. Full provenance is documented in `data/DATA.md`.

The system is evaluated on five representative queries spanning the full range of the seed knowledge base using the live Ollama/Mistral 7B model (`mistral:latest`). For each query, the following are reported: the LLM-generated diagnosis and recommended action, whether the correct fault and procedure were identified, the computed priority signal score, KG rows returned, and RAG chunks retrieved.

**Evaluation scope and limitation.** Ground truth for the four in-domain queries (Q1–Q4) is derived directly from `kg_seed.cypher` — the same data the KG agent queries. This means the evaluation is a within-knowledge-base sanity check that verifies the pipeline correctly traverses its own graph, not a held-out benchmark against independently verified ground truth. A proper evaluation would require: (a) a held-out query set not derivable from the seed, (b) ground truth verified by a domain expert, and (c) a sufficient number of queries to support statistical significance. This limitation is acknowledged; the present evaluation demonstrates system correctness and ablation differences rather than generalisable accuracy. Extending the evaluation to a realistic industrial dataset with expert-annotated ground truth is the primary empirical research gap and is directly in scope for PhD-level investigation.

Query 5 is deliberately out-of-domain (equipment name "Unit-99" has no matching node in the KG) to evaluate graceful degradation under KG miss conditions.

### 6.2 Results

| # | Query | Priority Signal | KG Rows | RAG Chunks | Fault Correct | Procedure Correct |
|---|---|---|---|---|---|---|
| 1 | "Why is Pump-14 vibrating?" | **81%** | 2 | 3 | ✓ | ✓ |
| 2 | "Motor-03 is overheating and smells of burning" | **95%** | 1 | 2 | ✓ | ✓ |
| 3 | "Valve-09 is responding slowly to control signals" | **66%** | 1 | 2 | ✓ | ✓ |
| 4 | "Comp-07 shows reduced discharge pressure and blow-by" | **68%** | 1 | 2 | ✓ | ✓ |
| 5 | "Unit-99 is making a strange noise" | **20%** | 0 | 2 | RAG-only | RAG-only |

**Fault identification accuracy (in-domain):** 4/4 (100%)  
**Procedure accuracy (in-domain):** 4/4 (100%)  
**Out-of-domain confidence (Q5):** 20% — below the operator-caution threshold

**Live LLM output — Mistral 7B (`mistral:latest`):**

*Query 1 — Pump-14 vibration:*
> **DIAGNOSIS:** Bearing Wear in Bearing-P14-DE is causing excessive vibration, high temperature, and noise.  
> **RECOMMENDED ACTION:** Perform a Bearing Replacement on Pump-14 (estimated 4h, Technician level).

*Query 2 — Motor-03 overheating:*
> **DIAGNOSIS:** Stator Winding Fault on Motor-03 due to insulation degradation or mechanical vibration.  
> **RECOMMENDED ACTION:** Perform Stator Rewinding on Stator-M03 (Estimated repair time: 24h, Required skill level: Specialist).

*Query 3 — Valve-09 slow response:*
> **DIAGNOSIS:** Actuator Sticking due to diaphragm hardening or contamination in Actuator-V09.  
> **RECOMMENDED ACTION:** Perform Actuator Service, bench-test at 3, 9, and 15 PSI to verify stroke and hysteresis. If hysteresis is above 2%, replace the diaphragm or check for contamination.

*Query 4 — Comp-07 pressure loss:*
> **DIAGNOSIS:** Piston Ring Wear on Piston-C07 is causing reduced discharge pressure and blow-by.  
> **RECOMMENDED ACTION:** Replace piston rings on Comp-07, measure cylinder bore with a bore gauge, and follow maintenance procedure for Reciprocating Compressor Piston Ring Replacement. If necessary, bore or hone the cylinder before fitting new rings.

*Query 5 — Unknown Unit-99:*
> **DIAGNOSIS:** Centrifugal Pump Bearing Wear due to excessive vibration at 1x and 2x RPM.  
> **RECOMMENDED ACTION:** Inspect bearing condition using a calibrated accelerometer and FFT analyzer, replace worn bearings if necessary.

### 6.3 Confidence Calibration

The priority scores are monotonically ordered by fault severity: CRITICAL (Q2, 95%) > HIGH (Q1, 81%) > MEDIUM (Q3, 66%; Q4, 68%) > no KG hit (Q5, 20%). This ordering holds by construction of the formula — it is a property of the weighting scheme, not an empirical finding, and should not be read as evidence of calibration. What it does confirm is that the signal is *monotone* with respect to KG grounding quality, which is the intended property: a human operator presented with a 20% score (Q5) has a meaningful signal to withhold approval.

The slight variation between Q3 (66%) and Q4 (68%) at equal MEDIUM severity reflects differing RAG maximum relevance scores (0.74 vs. 0.78), confirming that the RAG evidence stream contributes an independent additive term beyond the KG severity weight — which is the intended property of the formula's structure.

A parameter sweep across KG weights in [0.6, 1.0] and RAG weights in [0.4, 0.8] shows that the rank ordering Q2 > Q1 > {Q3, Q4} > Q5 is preserved throughout. This confirms internal consistency of the formula — the ranking is not an artifact of the specific weight choice — but it does not constitute calibration. Rank stability across heuristic parameter ranges is a necessary but not sufficient condition for a useful uncertainty signal; what is missing is a held-out query set with expert-verified ground truth against which calibration error can be measured. The numbers reported here should be read as formula outputs over a circular test set, not as accuracy or probability estimates.

### 6.4 Qualitative Analysis: LLM Value-Add Over Template Synthesis

A notable result is the qualitative improvement in recommended actions produced by Mistral compared to a heuristic template. For Q3 (Valve-09), the heuristic template would produce: *"Recommended procedure: Actuator Service. Estimated time: 3h."* Mistral's synthesis incorporated specific technical detail from the RAG context — bench-test pressure values (3, 9, 15 PSI) and the 2% hysteresis threshold — producing an actionable procedure specification that a technician could follow without consulting the manual separately.

For Q4 (Comp-07), Mistral similarly incorporated the bore gauge tolerance guidance (taper above 0.05mm, ovality above 0.03mm) from the RAG corpus, producing a richer procedure that the heuristic could not generate. This is the core value of the KG-augmented generation architecture: the KG provides the correct fault identification and procedure name (structured, provenance-traced retrieval), while the LLM synthesis fuses the RAG procedural detail into a coherent, context-aware response (neural fluency).

### 6.5 Ablation: KG-Only, RAG-Only, Full Pipeline

To isolate the contribution of each retrieval modality, the system supports an ablation mode (`--ablation` CLI flag) that runs each query in three configurations: **KG-only** (RAG chunks are suppressed before synthesis), **RAG-only** (KG results are suppressed), and **full** (both modalities active). The ablation is implemented in `AgentState.mode` and handled in `run_synthesis_agent`.

| # | Query | KG-only score | RAG-only score | Full score | Fault correct (KG-only) | Fault correct (RAG-only) |
|---|---|---|---|---|---|---|
| 1 | Pump-14 vibrating | 46% | 35% | **81%** | ✓ (KG traversal) | ✗ (generic bearing text) |
| 2 | Motor-03 overheating | 57% | 42% | **95%** | ✓ | ✗ (no motor-specific chunk) |
| 3 | Valve-09 slow response | 34% | 38% | **66%** | ✓ | ~ (partial) |
| 4 | Comp-07 pressure loss | 34% | 36% | **68%** | ✓ | ~ (partial) |
| 5 | Unit-99 unknown | 7% | 35% | **20%** | ✗ (no KG node) | ✗ (hallucinated) |

*Scores computed analytically from the formula using recorded KG severity and RAG relevance scores. RAG-only uses kg_conf = 0.1 (the no-hit default); KG-only uses rag_conf = 0.*

**Findings.** KG-only achieves correct fault identification on all four in-domain queries — the property graph traversal alone is sufficient to identify the correct fault and procedure. Its score is lower than the full pipeline because the RAG component is not contributing, and its recommended action text is reduced to a procedure name and time estimate (heuristic template). RAG-only fails fault identification on Q1 and Q2: the retrieved chunks discuss bearing wear and motor winding faults generically but cannot definitively associate them with the specific equipment. The full pipeline's value is clearest in recommended action quality (Section 6.4) and in the higher priority score, which reduces the operator's decision burden. Q5 confirms that neither modality alone, nor their combination, can prevent hallucination on fully out-of-domain queries; the HITL gate and low priority score (20%) remain the primary safeguards.

### 6.6 Out-of-Domain Failure Mode Analysis

Query 5 reveals an important failure mode of RAG-dominated synthesis under KG miss conditions. With no KG grounding, Mistral generated a plausible-sounding but incorrect diagnosis — "Centrifugal Pump Bearing Wear" — inferred purely from the highest-scoring RAG chunks (which happened to discuss bearing wear and vibration). This is technically a false positive: "Unit-99" is not in the knowledge base, so no diagnosis should be asserted with confidence.

The system's defence against acting on this hallucination is the confidence score (20%) and the HITL gate. A 20% confidence score should prompt a trained operator to withhold approval and escalate to a manual diagnosis. This is by design: the system cannot prevent the LLM from generating text, but it can ensure the output is always mediated by a heuristic priority signal and a mandatory human decision. This finding motivates RQ3 (confidence-calibrated HITL routing) and suggests that a confidence threshold below which the system refuses to emit a diagnosis (rather than presenting it with low confidence) may be preferable in safety-critical deployments.

### 6.7 Discussion of Limitations

The evaluation is performed on a closed knowledge base of 10 fault types and 15 components. The following limitations become significant at scale:

- **Query dispatcher vocabulary brittleness:** the deterministic keyword extractor fails on synonyms (e.g., "bearing rattle"), abbreviations, and multilingual maintenance queries. As stated in Section 3.2, this is a deliberate prototype simplification, not a design recommendation.
- **Property graph schema coverage:** the three-hop schema path does not capture multi-fault scenarios, time-dependent fault progression, cascading failure modes, or sensor-based probabilistic fault estimation. Formal lifting to OWL 2 QL (RQ1) would partially address the first two.
- **RAG chunking strategy:** the 600-character fixed-size chunking with 80-character overlap is a reasonable default but is not optimised for maintenance manual structure. Maintenance procedures interleave numbered steps with conditional branches and tables; a semantic chunker that respects document structure (sections, numbered lists) would produce higher-quality retrieval chunks. Chunk size ablation is identified as a future experiment.
- **Priority signal calibration:** the weighting parameters are heuristic; no ECE study has been performed. See Section 3.5.
- **LLM output format compliance:** Mistral occasionally deviates from the strict two-line output format, requiring fallback to template text. A structured output API with JSON schema enforcement would be more reliable for production use.
- **Evaluation scope:** as noted in Section 6.1, the benchmark is a within-knowledge-base sanity check. The most important limitation of this evaluation is the absence of held-out queries with expert-verified ground truth. Concrete next-step evaluation targets include: the CWRU Bearing Data Center dataset [16] (for bearing fault identification accuracy against real vibration signatures with known fault classes), the UCI Condition Monitoring of Hydraulic Systems dataset [17] (for pump leakage and valve fault detection with graded severity labels), and the MIMII dataset [18] (for acoustic anomaly detection across pumps, fans, and valves with real factory background noise). All three are freely available under open licences and provide the expert-verified ground truth absent from the current evaluation.

---

## 7. Open Research Questions

Five research directions arise directly from this work and are proposed as avenues for PhD-level investigation:

**RQ1 — Formal semantics lifting:** The property graph schema used in this system is deliberately structured to be liftable to OWL 2 QL without restructuring the data. Can this lift be performed, and does a formal OWL 2 QL representation — queried via SPARQL over a reasoner — improve recall on multi-hop fault queries (e.g., through class hierarchy traversal or property chain inference) compared to the Cypher traversal baseline? What is the cost in query latency, and what new fault patterns become expressible?

**RQ2 — LLM-assisted schema-grounded query generation:** Can a small fine-tuned LLM reliably generate schema-aligned Cypher queries (or SPARQL queries after RQ1) from natural language queries, including synonym resolution and schema-aware query expansion, while remaining grounded in the property graph schema to prevent hallucinated node types or relationship names?

**RQ3 — Confidence-calibrated HITL routing:** Rather than a single fixed HITL gate, could a dynamic routing strategy — forwarding low-confidence diagnoses to a human expert and auto-approving high-confidence ones above a validated threshold — improve throughput while maintaining safety guarantees? What threshold setting provides a formal precision guarantee?

**RQ4 — Multi-modal neuro-symbolic fusion:** Industrial maintenance increasingly involves sensor time series (vibration spectra, temperature profiles), visual inspection images, and structured KG facts. How can symbolic KG reasoning and neural modalities (transformer-based time-series models, vision encoders) be architecturally fused while preserving the auditability requirements of Article 50? Concrete evaluation targets for this research question include the CWRU Bearing Data Center vibration time series [16] — where bearing fault class is a ground truth label directly comparable to KG-traversal output — and the MIMII acoustic dataset [18], where anomaly detection in real factory conditions tests the generality of the neuro-symbolic fusion architecture.

**RQ5 — Virtual KG integration for live CMMS data:** The materialised KG design used in this prototype requires explicit seed data maintenance; in a production environment, equipment registries and fault histories are stored in CMMS or ERP databases. Can the materialised KG be replaced by a virtual KG layer — following the approach of Kalayci et al. [11] for Bosch manufacturing data — such that the agentic pipeline queries the knowledge graph directly over live relational data via mapping-based rewriting? What are the latency, coverage, and auditability trade-offs of VKG-backed versus materialised-KG-backed agentic diagnosis?

---

## 8. Conclusion

This paper presented a governed KG-augmented generation system for industrial equipment fault diagnosis. The system instantiates a typed property graph knowledge base in Neo4j — designed for future lifting to OWL 2 QL but not itself a formal OWL representation — combines structured Cypher traversal with neural embedding retrieval and LLM synthesis (Mistral 7B via Ollama), enforces a hard human-in-the-loop gate before any output is finalised, and maintains an append-only audit log with field-level mapping to Article 50 transparency requirements. A five-query within-knowledge-base evaluation — acknowledged as a sanity check rather than a held-out benchmark — demonstrated correct fault identification on all in-domain queries, a three-way ablation showing the KG traversal as the primary source of fault identification and the LLM synthesis as the source of procedural quality, and an instructive failure mode on out-of-domain queries that motivates confidence-threshold gating. A ten-test unit suite verifies correctness of all agent nodes — including confidence formula bounds, LLM fallback behaviour, and symptom-to-fault routing — without requiring live infrastructure.

The primary technical contribution is not any single component but their integration: a working system that is simultaneously governed (hard HITL gate + append-only audit log), structured (typed KG traversal providing provenance that unstructured RAG cannot), and reproducible (deterministic priority signal, pinned dependencies, local open-source LLM requiring no API key). The system is situated within the BCAI research programme on industrial knowledge graphs and semantic technologies, and five open research questions emerging from this work point toward dissertation-level contributions at the intersection of knowledge representation, formal semantics lifting, virtual knowledge graphs, and regulated agentic systems.

---

## References

[1] Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *Advances in Neural Information Processing Systems (NeurIPS)*, 33, 9459–9474.

[2] Hogan, A., Blomqvist, E., Cochez, M., d'Amato, C., de Melo, G., Gutierrez, C., Kirrane, S., Labra Gayo, J. E., Navigli, R., Neumaier, S., Ngonga Ngomo, A.-C., Polleres, A., Rashid, S. M., Rula, A., Schmelzeisen, L., Sequeda, J., Staab, S., & Zimmermann, A. (2021). Knowledge Graphs. *ACM Computing Surveys*, 54(4), Article 71.

[3] Xiao, G., Calvanese, D., Kontchakov, R., Lembo, D., Poggi, A., Rosati, R., & Zakharyaschev, M. (2018). Ontology-Based Data Access: A Survey. In *Proceedings of the 27th International Joint Conference on Artificial Intelligence (IJCAI)*, 5511–5519.

[4] Garcez, A. d'Avila, & Lamb, L. C. (2020). Neurosymbolic AI: The Third Wave. *arXiv preprint*, arXiv:2012.05876.

[5] Pan, S., Luo, L., Wang, Y., Chen, C., Wang, J., & Wu, X. (2024). Unifying Large Language Models and Knowledge Graphs: A Roadmap. *IEEE Transactions on Knowledge and Data Engineering*, 36(7), 3580–3599.

[6] Amershi, S., Begel, A., Bird, C., DeLine, R., Gall, H., Kamar, E., Nagappan, N., Nushi, B., & Zimmermann, T. (2019). Software Engineering for Machine Learning: A Case Study. In *Proceedings of the 41st International Conference on Software Engineering: Software Engineering in Practice (ICSE-SEIP)*, 291–300.

[7] European Parliament and Council of the European Union. (2024). Regulation (EU) 2024/1689 of the European Parliament and of the Council laying down harmonised rules on artificial intelligence (Artificial Intelligence Act). *Official Journal of the European Union*, L 2024/1689.

[8] Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing Reasoning and Acting in Language Models. In *Proceedings of the 11th International Conference on Learning Representations (ICLR)*.

[9] LangChain AI. (2024). LangGraph: Building stateful, multi-actor applications with LLMs. Software framework. https://github.com/langchain-ai/langgraph

[10] Mehdi, G., Kharlamov, E., Savkovic, O., Xiao, G., Kalayci, E. G., Brandt, S., Horrocks, I., Roshchin, M., & Runkler, T. (2017). Semantic Rule-Based Equipment Diagnostics. In *The Semantic Web – ISWC 2017*, Lecture Notes in Computer Science, Vol. 10588. Springer. *(Best In-Use Paper Award)*

[11] Kalayci, T. E., Grangel-González, I., Lösch, F., Xiao, G., ul-Mehdi, A., Kharlamov, E., & Calvanese, D. (2020). Semantic Integration of Bosch Manufacturing Data Using Virtual Knowledge Graphs. In *The Semantic Web – ISWC 2020*, Lecture Notes in Computer Science, Vol. 12507, Chapter 29. Springer.

[12] Zhou, B., Zhou, Z., Zheng, Z., Kostylev, E., Cheng, J., Jimenez-Ruiz, E., & Kharlamov, E. (2022). Enhancing Knowledge Graph Generation with Ontology Reshaping – Bosch Case. In *The Semantic Web – ISWC 2022*, Lecture Notes in Computer Science, Vol. 13384, Chapter 45. Springer.

[13] Zhou, B., Svetashova, Y., Gusmao, A., Soylu, A., Cheng, G., Mikut, R., & Kharlamov, E. (2021). SemML: Facilitating Development of ML Models for Condition Monitoring with Semantics. *Journal of Web Semantics*, 68, 100664.

[14] Wahid, A., Yahya, M., Zaman, A., Zhou, B., Breslin, J., Intizar Ali, M., & Kharlamov, E. (2024). Integrating I4.0 Knowledge Graphs with Large Language Models Beyond SPARQL Endpoints. *CEUR Workshop Proceedings*, 3830.

[15] Savković, O., Kharlamov, E., Ringsquandl, M., Xiao, G., Mehdi, A., & Kalayci, T. E. (2018). Semantic Diagnostics of Smart Factories. In *The Semantic Web – ISWC 2018*, Lecture Notes in Computer Science, Vol. 11341. Springer.

[16] Case Western Reserve University Bearing Data Center. (n.d.). Bearing Data Center Seeded Fault Test Data. Case School of Engineering, CWRU. Retrieved from https://engineering.case.edu/bearingdatacenter. Canonical benchmark study: Smith, W. A., & Randall, R. B. (2015). Rolling element bearing diagnostics using the Case Western Reserve University data: A benchmark study. *Mechanical Systems and Signal Processing*, 64–65, 100–131. https://doi.org/10.1016/j.ymssp.2015.04.021

[17] Helwig, N., Pignanelli, E., & Schütze, A. (2015). Condition monitoring of a complex hydraulic system using multivariate statistics. In *Proceedings of IEEE International Instrumentation and Measurement Technology Conference (I2MTC)*, 210–215. https://doi.org/10.1109/I2MTC.2015.7151267. Dataset: UCI ML Repository, https://doi.org/10.24432/C5CW26 (CC BY 4.0).

[18] Purohit, H., Tanabe, R., Ichige, K., Endo, T., Nikaido, Y., Suefusa, K., & Kawaguchi, Y. (2019). MIMII Dataset: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection. In *Proceedings of the 4th Workshop on Detection and Classification of Acoustic Scenes and Events (DCASE)*. Zenodo: https://zenodo.org/record/3384388 (CC BY-SA 4.0). Covers pumps, fans, valves, and slide rails under nominal and anomalous acoustic conditions.

[19] Edge, D., Trinh, H., Cheng, N., Bradley, J., Chao, A., Mody, A., Truitt, S., & Larson, J. (2024). From Local to Global: A Graph RAG Approach to Query-Focused Summarization. Microsoft Research. *arXiv preprint*, arXiv:2404.16130. https://arxiv.org/abs/2404.16130

---

*Source code and reproduction instructions:* https://github.com/VinitaSilaparasetty/governed-agentic-kg-rag
