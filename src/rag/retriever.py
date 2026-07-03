"""
Vector search over chunked maintenance manuals.
"""
from dataclasses import dataclass
from pathlib import Path

from langchain_chroma import Chroma

from .ingest import load_vector_store, CHROMA_DIR


@dataclass
class RetrievedChunk:
    content: str
    source_file: str
    score: float


class ManualRetriever:
    def __init__(self, chroma_dir: Path = CHROMA_DIR, top_k: int = 4):
        self._store: Chroma = load_vector_store(chroma_dir)
        self._top_k = top_k

    def search(self, query: str) -> list[RetrievedChunk]:
        results = self._store.similarity_search_with_relevance_scores(query, k=self._top_k)
        return [
            RetrievedChunk(
                content=doc.page_content,
                source_file=doc.metadata.get("source_file", "unknown"),
                score=round(float(score), 4),
            )
            for doc, score in results
        ]
