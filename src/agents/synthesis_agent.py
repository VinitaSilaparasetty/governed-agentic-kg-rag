"""
Synthesis agent: combines KG structured facts + RAG unstructured text into a
candidate diagnosis and recommended action with a confidence score.
"""
from .schemas import AgentState, SynthesisOutput
from ..governance.audit_log import log_step


def _severity_weight(severity: str | None) -> float:
    return {"CRITICAL": 1.0, "HIGH": 0.8, "MEDIUM": 0.6, "LOW": 0.4}.get(severity or "", 0.5)


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

    # ── Build diagnosis text ───────────────────────────────────────────────
    query = state.user_query
    equipment = state.plan.sub_tasks[0].equipment_name if state.plan else None

    if top_fault:
        components_str = ", ".join(top_fault["components"]) if top_fault["components"] else "unknown component"
        symptoms_str = "; ".join(top_fault["symptoms"])
        procedures_str = " / ".join(top_fault["procedures"]) or "No procedure recorded"
        diagnosis = (
            f"The most likely fault on {equipment or 'the equipment'} is "
            f"**{top_fault['fault']}** (severity: {top_fault['severity']}). "
            f"Affected component(s): {components_str}. "
            f"Typical symptoms: {symptoms_str}."
        )
        recommended_action = (
            f"Recommended procedure: {procedures_str}. "
            f"Estimated time: {top_fault['estimated_time'] or 'N/A'}. "
            f"Required skill: {top_fault['skill_level'] or 'N/A'}."
        )
    else:
        diagnosis = f"No structured fault data found in the knowledge graph for query: '{query}'."
        recommended_action = "Consult maintenance manual and perform visual inspection."

    # ── Augment with RAG context ───────────────────────────────────────────
    rag_context_snippets: list[str] = []
    for chunk in rag_chunks[:2]:
        first_line = chunk.content.split("\n")[0].strip()
        rag_context_snippets.append(f"[{chunk.source_file}] {first_line}")

    reasoning = (
        f"KG returned {len(kg_results)} fact rows across {len(fault_candidates)} unique fault types. "
        f"RAG retrieved {len(rag_chunks)} manual chunks. "
        + ("RAG context: " + " | ".join(rag_context_snippets) if rag_context_snippets else "No RAG context.")
    )

    # ── Confidence score ───────────────────────────────────────────────────
    kg_conf = _severity_weight(top_fault["severity"]) * 0.8 if top_fault else 0.1
    rag_conf = max((c.score for c in rag_chunks), default=0.0) * 0.6
    confidence = round(min((kg_conf + rag_conf) / 1.4, 1.0), 3)

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
        },
        output_data=output.model_dump(),
        tool_calls=[],
        sources=output.evidence_sources,
        confidence=confidence,
        notes=f"top_fault={top_fault['fault'] if top_fault else 'none'}",
    )

    return state.model_copy(update={"synthesis": output})
