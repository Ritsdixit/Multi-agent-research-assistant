"""
Research Agent: retrieves relevant chunks from the vector store and
synthesizes a grounded research answer to the user's question.
"""
from langchain_core.documents import Document as LCDocument
from backend.vectorstore.store import similarity_search
from backend.config import get_llm

RESEARCH_PROMPT = """You are a meticulous Research Agent helping a student analyze uploaded papers/notes.

Conversation history (for context only):
{history}

User question:
{question}

Below are retrieved excerpts from the user's documents. Each excerpt is tagged with its
source filename and exact page number.

{context}

Instructions:
- Answer using ONLY information grounded in the excerpts above. If the excerpts don't
  contain the answer, say so clearly instead of guessing.
- Be precise and technical where appropriate.
- Do not fabricate page numbers or facts not present in the excerpts.
- Write a clear, well-organized research finding (not a final polished answer yet -
  that will be refined by another agent).
"""


def format_context(chunks: list[LCDocument]) -> str:
    blocks = []
    for c in chunks:
        blocks.append(
            f"[Source: {c.metadata.get('filename')} | Page {c.metadata.get('page')}]\n{c.page_content}"
        )
    return "\n\n---\n\n".join(blocks)


def run_research_agent(question: str, history: str, doc_ids: list[str] | None = None) -> dict:
    chunks = similarity_search(question, doc_ids=doc_ids)
    if not chunks:
        return {
            "research_output": "No relevant content was found in the uploaded documents for this question.",
            "retrieved_chunks": [],
        }

    context = format_context(chunks)
    llm = get_llm(temperature=0.2)
    prompt = RESEARCH_PROMPT.format(history=history or "(none)", question=question, context=context)
    response = llm.invoke(prompt)

    return {
        "research_output": response.content,
        "retrieved_chunks": chunks,
    }
