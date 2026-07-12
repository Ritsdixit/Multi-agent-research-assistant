"""
Study roadmap generation: builds a week-by-week study plan grounded in the
uploaded documents' content and the user's stated goal.
"""
from backend.vectorstore.store import similarity_search
from backend.agents.research_agent import format_context
from backend.agents.json_utils import parse_json_response
from backend.config import get_llm

ROADMAP_PROMPT = """You are a Study Roadmap Planner Agent.

Student's goal: {goal}
Time available: {weeks} weeks

Below is a sample of the material from the student's uploaded documents:
{context}

Design a week-by-week study roadmap that helps the student achieve their goal using this
material (plus your own knowledge to fill gaps and suggest general best practices).

Return ONLY valid JSON (no markdown fences, no commentary) matching this schema:
[
  {{
    "week": 1,
    "title": "short title for the week",
    "topics": ["topic 1", "topic 2"],
    "tasks": ["actionable task 1", "actionable task 2"],
    "resources": ["which uploaded doc/pages to review, or general resource suggestion"]
  }}
]
Produce exactly {weeks} entries, one per week.
"""


def generate_roadmap(goal: str, weeks: int, doc_ids: list[str] | None = None) -> list[dict]:
    chunks = similarity_search(goal, k=12, doc_ids=doc_ids)
    context = format_context(chunks) if chunks else "(No specific document content matched; use general best practices.)"

    llm = get_llm(temperature=0.4)
    prompt = ROADMAP_PROMPT.format(goal=goal, weeks=weeks, context=context)
    response = llm.invoke(prompt)
    try:
        plan = parse_json_response(response.content)
    except Exception:
        plan = []
    return plan
