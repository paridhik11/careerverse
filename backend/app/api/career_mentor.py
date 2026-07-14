"""Routes for the Career Mentor Chatbot.

Thin HTTP layer only: request/response shaping and translating
service/agent exceptions into appropriate HTTP status codes. All DB access
and context assembly live in the service/model layers.

Endpoints
---------
POST /career-mentor/chat
    Streams the mentor's response token-by-token as Server-Sent Events
    (text/event-stream). Persists both the user message and the complete
    assistant response to ``MentorMessage`` rows after streaming completes.

GET /career-mentor/history/{resume_id}
    Returns the full persisted conversation history for a resume so the
    sidebar can restore state on any page.

Streaming design
----------------
``StreamingResponse`` iterates the async generator and sends chunks to the
client. A ``BackgroundTask`` runs after the generator is exhausted to
persist both messages to the DB using a fresh session from ``SessionLocal``
(not the request-scoped session, which is closed when the response
completes).

SSE format: each chunk is sent as ``data: <json-encoded-text>\n\n``. The
sentinel ``data: [DONE]\n\n`` signals the end of the stream. The frontend
JSON-decodes each data payload so that newlines inside the model's text
survive the SSE framing correctly.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.agents import career_mentor as career_mentor_agent
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.mentor_message import (
    HISTORY_WINDOW,
    MentorChatRequest,
    MentorGeneralChatRequest,
    MentorHistoryResponse,
    MentorMessage,
    MentorMessageRecord,
)
from app.models.resume import Resume
from app.models.user import User
from app.services import mentor_context as mentor_context_service
from app.services import resume_store_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/career-mentor", tags=["career-mentor"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_history(db: Session, resume_id: int, limit: int = HISTORY_WINDOW) -> list[MentorMessage]:
    """Return the most recent `limit` messages for a resume, oldest-first."""
    rows = (
        db.query(MentorMessage)
        .filter(MentorMessage.resume_id == resume_id)
        .order_by(MentorMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(rows))


def _history_to_message_dicts(messages: list[MentorMessage]) -> list[dict[str, str]]:
    """Convert ORM rows to the ``{"role": ..., "content": ...}`` format."""
    return [{"role": m.role, "content": m.content} for m in messages]


def _persist_exchange(
    db: Session,
    resume_id: int,
    user_content: str,
    assistant_content: str,
) -> None:
    """Save a user+assistant exchange to the DB.

    Accepts the request-scoped ``db`` session. In FastAPI's request lifecycle,
    background tasks run before dependency cleanup, so the session is still
    valid when this is called as a ``BackgroundTask``.
    """
    try:
        now = datetime.now(timezone.utc)
        db.add(MentorMessage(resume_id=resume_id, role="user", content=user_content, created_at=now))
        db.add(
            MentorMessage(
                resume_id=resume_id,
                role="assistant",
                content=assistant_content,
                created_at=now,
            )
        )
        db.commit()
        logger.debug(
            "Mentor exchange persisted for resume_id=%s (%d user chars, %d assistant chars).",
            resume_id,
            len(user_content),
            len(assistant_content),
        )
    except Exception:
        logger.exception("Failed to persist mentor exchange for resume_id=%s.", resume_id)
        db.rollback()


async def _sse_generator(
    user_message: str,
    resume_id: int,
    context: str,
    history: list[dict[str, str]],
    buffer: list[str],
) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted chunks from the Career Mentor Agent.

    Accumulates the full response text in ``buffer`` so the background task
    can persist it after the generator is exhausted.

    Each data payload is JSON-encoded so that newlines inside the model's
    prose survive SSE framing correctly. The sentinel ``[DONE]`` is a plain
    string (not JSON) so the frontend can detect stream completion cheaply.
    """
    try:
        async for chunk in career_mentor_agent.stream_response(
            user_message=user_message,
            context=context,
            history=history,
        ):
            buffer.append(chunk)
            yield f"data: {json.dumps(chunk)}\n\n"
    except career_mentor_agent.CareerMentorTimeoutError as exc:
        error_msg = "The mentor took too long to respond. Please try again."
        yield f"data: {json.dumps(error_msg)}\n\n"
        logger.warning("Mentor stream timeout for resume_id=%s: %s", resume_id, exc)
    except career_mentor_agent.LLMRequestError as exc:
        error_msg = "The mentor encountered an error. Please try again."
        yield f"data: {json.dumps(error_msg)}\n\n"
        logger.error("Mentor stream error for resume_id=%s: %s", resume_id, exc)

    yield "data: [DONE]\n\n"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/chat/general",
    summary="Send a message to the Career Mentor without a resume (general career questions).",
    status_code=status.HTTP_200_OK,
)
async def mentor_chat_general(
    request: MentorGeneralChatRequest,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Stream the Career Mentor's response to a general career question.

    No resume is required.  The mentor answers from general career knowledge
    and the user's message only.  History is kept in memory for the session
    (no DB persistence for general chat — resumeId-scoped chat persists).

    HTTP status codes
    -----------------
    - 200: stream started successfully.
    - 400: message is empty.
    """
    if not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty.",
        )

    # General context — no resume data available.
    general_context = (
        "The user has not yet uploaded a resume. "
        "Answer their career question from general knowledge. "
        "Be helpful, encouraging, and specific. "
        "If they ask about their own resume or career matches, remind them to upload a resume first."
    )

    history = request.history or []
    buffer: list[str] = []

    async def _generator() -> AsyncGenerator[str, None]:
        async for chunk in _sse_generator(
            user_message=request.message,
            resume_id=0,
            context=general_context,
            history=history,
            buffer=buffer,
        ):
            yield chunk

    return StreamingResponse(
        _generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/chat",
    summary="Send a message to the Career Mentor and stream the response.",
    status_code=status.HTTP_200_OK,
)
async def mentor_chat(
    request: MentorChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Stream the Career Mentor's response to the user's message.

    The mentor's answer is streamed token-by-token as Server-Sent Events
    (``text/event-stream``). After the stream completes, both the user
    message and the full assistant response are persisted to ``MentorMessage``
    via a background task.

    Prerequisites
    -------------
    - ``POST /resumes`` — the resume must exist and belong to the current user.

    HTTP status codes
    -----------------
    - 200: stream started successfully.
    - 404: resume not found or does not belong to the current user.
    - 400: message is empty.
    """
    resume: Resume | None = resume_store_service.get_resume_by_id(db, request.resume_id)
    if resume is None or resume.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    # Assemble project context (pure DB reads — no LLM calls).
    context = mentor_context_service.assemble_context(db, resume)

    # Load recent history for conversational continuity.
    history_rows = _get_history(db, request.resume_id)
    history = _history_to_message_dicts(history_rows)

    # Buffer accumulates the full response for persistence after streaming.
    buffer: list[str] = []

    async def _generator() -> AsyncGenerator[str, None]:
        async for chunk in _sse_generator(
            user_message=request.message,
            resume_id=request.resume_id,
            context=context,
            history=history,
            buffer=buffer,
        ):
            yield chunk

    def _persist() -> None:
        _persist_exchange(
            db=db,
            resume_id=request.resume_id,
            user_content=request.message,
            assistant_content="".join(buffer),
        )

    background_tasks.add_task(_persist)

    return StreamingResponse(
        _generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/history/{resume_id}",
    response_model=MentorHistoryResponse,
    summary="Return the full conversation history for a resume.",
    status_code=status.HTTP_200_OK,
)
async def get_mentor_history(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MentorHistoryResponse:
    """Return all persisted mentor messages for the given resume.

    The sidebar calls this on mount to restore conversation state when
    navigating between pages.

    HTTP status codes
    -----------------
    - 200: history returned (may be an empty list if no messages yet).
    - 404: resume not found or does not belong to the current user.
    """
    resume: Resume | None = resume_store_service.get_resume_by_id(db, resume_id)
    if resume is None or resume.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    rows = (
        db.query(MentorMessage)
        .filter(MentorMessage.resume_id == resume_id)
        .order_by(MentorMessage.created_at.asc())
        .all()
    )

    return MentorHistoryResponse(
        messages=[
            MentorMessageRecord(
                id=r.id,
                resume_id=r.resume_id,
                role=r.role,  # type: ignore[arg-type]
                content=r.content,
                created_at=r.created_at,
            )
            for r in rows
        ]
    )
