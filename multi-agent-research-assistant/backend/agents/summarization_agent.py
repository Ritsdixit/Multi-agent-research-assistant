"""
Summarization Agent: takes the Research Agent's raw findings and produces a
concise, well-structured final answer for the user.
"""
from backend.config import get_llm

SUMMARY_PROMPT = """You are a Summarization Agent. Turn the raw research findings below into a
clear, concise, well-structured final answer for a student.

Original question:
{question}

Raw research findings:
{research_output}

Instructions:
- Keep it concise but complete: use short paragraphs or bullet points.
- Preserve technical accuracy - do not add information not present in the findings.
- If the research findings say information wasn't found, communicate that honestly.
- End with a one-line TL;DR if the answer is more than a few sentences.
"""


def run_summarization_agent(question: str, research_output: str) -> str:
    llm = get_llm(temperature=0.3)
    prompt = SUMMARY_PROMPT.format(question=question, research_output=research_output)
    response = llm.invoke(prompt)
    return response.content
