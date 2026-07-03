"""
Chunk and embed maintenance manual text files into the vector store.

Default provider: fastembed (ONNX-based, no PyTorch/CUDA required).
Swap to OpenAI or Anthropic by setting EMBEDDING_PROVIDER in .env.
"""
import os
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma


MANUALS_DIR = Path(__file__).parents[2] / "data" / "manuals"
CHROMA_DIR = Path(__file__).parents[2] / ".chroma_db"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "fastembed")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")


def _get_embeddings():
    if EMBEDDING_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"))
    if EMBEDDING_PROVIDER == "anthropic":
        from langchain_anthropic import AnthropicEmbeddings
        return AnthropicEmbeddings(model=os.getenv("ANTHROPIC_EMBEDDING_MODEL", "voyage-3"))
    # Default: fastembed (ONNX runtime — no PyTorch, no GPU required)
    from langchain_community.embeddings import FastEmbedEmbeddings
    return FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)


def ingest_manuals(manuals_dir: Path = MANUALS_DIR, chroma_dir: Path = CHROMA_DIR) -> Chroma:
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
    docs = []
    for txt_file in sorted(manuals_dir.glob("*.txt")):
        loader = TextLoader(str(txt_file))
        raw = loader.load()
        chunks = splitter.split_documents(raw)
        for chunk in chunks:
            chunk.metadata["source_file"] = txt_file.name
        docs.extend(chunks)

    print(f"  Embedding {len(docs)} chunks with {EMBEDDING_PROVIDER}/{EMBEDDING_MODEL} ...")
    embeddings = _get_embeddings()
    store = Chroma.from_documents(docs, embeddings, persist_directory=str(chroma_dir))
    return store


def load_vector_store(chroma_dir: Path = CHROMA_DIR) -> Chroma:
    if not chroma_dir.exists():
        return ingest_manuals(chroma_dir=chroma_dir)
    embeddings = _get_embeddings()
    return Chroma(persist_directory=str(chroma_dir), embedding_function=embeddings)
