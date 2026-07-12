"""
FastAPI backend for the Multi-Agent Research Assistant.

Endpoints:
  POST /upload            - upload & ingest a PDF
  GET  /documents         - list uploaded documents
  DELETE /documents/{id}  - delete a document
  POST /chat              - ask a question (runs the multi-agent pipeline)
  GET  /history/{session} - fetch chat history
  POST /flashcards        - generate flashcards
  POST /quiz               - generate a quiz
  POST /roadmap             - generate a study roadmap
  POST /voice/transcribe   - speech-to-text
  POST /voice/speak         - text-to-speech, returns audio file
"""
import os
import shutil
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import init_db, get_db, Document, Flashcard, RoadmapEntry
from backend.models import (
    ChatRequest, ChatResponse, Citation, UploadResponse,
    FlashcardRequest, FlashcardResponse, FlashcardItem,
    QuizRequest, QuizResponse, QuizQuestion,
    RoadmapRequest, RoadmapResponse, RoadmapWeek,
    HistoryResponse,
)
from backend.ingestion.pdf_processor import chunk_pdf
from backend.vectorstore.store import add_documents, delete_document as vs_delete_document
from backend.agents.graph import run_pipeline
from backend.memory.conversation_memory import save_message, get_history, get_history_as_text
from backend.features.flashcards import generate_flashcards
from backend.features.roadmap import generate_roadmap
from backend.agents.quiz_agent import run_quiz_agent

app = FastAPI(title="Multi-Agent Research Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {"status": "ok", "service": "Multi-Agent Research Assistant"}


# ---------------------------------------------------------------------------
# Document upload / management
# ---------------------------------------------------------------------------
@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")

    doc_id = uuid.uuid4().hex[:8]
    save_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{file.filename}")
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc_id, chunks, num_pages = chunk_pdf(save_path, file.filename, doc_id=doc_id)
    if not chunks:
        raise HTTPException(422, "Could not extract any text from this PDF (it may be scanned/image-only).")

    num_chunks = add_documents(chunks)

    db_doc = Document(doc_id=doc_id, filename=file.filename, num_pages=num_pages)
    db.add(db_doc)
    db.commit()

    return UploadResponse(doc_id=doc_id, filename=file.filename, num_pages=num_pages, num_chunks=num_chunks)


@app.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    return [
        {"doc_id": d.doc_id, "filename": d.filename, "num_pages": d.num_pages, "uploaded_at": d.uploaded_at.isoformat()}
        for d in docs
    ]


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.doc_id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found.")
    vs_delete_document(doc_id)
    db.delete(doc)
    db.commit()
    return {"status": "deleted", "doc_id": doc_id}


# ---------------------------------------------------------------------------
# Chat (multi-agent pipeline)
# ---------------------------------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    history_text = get_history_as_text(db, req.session_id)

    result = run_pipeline(req.question, history=history_text, doc_ids=req.doc_ids)

    save_message(db, req.session_id, "user", req.question)
    save_message(db, req.session_id, "assistant", result["summary"], agent_trace=result.get("agent_trace"))

    citations = [Citation(**c) for c in result.get("citations", [])]

    return ChatResponse(
        answer=result["research_output"],
        summary=result["summary"],
        citations=citations,
        agent_trace=result.get("agent_trace", []),
    )


@app.get("/history/{session_id}", response_model=HistoryResponse)
def history(session_id: str, db: Session = Depends(get_db)):
    return HistoryResponse(session_id=session_id, messages=get_history(db, session_id))


# ---------------------------------------------------------------------------
# Flashcards
# ---------------------------------------------------------------------------
@app.post("/flashcards", response_model=FlashcardResponse)
def flashcards(req: FlashcardRequest, db: Session = Depends(get_db)):
    cards = generate_flashcards(req.topic, req.num_cards, doc_ids=req.doc_ids)
    for c in cards:
        db.add(Flashcard(
            session_id=req.session_id,
            doc_id=(req.doc_ids[0] if req.doc_ids else None),
            question=c.get("question", ""),
            answer=c.get("answer", ""),
            source_page=c.get("source_page", ""),
        ))
    db.commit()
    return FlashcardResponse(flashcards=[FlashcardItem(**c) for c in cards])


@app.get("/flashcards/{session_id}")
def get_flashcards(session_id: str, db: Session = Depends(get_db)):
    rows = db.query(Flashcard).filter(Flashcard.session_id == session_id).all()
    return [
        {"question": r.question, "answer": r.answer, "source_page": r.source_page}
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Quiz
# ---------------------------------------------------------------------------
@app.post("/quiz", response_model=QuizResponse)
def quiz(req: QuizRequest):
    questions = run_quiz_agent(req.topic, req.num_questions, req.difficulty, doc_ids=req.doc_ids)
    return QuizResponse(questions=[QuizQuestion(**q) for q in questions])


# ---------------------------------------------------------------------------
# Study Roadmap
# ---------------------------------------------------------------------------
@app.post("/roadmap", response_model=RoadmapResponse)
def roadmap(req: RoadmapRequest, db: Session = Depends(get_db)):
    plan = generate_roadmap(req.goal, req.weeks, doc_ids=req.doc_ids)
    import json
    db.add(RoadmapEntry(session_id=req.session_id, goal=req.goal, roadmap_json=json.dumps(plan)))
    db.commit()
    return RoadmapResponse(goal=req.goal, weeks=[RoadmapWeek(**w) for w in plan])


# ---------------------------------------------------------------------------
# Voice (optional)
# ---------------------------------------------------------------------------
@app.post("/voice/transcribe")
async def voice_transcribe(file: UploadFile = File(...)):
    from backend.voice.voice_io import transcribe_audio
    audio_bytes = await file.read()
    try:
        text = transcribe_audio(audio_bytes, filename_hint=file.filename)
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    return {"text": text}


@app.post("/voice/speak")
def voice_speak(text: str):
    from backend.voice.voice_io import synthesize_speech
    path = synthesize_speech(text)
    return FileResponse(path, media_type="audio/mpeg", filename="speech.mp3")
