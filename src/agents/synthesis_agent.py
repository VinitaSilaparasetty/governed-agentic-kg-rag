"""
Synthesis agent: combines KG structured facts + RAG unstructured text into a
candidate diagnosis and recommended action with a confidence score.

LLM synthesis uses Ollama (free, local, open-source) by default.
Set LLM_PROVIDER=ollama and LLM_MODEL=mistral:7b in .env, then:
  ollama pull mistral
"""
import os
from .schemas import AgentState, SynthesisOutput
from ..governance.audit_log import log_step


def _severity_weight(severity: str | None) -> float:
    return {"CRITICAL": 1.0, "HIGH": 0.8, "MEDIUM": 0.6, "LOW": 0.4}.get(severity or "", 0.5)


def _get_llm():
    """Return a LangChain chat model configured from environment variables."""
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    model = os.getenv("LLM_MODEL", "mistral:7b")
    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=0)
    raise ValueError(
        f"Unsupported LLM_PROVIDER={provider!r}. "
        "Supported: ollama. Install from https://ollama.com then: ollama pull mistral"
    )


def _run_llm_synthesis(
    query: str,
    equipment: str | None,
    top_fault: dict | None,
    rag_chunks: list,
) -> tuple[str, str]:
    """Call the LLM with KG facts + RAG excerpts; return (diagnosis, recommended_action)."""
    from langchain_core.messages import SystemMessage, HumanMessage

    if top_fault:
        components = ", ".join(top_fault["components"]) or "unknown component"
        symptoms = "; ".join(top_fault["symptoms"]) or "none recorded"
        procedures = " / ".join(top_fault["procedures"]) or "none recorded"
        kg_context = (
            f"Equipment: {equipment or 'unknown'}\n"
            f"Most likely fault: {top_fault['fault']} (severity: {top_fault['severity']})\n"
            f"Affected components: {components}\n"
            f"Observed symptoms: {symptoms}\n"
            f"Maintenance procedure: {procedures}\n"
            f"Estimated repair time: {top_fault['estimated_time'] or 'N/A'}\n"
            f"Required skill level: {top_fault['skill_level'] or 'N/A'}"
        )
    else:
        kg_context = "No knowledge-graph data available."

    rag_excerpts = (
        "\n\n".join(c.content[:400] for c in rag_chunks[:3])
        if rag_chunks else "No maintenance manual excerpts retrieved."
    )

    system = (
        "You are an industrial equipment fault-diagnosis expert. "
        "Given structured knowledge-graph facts and maintenance manual excerpts, "
        "write a concise technical diagnosis and a specific recommended action. "
        "Be direct and factual. No disclaimers. No markdown formatting. "
        "Always name the specific fault and the specific maintenance procedure."
    )
    user = (
        f"TECHNICIAN QUERY: {query}\n\n"
        f"--- KNOWLEDGE GRAPH FACTS ---\n{kg_context}\n\n"
        f"--- MAINTENANCE MANUAL EXCERPTS ---\n{rag_excerpts}\n\n"
        "Respond in EXACTLY this two-line format (no other text):\n"
        "DIAGNOSIS: <one sentence — specific fault, affected component, root cause>\n"
        "RECOMMENDED ACTION: <specific maintenance steps the technician should take>"
    )

    llm = _get_llm()
    response = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
    text = response.content.strip()

    # Defaults in case the model deviates from the expected format
    diagnosis = f"Fault detected on {equipment or 'equipment'}: {top_fault['fault'] if top_fault else 'unknown'}."
    recommended_action = "Consult the maintenance manual and perform a visual inspection."

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("DIAGNOSIS:"):
            diagnosis = stripped[len("DIAGNOSIS:"):].strip()
        elif stripped.startswith("RECOMMENDED ACTION:"):
            recommended_action = stripped[len("RECOMMENDED ACTION:"):].strip()

    return diagnosis, recommended_action


def _heuristic_synthesis(
    query: str,
    equipment: str | None,
    top_fault: dict | None,
) -> tuple[str, str]:
    """Template-based fallback used when Ollama is unavailable."""
    if top_fault:
        components_str = ", ".join(top_fault["components"]) if top_fault["components"] else "unknown component"
        symptoms_str = "; ".join(top_fault["symptoms"])
        procedures_str = " / ".join(top_fault["procedures"]) or "No procedure recorded"
        diagnosis = (
            f"The most likely fault on {equipment or 'the equipment'} is "
            f"{top_fault['fault']} (severity: {top_fault['severity']}). "
            f"Affected component(s): {components_str}. "
            f"Typical symptoms: {symptoms_str}."
        )
        recommended_action = (
            f"Recommended procedure: {procedures_str}. "
            f"Estimated time: {top_fault['estimated_time'] or 'N/A'}. "
            f"Required skill: {top_fault['skill_level'] or 'N/A'}."
        )
    else:
        diagnosis = f"No structured fault data found for query: '{query}'."
        recommended_action = "Consult maintenance manual and perform visual inspection."
    return diagnosis, recommended_action


