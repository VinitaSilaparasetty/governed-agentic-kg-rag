# Governed KG-Integrated Multi-Agent RAG for Industrial Fault Diagnosis: A Neuro-Symbolic Approach with Transparent Human Oversight

**Vinita Silaparasetty**  
Aevoxis Solutions  
emtech1968@gmail.com

---

## Abstract

We present a governed multi-agent retrieval-augmented generation (RAG) system that integrates a structured knowledge graph (KG) with unstructured document retrieval to perform industrial equipment fault diagnosis. The system is orchestrated by a LangGraph state machine comprising four specialised agents — a deterministic planner, a KG retrieval agent (Neo4j/Cypher), a vector-similarity RAG agent (Chroma/fastembed), and an LLM synthesis agent (Ollama/Mistral) — together with a hard human-in-the-loop gate before any output is finalised. The KG schema (Equipment → Component → FaultType → MaintenanceProcedure) constitutes a lightweight domain ontology whose node labels and relationship types correspond directly to OWL classes and object properties, enabling symbolic reasoning via Cypher alongside neural retrieval over maintenance manual embeddings. Every agent step is written to an append-only structured audit log with field-level mapping to EU AI Act Article 50 transparency requirements. A five-query benchmark over the seed knowledge base demonstrates fault identification accuracy of 100% on in-domain queries and graceful degradation (low-confidence fallback) on out-of-domain queries, with a deterministic confidence scoring formula enabling calibrated uncertainty communication to the human operator. We discuss the system as a concrete instantiation of the neuro-symbolic integration paradigm and identify four open research questions arising from its design.

---

## 1. Introduction

Large language models have demonstrated impressive capability on open-domain question answering, but they remain unreliable for high-stakes industrial diagnostic tasks. Hallucination, inconsistent reasoning over structured data, and the absence of traceability make raw LLM outputs inappropriate for environments where an incorrect maintenance recommendation can cause equipment damage, unplanned downtime, or — in safety-critical facilities — personal injury.

Two complementary research traditions address these weaknesses. Knowledge graphs (KGs) provide structured, interpretable, and verifiable representations of domain facts: an equipment-to-component-to-fault ontology can definitively answer "which component of Pump-14 is most likely to cause vibration?" without recourse to probabilistic sampling. Retrieval-augmented generation (RAG) systems augment LLM generation with retrieved passages from a corpus, improving factual grounding for questions requiring procedural or contextual detail not captured in structured data.

The key insight driving this system is that these two modalities answer *different types of questions* about the same domain. A KG answers: *what* component, *which* fault, *what* severity, *what* procedure — all with full provenance. A RAG system answers: *how* to carry out the procedure — the safety prerequisites, diagnostic decision trees, and post-maintenance monitoring schedules contained in unstructured technical manuals. Neither alone is sufficient; both together, grounded by explicit governance, constitute a sound basis for a diagnostic recommendation.

This paper makes the following contributions:

1. A working multi-agent neuro-symbolic architecture combining KG symbolic reasoning with neural embeddings and LLM synthesis, orchestrated by a LangGraph state machine with conditional edges.
2. A domain ontology for industrial equipment maintenance encoded as a Neo4j property graph, with node types and relationship semantics drawn from ontology-based data access (OBDA) principles.
3. A governance layer implementing EU AI Act Article 50 requirements via an append-only structured audit log and a hard human-in-the-loop checkpoint in the agent graph.
4. A five-query empirical evaluation demonstrating fault identification accuracy, confidence calibration, and graceful degradation on out-of-domain inputs.

---

## 2. Background and Related Work

### 2.1 Retrieval-Augmented Generation

Lewis et al. [1] introduced retrieval-augmented generation as a method for conditioning language model generation on non-parametric memory — a retrieval corpus — to improve factual accuracy on knowledge-intensive tasks. Standard RAG retrieves top-*k* document chunks by embedding similarity and passes them as context to the generator. A known limitation is the inability to perform structured relational reasoning: RAG cannot answer "which specific component of a specific machine is most likely responsible for this fault" without a schema that makes those relationships explicit.

### 2.2 Knowledge Graphs and Ontology-Based Data Access

Hogan et al. [2] survey the knowledge graph paradigm, defining a KG as a graph-based data structure where nodes represent entities and edges represent typed relationships. In industrial settings, KGs have been applied to equipment monitoring, maintenance planning, and semantic data integration. The ontology-based data access (OBDA) paradigm [3] uses OWL ontologies as virtual mediation layers over heterogeneous data sources, enabling SPARQL queries to return results logically entailed by the ontology even when the data is stored in relational or graph form. The schema used in this system — `(:Equipment)-[:HAS_COMPONENT]->(:Component)-[:CAN_EXHIBIT]->(:FaultType)-[:RESOLVED_BY]->(:MaintenanceProcedure)` — mirrors the OBDA ontology pattern: node labels correspond to OWL classes (`owl:Class`), relationship types to OWL object properties (`owl:ObjectProperty`), and node properties to OWL datatype properties (`owl:DatatypeProperty`).

