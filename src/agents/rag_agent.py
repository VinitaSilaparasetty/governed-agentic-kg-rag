"""
RAG agent: embeds query and retrieves top-k relevant manual chunks.
"""
from .schemas import AgentState, RAGAgentOutput, RAGChunk
from ..rag.retriever import ManualRetriever
from ..governance.audit_log import log_step


def run_rag_agent(state: AgentState) -> AgentState:
    if not state.plan:
        return state.model_copy(update={"error": "RAG agent: no plan available"})

    rag_sub_tasks = [t for t in state.plan.sub_tasks if t.target in ("rag", "both")]
    if not rag_sub_tasks:
        return state

    query = rag_sub_tasks[0].question
    retriever = ManualRetriever(top_k=4)
    raw_chunks = retriever.search(query)

    chunks = [
        RAGChunk(content=c.content, source_file=c.source_file, score=c.score)
        for c in raw_chunks
    ]

    output = RAGAgentOutput(sub_task_question=query, chunks=chunks)

    log_step(
        agent="rag_agent",
        input_data={"query": query},
        output_data=output.model_dump(),
        tool_calls=["chroma.similarity_search_with_relevance_scores"],
        sources=[c.source_file for c in chunks],
        confidence=max((c.score for c in chunks), default=0.0),
        notes=f"{len(chunks)} chunks retrieved",
    )

    return state.model_copy(update={"rag_output": output})
