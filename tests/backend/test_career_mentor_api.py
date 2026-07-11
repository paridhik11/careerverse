"""Integration tests for the Career Mentor API.

Uses an in-memory SQLite DB (via the shared `client` fixture from conftest.py)
and mocks the Career Mentor Agent so no real OpenAI calls are made.

Tests verify:
- Conversation history is persisted and returned correctly by
  GET /career-mentor/history/{resume_id}.
- POST /career-mentor/chat returns a streaming SSE response.
- History accumulates correctly across multiple exchanges.
- POST /career-mentor/chat returns 404 for an unknown resume.
- GET /career-mentor/history/{resume_id} returns 404 for an unknown resume.
- GET /career-mentor/history/{resume_id} returns an empty list when no
  messages exist yet.
"""

from __future__ import annotations

import io
import json
from types import SimpleNamespace
from unittest.mock import patch

import fitz
import pytest

# ---------------------------------------------------------------------------
# Helpers — seed a user + resume in the test DB via API calls
# ---------------------------------------------------------------------------

SIGNUP_PAYLOAD = {"email": "mentor_test@example.com", "password": "TestPass123!"}


def _signup_and_login(client) -> str:
    """Register a user, log in, and return the bearer token."""
    client.post("/signup", json=SIGNUP_PAYLOAD)
    res = client.post("/login", json=SIGNUP_PAYLOAD)
    assert res.status_code == 200, f"Login failed: {res.json()}"
    return res.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _make_pdf_bytes(text: str) -> bytes:
    """Create a real PDF with extractable text using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(50, 50, 550, 780), text, fontsize=11, fontname="helv")
    data = doc.tobytes()
    doc.close()
    return data


_SAMPLE_PDF = _make_pdf_bytes(
    "Jane Doe\njane.doe@example.com\n\n"
    "Skills\nPython, SQL, pandas, FastAPI\n\n"
    "Education\nB.S. Computer Science\n\n"
    "Experience\nJunior Analyst at FinCo — 1 year\n\n"
    "Projects\nCareerVerse AI — AI-powered career platform\n"
)


def _upload_resume(client, token: str) -> int:
    """Upload a real PDF with extractable text and return the resume id."""
    res = client.post(
        "/resumes",
        files={"file": ("test_resume.pdf", io.BytesIO(_SAMPLE_PDF), "application/pdf")},
        headers=_auth_headers(token),
    )
    assert res.status_code in (200, 201), f"Resume upload failed: {res.json()}"
    return res.json()["id"]


# ---------------------------------------------------------------------------
# Fake async generator for the mentor agent
# ---------------------------------------------------------------------------


async def _fake_stream_response(user_message, context, history):
    """Yields two text chunks — simulates a complete mentor response."""
    yield "Great question! "
    yield "Here is your answer."


# ---------------------------------------------------------------------------
# Tests: GET /career-mentor/history/{resume_id}
# ---------------------------------------------------------------------------


def test_get_history_returns_empty_list_when_no_messages(client) -> None:
    """History endpoint returns an empty list for a resume with no messages yet."""
    token = _signup_and_login(client)
    resume_id = _upload_resume(client, token)

    res = client.get(f"/career-mentor/history/{resume_id}", headers=_auth_headers(token))
    assert res.status_code == 200
    data = res.json()
    assert data["messages"] == []


def test_get_history_returns_404_for_unknown_resume(client) -> None:
    """History endpoint returns 404 for a resume ID that doesn't exist."""
    token = _signup_and_login(client)

    res = client.get("/career-mentor/history/99999", headers=_auth_headers(token))
    assert res.status_code == 404


def test_get_history_requires_authentication(client) -> None:
    """History endpoint returns 401 when no bearer token is provided."""
    res = client.get("/career-mentor/history/1")
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# Tests: POST /career-mentor/chat (streaming)
# ---------------------------------------------------------------------------


def test_chat_streams_sse_response(client) -> None:
    """POST /career-mentor/chat returns a streaming SSE response."""
    token = _signup_and_login(client)
    resume_id = _upload_resume(client, token)

    with patch(
        "app.agents.career_mentor.stream_response",
        side_effect=_fake_stream_response,
    ):
        res = client.post(
            "/career-mentor/chat",
            json={"resume_id": resume_id, "message": "Why did Software Engineer match me?"},
            headers=_auth_headers(token),
        )

    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]

    # Decode the full SSE body.
    body = res.text
    assert "data: " in body
    # Verify the two expected chunks appear as JSON-encoded SSE events.
    assert json.dumps("Great question! ") in body
    assert json.dumps("Here is your answer.") in body
    # Verify the [DONE] sentinel.
    assert "data: [DONE]" in body