### 2.3 Neuro-Symbolic Integration

The neuro-symbolic AI paradigm [4] seeks to combine the interpretability and formal reasoning capabilities of symbolic AI with the flexibility and pattern recognition of neural systems. Pan et al. [5] survey the roadmap for unifying LLMs with KGs, identifying three integration patterns: KG-enhanced LLM (the KG provides context to improve generation), LLM-enhanced KG (the LLM assists in KG construction or query generation), and synergistic integration (bidirectional interaction). This system realises the first pattern at the retrieval layer and explores a hybrid second pattern in the planner, which uses deterministic keyword extraction to generate structured KG sub-tasks — a design decision discussed further in Section 4.2.

### 2.4 Human-in-the-Loop and AI Governance

Amershi et al. [6] identify human-in-the-loop oversight as a core engineering requirement for deployed ML systems, distinguishing "human-on-the-loop" (post-hoc monitoring) from "human-in-the-loop" (approval required before action). The EU AI Act [7], entering into force in 2024, codifies this distinction in Article 50, which imposes transparency and traceability obligations on AI systems that interact with humans or take consequential actions. To our knowledge, no published system-level implementation of Article 50 compliance in the multi-agent RAG setting exists in the literature; this work provides a concrete reference implementation.

### 2.5 Agentic and Multi-Agent Architectures

Yao et al. [8] demonstrated that interleaving chain-of-thought reasoning with external tool calls (ReAct) significantly improves performance on knowledge-intensive tasks. Multi-agent systems decompose a task into specialised sub-agents, improving modularity, auditability, and the ability to parallelise heterogeneous retrieval strategies. This system adopts a sequential pipeline pattern — planner → KG agent → RAG agent → synthesis agent — orchestrated by LangGraph [9], a framework for expressing agent workflows as directed graphs with typed state transitions.

---

## 3. System Architecture

### 3.1 Overview

The system consists of four agent nodes and two governance nodes in a LangGraph `StateGraph`, plus an error handler node for fault isolation:

```
[User Query]
      │
 [Planner Agent]          — deterministic query decomposition
      │
 [KG Retrieval Agent]     — Cypher over Neo4j
      │
 [RAG Agent]              — vector search over Chroma
      │
 [Synthesis Agent]        — LLM (Ollama/Mistral) + confidence scoring
      │
 [Human Checkpoint]       — hard approval gate (HITL)
      │
 [Audit Log]              — append-only JSON Lines (Art. 50)
```

All agents share a Pydantic v2 `AgentState` object. Each node receives the state, performs its computation, and returns an updated state via `model_copy(update={...})`. No agent mutates shared state in place, preserving immutability for auditability.

### 3.2 Planner Agent

The planner decomposes the user query into a `PlannerOutput` containing one or more `SubTask` objects. Each sub-task specifies a target (`kg`, `rag`, or `both`), an extracted equipment name (if present), and a fault hint (if a symptom keyword is detected). The planner uses a deterministic keyword matching strategy over a curated vocabulary of equipment names and symptom terms rather than an LLM call. This is a governance choice: deterministic decomposition is fully auditable (the mapping from query to sub-tasks is a fixed, inspectable function) and eliminates one class of hallucination risk. The trade-off — reduced generalisation to synonym-rich or ambiguous queries — is identified as a future research direction in Section 7.

### 3.3 KG Retrieval Agent

The KG agent generates Cypher queries parameterised by the equipment name and fault hint extracted by the planner. The primary query follows the ontology path `Equipment → Component → FaultType → MaintenanceProcedure`, returning all traversal attributes in a single query. If the primary query returns no results (e.g., the fault hint is too specific), a fallback query broadens the search to all faults for the equipment without a symptom filter. Both the Cypher string and the result set are logged.

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

This formula is intentionally transparent and monotone: higher fault severity and higher RAG retrieval confidence both increase the output confidence, and the normalisation by 1.4 bounds the result to [0, 1]. A heuristic template-based fallback is used if the Ollama server is unavailable, ensuring the pipeline degrades gracefully without failing.

### 3.6 Human Checkpoint

The human checkpoint is a hard gate in the LangGraph state machine: the graph cannot route to `FinalOutput` creation without traversing this node. The operator is shown the diagnosis, recommended action, confidence score, evidence sources, and system reasoning, and must type `A` (approve), `R` (reject), or `E` (edit) at the CLI. The decision, original recommendation, and any edited text are written to the audit log. This implements the Article 50(3) human oversight requirement at the architectural level, not as a post-hoc addition.

