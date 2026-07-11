"""Pydantic schemas and the SQLAlchemy `MentorMessage` model.

A `MentorMessage` is one turn in the Career Mentor Chatbot conversation,
persisted so the conversation survives page navigation. Each message belongs
to a resume: the chatbot is scoped to the user's own project data.

Role is either "user" (the candidate's message) or "assistant" (the mentor's
response). Both sides of every exchange are stored so the full conversation
can be restored on any page that mounts the sidebar.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

MessageRole = Literal["user", "assistant"]

HISTORY_WINDOW = 10  # messages sent to GPT-4o for context continuity


# ---------------------------------------------------------------------------
# SQLAlchemy ORM model
# ---------------------------------------------------------------------------


class MentorMessage(Base):
    """One conversational turn in the Career Mentor Chatbot.

    Persisted per-resume so the sidebar restores history across page
    navigation. The `role` column is either "user" or "assistant".
    `content` is the raw text of the message — the mentor returns plain
    conversational prose, never structured JSON.
    """

    __tablename__ = "mentor_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    resume_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("resumes.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Pydantic read model
# ---------------------------------------------------------------------------


class MentorMessageRecord(BaseModel):
    """Read model for a persisted `MentorMessage` — returned by the history API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    resume_id: int
    role: MessageRole
    content: str
    created_at: datetime


# ---------------------------------------------------------------------------
# API request / response models
# ---------------------------------------------------------------------------


class MentorChatRequest(BaseModel):
    """Request body for POST /career-mentor/chat."""

    resume_id: int = Field(description="Id of the resume to use as context.")
    message: str = Field(min_length=1, description="The user's message to the mentor.")


class MentorHistoryResponse(BaseModel):
    """Returned by GET /career-mentor/history/{resume_id}."""

    messages: list[MentorMessageRecord]
