"""
PDF ingestion: extracts text page-by-page and splits into overlapping chunks
while preserving exact page-number metadata (needed for the Citation Agent).
"""
import uuid
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LCDocument

from backend.config import settings


def extract_pages(pdf_path: str) -> list[dict]:
    """Return a list of {page_number, text} dicts, 1-indexed pages."""
    pages = []
    with fitz.open(pdf_path) as doc:
        for i, page in enumerate(doc):
            text = page.get_text("text")
            pages.append({"page_number": i + 1, "text": text})
    return pages


def chunk_pdf(pdf_path: str, filename: str, doc_id: str | None = None) -> tuple[str, list[LCDocument]]:
    """
    Extract + chunk a PDF, tagging every chunk with its source page number(s).
    Returns (doc_id, list of LangChain Document chunks with metadata).
    """
    doc_id = doc_id or str(uuid.uuid4())[:8]
    pages = extract_pages(pdf_path)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[LCDocument] = []
    for page in pages:
        if not page["text"].strip():
            continue
        page_chunks = splitter.split_text(page["text"])
        for idx, chunk_text in enumerate(page_chunks):
            chunks.append(
                LCDocument(
                    page_content=chunk_text,
                    metadata={
                        "doc_id": doc_id,
                        "filename": filename,
                        "page": page["page_number"],
                        "chunk_index": idx,
                    },
                )
            )
    return doc_id, chunks, len(pages)