---

## 4. Knowledge Graph as Domain Ontology

The schema defined in `data/kg_seed.cypher` encodes a lightweight maintenance ontology across four concept types and three relationship types:

| Neo4j Element | OWL Analogue | Semantics |
|---|---|---|
| `:Equipment` | `owl:Class` | A physical industrial asset |
| `:Component` | `owl:Class` | A named sub-assembly of an asset |
| `:FaultType` | `owl:Class` | A failure mode with severity classification and symptom list |
| `:MaintenanceProcedure` | `owl:Class` | A structured repair procedure with steps, time, and skill level |
| `HAS_COMPONENT` | `owl:ObjectProperty` | Composition: equipment contains component |
| `CAN_EXHIBIT` | `owl:ObjectProperty` | Fault risk: component can manifest fault |
| `RESOLVED_BY` | `owl:ObjectProperty` | Resolution: fault is addressed by procedure |

The `severity` property on `:FaultType` (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) constitutes an ordinal datatype property that drives both the synthesis agent's fault ranking and the confidence scoring formula. The `fault_code` property provides a controlled vocabulary aligned with industrial maintenance standards (similar in intent to ISO 13306 maintenance terminology).

This ontological structuring distinguishes the system from a flat-schema property graph. The three-hop path `Equipment → Component → FaultType → MaintenanceProcedure` is a tractable, semantically well-typed inference chain: the system can answer "what procedure resolves the most severe fault that component C of equipment E can exhibit?" purely through graph traversal, with no LLM required for the retrieval step. This mirrors the OBDA paradigm in which ontology-mediated query rewriting provides logically grounded answers over heterogeneous data.

A natural extension — identified as a research direction in Section 7 — would lift this schema to a formal OWL 2 QL ontology, enabling SPARQL-based inference and alignment with industrial ontology standards such as ISO 15926 (oil and gas), IEC 61360 (component data elements), or the Bosch-specific ontologies developed within the BCAI group.

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
| `confidence` | 50(2) — AI confidence | Numeric score (0–1) for meaningful human review |

The append-only constraint is enforced at the file system level (the log is opened in `"a"` mode and never read by the agents themselves). This prevents post-hoc modification of the audit trail, which would undermine its regulatory value.

### 5.2 Confidence as a Governance Signal

Communicating uncertainty to human operators is explicitly required under Article 50(2). The confidence formula in this system provides a calibrated signal: a low score (below ~0.40) indicates that both the KG evidence was weak (low-severity fault or no KG hit) and the RAG retrieval was non-specific, signalling to the operator that additional consultation is required before acting. This is not "confidence theatre" — the score carries actionable information about the quality of each evidence stream independently.

---

## 6. Evaluation

### 6.1 Experimental Setup

We evaluate the system on five representative queries spanning the full range of the seed knowledge base using the live Ollama/Mistral 7B model (`mistral:latest`). For each query we report: the LLM-generated diagnosis and recommended action, whether the correct fault and procedure were identified, the computed confidence score, KG rows returned, and RAG chunks retrieved. Ground truth is derived directly from `kg_seed.cypher`.

Query 5 is deliberately out-of-domain (equipment name "Unit-99" has no matching node in the KG) to evaluate graceful degradation under KG miss conditions.

### 6.2 Results

| # | Query | Confidence | KG Rows | RAG Chunks | Fault Correct | Procedure Correct |
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

The confidence scores are monotonically ordered by fault severity: CRITICAL (Q2, 95%) > HIGH (Q1, 81%) > MEDIUM (Q3, 66%; Q4, 68%) > no KG hit (Q5, 20%). This ordering holds by construction of the formula, confirming the signal is well-calibrated with respect to the quality of KG grounding.

The slight variation between Q3 (66%) and Q4 (68%) at equal MEDIUM severity reflects differing RAG maximum relevance scores (0.74 vs. 0.78), demonstrating that the RAG evidence stream contributes independent information to the confidence estimate beyond the KG severity weight alone.

### 6.4 Qualitative Analysis: LLM Value-Add Over Template Synthesis

A notable result is the qualitative improvement in recommended actions produced by Mistral compared to a heuristic template. For Q3 (Valve-09), the heuristic template would produce: *"Recommended procedure: Actuator Service. Estimated time: 3h."* Mistral's synthesis incorporated specific technical detail from the RAG context — bench-test pressure values (3, 9, 15 PSI) and the 2% hysteresis threshold — producing an actionable procedure specification that a technician could follow without consulting the manual separately.

