"""
Flashcard generation: creates Q&A flashcards grounded in uploaded documents,
tagged with source page numbers for quick lookup.
"""
from backend.vectorstore.store import similarity_search
from backend.agents.research_agent import format_context
from backend.agents.json_utils import parse_json_response
from backend.config import get_llm

FLASHCARD_PROMPT = """You are a Flashcard Generator helping a student revise.

Topic focus: {topic}

Source excerpts (tagged with filename + exact page number):
{context}

Create exactly {num_cards} flashcards grounded ONLY in the excerpts above.
Each flashcard should test one clear concept, definition, formula, or fact.

Return ONLY valid JSON (no markdown fences, no commentary) matching this schema:
[
  {{"question": "...", "answer": "...", "source_page": "filename p.X"}}
]
"""


def generate_flashcards(topic: str, num_cards: int, doc_ids: list[str] | None = None) -> list[dict]:
    query = topic or "important definitions, concepts and facts"
    chunks = similarity_search(query, k=max(10, num_cards), doc_ids=doc_ids)
    if not chunks:
        return []

    context = format_context(chunks)
    llm = get_llm(temperature=0.4)
    prompt = FLASHCARD_PROMPT.format(topic=topic or "general", context=context, num_cards=num_cards)
    response = llm.invoke(prompt)
    try:
        cards = parse_json_response(response.content)
    except Exception:
        cards = []
    return cards
