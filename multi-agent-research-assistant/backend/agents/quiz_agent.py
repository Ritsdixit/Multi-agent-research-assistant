"""
Quiz Generator Agent: creates multiple-choice quiz questions grounded in the
uploaded documents, with exact page citations for each question.
"""
from backend.vectorstore.store import similarity_search
from backend.agents.research_agent import format_context
from backend.agents.json_utils import parse_json_response
from backend.config import get_llm

QUIZ_PROMPT = """You are a Quiz Generator Agent creating a {difficulty}-difficulty quiz for a student
studying the material below.

Topic focus: {topic}

Source excerpts (each tagged with filename + exact page number):
{context}

Generate exactly {num_questions} multiple-choice questions grounded ONLY in the excerpts above.

Return ONLY valid JSON (no markdown fences, no commentary) matching this schema:
[
  {{
    "question": "...",
    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct_answer": "A) ...",
    "explanation": "why this is correct, referencing the material",
    "source_page": "filename p.X"
  }}
]
"""


def run_quiz_agent(topic: str, num_questions: int, difficulty: str, doc_ids: list[str] | None = None) -> list[dict]:
    query = topic or "key concepts and important facts"
    chunks = similarity_search(query, k=max(10, num_questions * 2), doc_ids=doc_ids)
    if not chunks:
        return []

    context = format_context(chunks)
    llm = get_llm(temperature=0.4)
    prompt = QUIZ_PROMPT.format(
        difficulty=difficulty, topic=topic or "general", context=context, num_questions=num_questions
    )
    response = llm.invoke(prompt)
    try:
        questions = parse_json_response(response.content)
    except Exception:
        questions = []
    return questions
