"""
ChromaDB wrapper: a persistent vector store shared across all uploaded documents.
Each chunk carries doc_id / filename / page metadata for exact citations.
"""
from langchain_chroma import Chroma
from langchain_core.documents import Document as LCDocument

from backend.config import settings, get_embeddings

_vectorstore = None


def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name="research_assistant",
            embedding_function=get_embeddings(),
            persist_directory=settings.CHROMA_PERSIST_DIR,
        )
    return _vectorstore


def add_documents(chunks: list[LCDocument]) -> int:
    vs = get_vectorstore()
    ids = [f"{c.metadata['doc_id']}_{c.metadata['page']}_{c.metadata['chunk_index']}" for c in chunks]
    vs.add_documents(chunks, ids=ids)
    return len(chunks)


def similarity_search(query: str, k: int = None, doc_ids: list[str] | None = None) -> list[LCDocument]:
    vs = get_vectorstore()
    k = k or settings.RETRIEVAL_K
    filter_ = {"doc_id": {"$in": doc_ids}} if doc_ids else None
    return vs.similarity_search(query, k=k, filter=filter_)


def delete_document(doc_id: str):
    vs = get_vectorstore()
    vs.delete(where={"doc_id": doc_id})