For Q4 (Comp-07), Mistral similarly incorporated the bore gauge tolerance guidance (taper above 0.05mm, ovality above 0.03mm) from the RAG corpus, producing a richer procedure that the heuristic could not generate. This is the core value of the neuro-symbolic architecture: the KG provides the correct fault identification and procedure name (symbolic precision), while the LLM synthesis fuses the RAG procedural detail into a coherent, context-aware response (neural fluency).

### 6.5 Out-of-Domain Failure Mode Analysis

Query 5 reveals an important failure mode of RAG-dominated synthesis under KG miss conditions. With no KG grounding, Mistral generated a plausible-sounding but incorrect diagnosis — "Centrifugal Pump Bearing Wear" — inferred purely from the highest-scoring RAG chunks (which happened to discuss bearing wear and vibration). This is technically a false positive: "Unit-99" is not in the knowledge base, so no diagnosis should be asserted with confidence.

The system's defence against acting on this hallucination is the confidence score (20%) and the HITL gate. A 20% confidence score should prompt a trained operator to withhold approval and escalate to a manual diagnosis. This is by design: the system cannot prevent the LLM from generating text, but it can ensure the output is always mediated by a calibrated confidence signal and a human decision. This finding motivates RQ3 (confidence-calibrated HITL routing) and suggests that a confidence threshold below which the system refuses to emit a diagnosis (rather than presenting it with low confidence) may be preferable in safety-critical deployments.

### 6.6 Discussion of Limitations

The evaluation is performed on a closed knowledge base of 10 fault types and 15 components. The following limitations become significant at scale:

- **Planner vocabulary brittleness:** the deterministic keyword extractor fails on synonyms (e.g., "bearing rattle"), abbreviations, and multilingual maintenance queries.
- **KG schema coverage:** the three-hop ontology path does not capture multi-fault scenarios, time-dependent fault progression, or sensor-based probabilistic fault estimation.
- **RAG chunk quality:** the 600-character chunking strategy is not optimised for structured maintenance procedures, which often interleave numbered steps with conditional branches.
- **LLM output format compliance:** Mistral occasionally deviates from the strict two-line output format, requiring fallback to template text. A structured output API with JSON schema enforcement would be more reliable for production use.

---

## 7. Open Research Questions

Four research directions arise directly from this work and are proposed as avenues for PhD-level investigation:

**RQ1 — Ontology-mediated KG expansion:** Can a formal OWL 2 QL ontology over the maintenance schema enable logical inference (e.g., transitivity of `CAN_EXHIBIT` across component hierarchies) that improves recall on multi-hop fault queries? What is the cost in query latency compared to native Cypher traversal?

**RQ2 — LLM-assisted Cypher generation with OBDA grounding:** Can a small fine-tuned LLM reliably generate ontology-aligned Cypher queries from natural language queries, including synonym resolution and schema-aware query expansion, while remaining grounded in the ontology schema to prevent hallucinated node types?

**RQ3 — Confidence-calibrated HITL routing:** Rather than a single fixed HITL gate, could a dynamic routing strategy — forwarding low-confidence diagnoses to a human expert and auto-approving high-confidence ones above a validated threshold — improve throughput while maintaining safety guarantees? What threshold setting provides a formal precision guarantee?

**RQ4 — Multi-modal neuro-symbolic fusion:** Industrial maintenance increasingly involves sensor time series (vibration spectra, temperature profiles), visual inspection images, and structured KG facts. How can symbolic KG reasoning and neural modalities (transformer-based time-series models, vision encoders) be architecturally fused while preserving the auditability requirements of Article 50?

---

## 8. Conclusion

This paper presented a governed multi-agent neuro-symbolic RAG system for industrial equipment fault diagnosis. The system instantiates a lightweight domain ontology in Neo4j, combines symbolic KG traversal with neural embedding retrieval and LLM synthesis (Mistral 7B via Ollama), enforces a hard human-in-the-loop gate before any output is finalised, and maintains an append-only audit log with field-level Article 50 compliance. A five-query evaluation against the live Mistral model demonstrated 100% fault identification accuracy on in-domain queries, measurable LLM value-add over template synthesis on procedural detail, and an instructive failure mode on out-of-domain queries that motivates confidence-threshold gating.

The primary technical contribution is not any single component but their integration: a working system that is simultaneously neuro-symbolic (KG + embeddings + LLM), governed (HITL + audit log), and reproducible (deterministic confidence formula, Docker-seeded KG, pinned dependencies, local open-source LLM). Four open research questions emerging from this work point toward dissertation-level contributions at the intersection of knowledge representation, neuro-symbolic AI, and regulated agentic systems.

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

---

*Source code and reproduction instructions:* https://github.com/VinitaSilaparasetty/governed-agentic-kg-rag