def test_chat_returns_404_for_unknown_resume(client) -> None:
    """POST /career-mentor/chat returns 404 for a resume ID that doesn't exist."""
    token = _signup_and_login(client)

    res = client.post(
        "/career-mentor/chat",
        json={"resume_id": 99999, "message": "Hello!"},
        headers=_auth_headers(token),
    )
    assert res.status_code == 404


def test_chat_requires_authentication(client) -> None:
    """POST /career-mentor/chat returns 401 when no bearer token is provided."""
    res = client.post(
        "/career-mentor/chat",
        json={"resume_id": 1, "message": "Hello!"},
    )
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# Tests: conversation history persistence
# ---------------------------------------------------------------------------


def test_history_persists_after_chat(client) -> None:
    """After a chat exchange, GET history returns the persisted messages."""
    token = _signup_and_login(client)
    resume_id = _upload_resume(client, token)

    with patch(
        "app.agents.career_mentor.stream_response",
        side_effect=_fake_stream_response,
    ):
        # Trigger the chat — background task persists the exchange synchronously
        # in TestClient because ASGI runs background tasks before the response
        # returns in test mode.
        client.post(
            "/career-mentor/chat",
            json={"resume_id": resume_id, "message": "What is my skill gap?"},
            headers=_auth_headers(token),
        )

    history_res = client.get(
        f"/career-mentor/history/{resume_id}",
        headers=_auth_headers(token),
    )
    assert history_res.status_code == 200
    messages = history_res.json()["messages"]

    assert len(messages) == 2
    user_msg = messages[0]
    assistant_msg = messages[1]

    assert user_msg["role"] == "user"
    assert user_msg["content"] == "What is my skill gap?"
    assert user_msg["resume_id"] == resume_id

    assert assistant_msg["role"] == "assistant"
    assert assistant_msg["content"] == "Great question! Here is your answer."
    assert assistant_msg["resume_id"] == resume_id


def test_history_accumulates_across_multiple_exchanges(client) -> None:
    """Multiple chat exchanges accumulate in history, oldest first."""
    token = _signup_and_login(client)
    resume_id = _upload_resume(client, token)

    messages_to_send = [
        "What career was recommended?",
        "What skills am I missing?",
        "Generate interview questions for my role.",
    ]

    with patch(
        "app.agents.career_mentor.stream_response",
        side_effect=_fake_stream_response,
    ):
        for msg in messages_to_send:
            client.post(
                "/career-mentor/chat",
                json={"resume_id": resume_id, "message": msg},
                headers=_auth_headers(token),
            )

    history_res = client.get(
        f"/career-mentor/history/{resume_id}",
        headers=_auth_headers(token),
    )
    assert history_res.status_code == 200
    history = history_res.json()["messages"]

    # 3 user messages + 3 assistant responses = 6 total.
    assert len(history) == 6

    # Verify user messages appear in order.
    user_messages = [m for m in history if m["role"] == "user"]
    assert [m["content"] for m in user_messages] == messages_to_send


def test_history_is_resume_scoped(client) -> None:
    """Messages for one resume do not appear in another resume's history.

    Creates two resumes for the same user and verifies isolation.
    """
    token = _signup_and_login(client)
    resume_id_1 = _upload_resume(client, token)
    resume_id_2 = _upload_resume(client, token)

    with patch(
        "app.agents.career_mentor.stream_response",
        side_effect=_fake_stream_response,
    ):
        client.post(
            "/career-mentor/chat",
            json={"resume_id": resume_id_1, "message": "Message for resume 1."},
            headers=_auth_headers(token),
        )

    history_1 = client.get(
        f"/career-mentor/history/{resume_id_1}",
        headers=_auth_headers(token),
    ).json()["messages"]

    history_2 = client.get(
        f"/career-mentor/history/{resume_id_2}",
        headers=_auth_headers(token),
    ).json()["messages"]

    assert len(history_1) == 2  # user + assistant
    assert len(history_2) == 0  # no messages for resume 2
