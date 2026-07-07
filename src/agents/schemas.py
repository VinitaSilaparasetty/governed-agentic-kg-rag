"""
Pydantic schemas for agent inputs, outputs, and shared graph state.
"""
from typing import Literal
from pydantic import BaseModel, Field


class PlannerInput(BaseModel):
    user_query: str


class SubTask(BaseModel):
    target: Literal["kg", "rag", "both"]
    question: str
    equipment_name: str | None = None
    fault_hint: str | None = None


class PlannerOutput(BaseModel):
    original_query: str
    sub_tasks: list[SubTask]


class KGResult(BaseModel):
    equipment: str | None = None
    component: str | None = None
    fault: str | None = None
    symptoms: list[str] = Field(default_factory=list)
    severity: str | None = None
    procedure: str | None = None
    steps: list[str] = Field(default_factory=list)
    estimated_time: str | None = None
    skill_level: str | None = None
    cypher_used: str = ""
    rows_returned: int = 0


class KGAgentOutput(BaseModel):
    sub_task_question: str
    results: list[KGResult]
    fallback_used: bool = False


class RAGChunk(BaseModel):
    content: str
    source_file: str
    score: float


class RAGAgentOutput(BaseModel):
    sub_task_question: str
    chunks: list[RAGChunk]


class SynthesisOutput(BaseModel):
    diagnosis: str
    recommended_action: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_sources: list[str]
    reasoning: str


class FinalOutput(BaseModel):
    user_query: str
    diagnosis: str
    recommended_action: str
    confidence: float
    evidence_sources: list[str]
    reasoning: str
    human_approved: bool
    human_edit: str | None = None


# ── LangGraph shared state ─────────────────────────────────────────────────
class AgentState(BaseModel):
    user_query: str = ""
    plan: PlannerOutput | None = None
    kg_output: KGAgentOutput | None = None
    rag_output: RAGAgentOutput | None = None
    synthesis: SynthesisOutput | None = None
    final: FinalOutput | None = None
    error: str | None = None
    # Ablation mode: "full" | "kg_only" | "rag_only"
    # kg_only suppresses RAG chunks in synthesis; rag_only suppresses KG results.
    mode: Literal["full", "kg_only", "rag_only"] = "full"
