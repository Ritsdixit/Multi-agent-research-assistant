"""
Basic smoke tests that don't require API keys - they test pure logic
(JSON parsing, citation dedup) rather than live LLM/embedding calls.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.json_utils import parse_json_response
from backend.agents.citation_agent import run_citation_agent
from langchain.schema import Document as LCDocument


def test_parse_json_plain():
    assert parse_json_response('[{"a": 1}]') == [{"a": 1}]


def test_parse_json_with_fences():
    text = '```json\n[{"a": 1}]\n```'
    assert parse_json_response(text) == [{"a": 1}]


def test_citation_dedup_and_sort():
    chunks = [
        LCDocument(page_content="text one", metadata={"doc_id": "d1", "filename": "b.pdf", "page": 3}),
        LCDocument(page_content="text two", metadata={"doc_id": "d1", "filename": "b.pdf", "page": 3}),
        LCDocument(page_content="text three", metadata={"doc_id": "d2", "filename": "a.pdf", "page": 1}),
    ]
    citations = run_citation_agent(chunks)
    assert len(citations) == 2
    assert citations[0]["filename"] == "a.pdf"
    assert citations[1]["page"] == 3


if __name__ == "__main__":
    test_parse_json_plain()
    test_parse_json_with_fences()
    test_citation_dedup_and_sort()
    print("All smoke tests passed.")
