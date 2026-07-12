"""
SQLite persistence layer using SQLAlchemy.
Stores: uploaded documents, chat history (memory), flashcards, quiz results.
"""
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from backend.config import settings

engine = create_engine(f"sqlite:///{settings.SQLITE_DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    doc_id = Column(String, unique=True, index=True)
    filename = Column(String)
    num_pages = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    session_id = Column(String, index=True)
    role = Column(String)  # "user" or "assistant"
    content = Column(Text)
    agent_trace = Column(Text, nullable=True)  # JSON string of which agents ran
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Flashcard(Base):
    __tablename__ = "flashcards"
    id = Column(Integer, primary_key=True)
    session_id = Column(String, index=True)
    doc_id = Column(String, nullable=True)
    question = Column(Text)
    answer = Column(Text)
    source_page = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class RoadmapEntry(Base):
    __tablename__ = "roadmaps"
    id = Column(Integer, primary_key=True)
    session_id = Column(String, index=True)
    goal = Column(Text)
    roadmap_json = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
