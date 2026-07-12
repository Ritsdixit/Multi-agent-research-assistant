"""
Conversation memory: persists chat turns per session_id in SQLite so the
Research Agent can use prior context, and users can revisit past sessions.
"""
import json
from sqlalchemy.orm import Session

from backend.database import ChatMessage


def save_message(db: Session, session_id: str, role: str, content: str, agent_trace: list[str] | None = None):
    msg = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        agent_trace=json.dumps(agent_trace) if agent_trace else None,
    )
    db.add(msg)
    db.commit()


def get_history(db: Session, session_id: str, limit: int = 20) -> list[dict]:
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "role": r.role,
            "content": r.content,
            "agent_trace": json.loads(r.agent_trace) if r.agent_trace else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


def get_history_as_text(db: Session, session_id: str, max_turns: int = 6) -> str:
    """Recent history formatted for injection into agent prompts."""
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(max_turns)
        .all()
    )
    rows.reverse()
    lines = [f"{r.role.upper()}: {r.content}" for r in rows]
    return "\n".join(lines)
