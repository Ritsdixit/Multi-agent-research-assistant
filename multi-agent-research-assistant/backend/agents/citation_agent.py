"""
Citation Agent: maps claims in the final answer back to exact source
documents and page numbers, using the metadata already attached to
retrieved chunks (no hallucinated page numbers - grounded in real metadata).
"""
from langchain_core.documents import Document as LCDocument


def run_citation_agent(retrieved_chunks: list[LCDocument]) -> list[dict]:
    """
    Deduplicate retrieved chunks into a clean citation list:
    [{doc_id, filename, page, snippet}]
    """
    seen = set()
    citations = []
    for chunk in retrieved_chunks:
        key = (chunk.metadata.get("doc_id"), chunk.metadata.get("page"))
        if key in seen:
            continue
        seen.add(key)
        snippet = chunk.page_content.strip().replace("\n", " ")
        snippet = (snippet[:180] + "...") if len(snippet) > 180 else snippet
        citations.append(
            {
                "doc_id": chunk.metadata.get("doc_id"),
                "filename": chunk.metadata.get("filename"),
                "page": chunk.metadata.get("page"),
                "snippet": snippet,
            }
        )
    # Sort by filename then page number for readability
    citations.sort(key=lambda c: (c["filename"] or "", c["page"] or 0))
    return citations