def run_synthesis_agent(state: AgentState) -> AgentState:
    kg_out = state.kg_output
    rag_out = state.rag_output

    kg_results = kg_out.results if kg_out else []
    rag_chunks = rag_out.chunks if rag_out else []

    # ── Aggregate KG evidence ──────────────────────────────────────────────
    fault_candidates: dict[str, dict] = {}
    for r in kg_results:
        if not r.fault:
            continue
        if r.fault not in fault_candidates:
            fault_candidates[r.fault] = {
                "fault": r.fault,
                "severity": r.severity,
                "symptoms": set(r.symptoms),
                "components": set(),
                "procedures": [],
                "steps": r.steps,
                "estimated_time": r.estimated_time,
                "skill_level": r.skill_level,
            }
        else:
            fault_candidates[r.fault]["symptoms"].update(r.symptoms)
        if r.component:
            fault_candidates[r.fault]["components"].add(r.component)
        if r.procedure and r.procedure not in fault_candidates[r.fault]["procedures"]:
            fault_candidates[r.fault]["procedures"].append(r.procedure)

    # ── Pick top fault from KG ─────────────────────────────────────────────
    top_fault: dict | None = None
    if fault_candidates:
        top_fault = max(fault_candidates.values(), key=lambda x: _severity_weight(x["severity"]))

    query = state.user_query
    equipment = state.plan.sub_tasks[0].equipment_name if state.plan else None

    # ── LLM synthesis (Ollama/Mistral by default; heuristic fallback) ──────
    llm_used = True
    llm_error: str | None = None
    try:
        diagnosis, recommended_action = _run_llm_synthesis(query, equipment, top_fault, rag_chunks)
    except Exception as exc:
        llm_used = False
        llm_error = str(exc)
        diagnosis, recommended_action = _heuristic_synthesis(query, equipment, top_fault)

    # ── Confidence score (deterministic formula, independent of LLM) ───────
    kg_conf = _severity_weight(top_fault["severity"]) * 0.8 if top_fault else 0.1
    rag_conf = max((c.score for c in rag_chunks), default=0.0) * 0.6
    confidence = round(min((kg_conf + rag_conf) / 1.4, 1.0), 3)

    # ── Reasoning trace ────────────────────────────────────────────────────
    rag_context_snippets: list[str] = []
    for chunk in rag_chunks[:2]:
        first_line = chunk.content.split("\n")[0].strip()
        rag_context_snippets.append(f"[{chunk.source_file}] {first_line}")

    provider = os.getenv("LLM_PROVIDER", "ollama")
    model = os.getenv("LLM_MODEL", "mistral:7b")
    llm_label = (
        f"LLM={provider}/{model}" if llm_used
        else f"LLM=unavailable({llm_error}); heuristic fallback used"
    )
    reasoning = (
        f"{llm_label}. "
        f"KG returned {len(kg_results)} fact rows across {len(fault_candidates)} unique fault types. "
        f"RAG retrieved {len(rag_chunks)} manual chunks. "
        + ("RAG context: " + " | ".join(rag_context_snippets) if rag_context_snippets else "No RAG context.")
    )

    evidence_sources = (
        ["Neo4j KG"] * bool(kg_results)
        + [c.source_file for c in rag_chunks[:3]]
    )

    output = SynthesisOutput(
        diagnosis=diagnosis,
        recommended_action=recommended_action,
        confidence=confidence,
        evidence_sources=list(dict.fromkeys(evidence_sources)),
        reasoning=reasoning,
    )

    log_step(
        agent="synthesis_agent",
        input_data={
            "kg_fault_count": len(fault_candidates),
            "rag_chunk_count": len(rag_chunks),
            "llm_used": llm_used,
        },
        output_data=output.model_dump(),
        tool_calls=[f"llm.invoke({provider}/{model})"] if llm_used else [],
        sources=output.evidence_sources,
        confidence=confidence,
        notes=f"top_fault={top_fault['fault'] if top_fault else 'none'}; llm_used={llm_used}",
    )

    return state.model_copy(update={"synthesis": output})
