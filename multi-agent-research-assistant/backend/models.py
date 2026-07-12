"""Pydantic request/response schemas for the API."""
from typing import List, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    question: str
    doc_ids: Optional[List[str]] = None  # restrict retrieval to specific docs


class Citation(BaseModel):
    doc_id: str
    filename: str
    page: int
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    summary: str
    citations: List[Citation]
    agent_trace: List[str]


class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    num_pages: int
    num_chunks: int


class FlashcardItem(BaseModel):
    question: str
    answer: str
    source_page: Optional[str] = None


class FlashcardRequest(BaseModel):
    session_id: str
    doc_ids: Optional[List[str]] = None
    topic: Optional[str] = None
    num_cards: int = 10


class FlashcardResponse(BaseModel):
    flashcards: List[FlashcardItem]


class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str
    source_page: Optional[str] = None


class QuizRequest(BaseModel):
    session_id: str
    doc_ids: Optional[List[str]] = None
    topic: Optional[str] = None
    num_questions: int = 5
    difficulty: str = "medium"  # easy | medium | hard


class QuizResponse(BaseModel):
    questions: List[QuizQuestion]


class RoadmapRequest(BaseModel):
    session_id: str
    goal: str
    doc_ids: Optional[List[str]] = None
    weeks: int = 4


class RoadmapWeek(BaseModel):
    week: int
    title: str
    topics: List[str]
    tasks: List[str]
    resources: List[str]


class RoadmapResponse(BaseModel):
    goal: str
    weeks: List[RoadmapWeek]


class HistoryResponse(BaseModel):
    session_id: str
    messages: List[dict]
