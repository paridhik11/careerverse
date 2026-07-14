"""Unit tests for the Career Mentor Agent (OpenRouter is always mocked).

These tests verify:
- The agent streams text chunks when the skill gap context is present.
- The mentor prompt contains the "not yet generated" note for skill gap when
  the context block carries that annotation (hallucination guard).
- The mentor can be asked for interview questions and returns a response
  grounded in the assembled context (prompt includes JD text).
- OpenRouterTimeoutError is wrapped as CareerMentorTimeoutError.
- OpenRouterServerError is wrapped as LLMRequestError.
- The temperature is passed to the OpenRouter client as specified.
- Conversation history is forwarded correctly in the messages list.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.agents import career_mentor as career_mentor_agent
from app.prompts.career_mentor import build_mentor_user_prompt
from app.services.openrouter_client import OpenRouterServerError, OpenRouterTimeoutError

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

CONTEXT_WITH_SKILL_GAP = """\
=== CANDIDATE RESUME ===
File: jane_doe.pdf
Name: Jane Doe
Skills: Python, SQL, pandas

=== RESUME REVIEW ===
Overall Score: 72/100
Summary: Strong data skills but limited ML experience.

=== CHOSEN CAREER ===
Role Title: Data Scientist
Match %: 82%
Job Description (full text, truncated):
We are looking for a Data Scientist proficient in Python, TensorFlow, and SQL.
Responsibilities include building predictive models and presenting findings to
stakeholders.

=== SKILL GAP ANALYSIS ===
Readiness Score: 65/100
Summary: Jane has solid Python and SQL foundations. The primary gaps are TensorFlow
and statistical modelling experience.
Missing technical skills: TensorFlow, Scikit-learn, Statistical modelling
Recommended next steps:
  1. Complete a hands-on TensorFlow project.
  2. Study statistical modelling fundamentals.

=== 3-MONTH LEARNING ROADMAP ===
Month 1: Build Python and ML foundations.
  Topics: Python, NumPy, pandas, basic ML concepts
"""

CONTEXT_WITHOUT_SKILL_GAP = """\
=== CANDIDATE RESUME ===
File: jane_doe.pdf
Name: Jane Doe
Skills: Python, SQL

=== RESUME REVIEW ===
Not yet available.

=== CHOSEN CAREER ===
Not yet selected. The user has not chosen a target career from their Top 3
recommendations. Skill gap and roadmap data are also unavailable until a
career is selected.

=== SKILL GAP ANALYSIS ===
Not yet generated. The Skill Gap Agent has not run for the selected career.

=== 3-MONTH LEARNING ROADMAP ===
Not yet generated. The Learning Roadmap Agent has not run for the selected career.
"""

CONTEXT_WITH_CAREER_FOR_INTERVIEW = """\
=== CANDIDATE RESUME ===
File: jane_doe.pdf
Skills: Python, SQL

=== CHOSEN CAREER ===
Role Title: Software Engineer
Match %: 78%
Job Description (full text, truncated):
We are looking for a Software Engineer with experience in Python, REST APIs,
Git, and collaborative team environments. Responsibilities: design and implement
scalable backend services, write unit tests, participate in code reviews.

=== SKILL GAP ANALYSIS ===
Not yet generated.

=== 3-MONTH LEARNING ROADMAP ===
Not yet generated.
"""

HISTORY_TURNS = [
    {"role": "user", "content": "What is my readiness score?"},
    {"role": "assistant", "content": "Your readiness score is 65/100."},
]


# ---------------------------------------------------------------------------
# Helper: async generator mock for streaming
# ---------------------------------------------------------------------------


def _make_stream_mock(chunks: list[str]):
    """Return an async generator that yields the given chunks."""

    async def _fake_stream(**kwargs):
        for chunk in chunks:
            yield chunk

    return _fake_stream


async def _collect(gen) -> list[str]:
    """Drain an async generator and return all yielded values."""
    result = []
    async for chunk in gen:
        result.append(chunk)
    return result


# ---------------------------------------------------------------------------
# Tests: streaming output
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_response_yields_chunks_when_skill_gap_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When skill gap context is present, the agent streams non-empty chunks."""
    expected = ["Your readiness", " score is 65/100.", " TensorFlow is the key gap."]
    monkeypatch.setattr(
        "app.services.openrouter_client.stream_chat_completion",
        _make_stream_mock(expected),
    )

    chunks = await _collect(
        career_mentor_agent.stream_response(
            user_message="What is my skill gap?",
            context=CONTEXT_WITH_SKILL_GAP,
            history=[],
        )
    )

    assert chunks == expected
    assert all(isinstance(c, str) for c in chunks)


@pytest.mark.asyncio
async def test_stream_response_yields_chunks_when_skill_gap_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When skill gap is missing from context, the agent still streams a response."""
    expected = ["The Skill Gap Agent has not run yet."]
    monkeypatch.setattr(
        "app.services.openrouter_client.stream_chat_completion",
        _make_stream_mock(expected),
    )

    chunks = await _collect(
        career_mentor_agent.stream_response(
            user_message="What skills am I missing?",
            context=CONTEXT_WITHOUT_SKILL_GAP,
            history=[],
        )
    )

    assert len(chunks) > 0
    assert "".join(chunks) == "The Skill Gap Agent has not run yet."


@pytest.mark.asyncio
async def test_stream_response_includes_skill_gap_context_in_messages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The skill gap data appears in the messages list sent to the LLM."""
    captured_messages: list = []

    async def capturing_stream(messages, **kwargs):
        captured_messages.extend(messages)
        yield "ok"

    monkeypatch.setattr(
        "app.services.openrouter_client.stream_chat_completion",
        capturing_stream,
    )

    await _collect(
        career_mentor_agent.stream_response(
            user_message="Explain my gaps.",
            context=CONTEXT_WITH_SKILL_GAP,
            history=[],
        )
    )

    full_prompt = " ".join(m["content"] for m in captured_messages)
    assert "TensorFlow" in full_prompt
    assert "SKILL GAP ANALYSIS" in full_prompt
    assert "Readiness Score: 65/100" in full_prompt


@pytest.mark.asyncio
async def test_stream_response_context_notes_missing_skill_gap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When skill gap is missing, the 'Not yet generated' note reaches the prompt."""
    captured_messages: list = []

    async def capturing_stream(messages, **kwargs):
        captured_messages.extend(messages)
        yield "ok"

    monkeypatch.setattr(
        "app.services.openrouter_client.stream_chat_completion",
        capturing_stream,
    )

    await _collect(
        career_mentor_agent.stream_response(
            user_message="What are my missing skills?",
            context=CONTEXT_WITHOUT_SKILL_GAP,
            history=[],
        )
    )

    full_prompt = " ".join(m["content"] for m in captured_messages)
    assert "Not yet generated" in full_prompt


@pytest.mark.asyncio
async def test_stream_response_interview_questions_grounded_in_jd(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Interview question requests include the JD text in the messages sent to the LLM."""
    captured_messages: list = []

    async def capturing_stream(messages, **kwargs):
        captured_messages.extend(messages)
        yield "1. Tell me about a REST API project."

    monkeypatch.setattr(
        "app.services.openrouter_client.stream_chat_completion",
        capturing_stream,
    )

    await _collect(
        career_mentor_agent.stream_response(
            user_message="Give me interview questions for my chosen role.",
            context=CONTEXT_WITH_CAREER_FOR_INTERVIEW,
            history=[],
        )
    )

    full_prompt = " ".join(m["content"] for m in captured_messages)
    assert "REST API" in full_prompt
    assert "Software Engineer" in full_prompt


# ---------------------------------------------------------------------------
# Tests: conversation history forwarded to LLM
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_response_forwards_conversation_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prior conversation turns appear in the messages list sent to the LLM."""
    captured_messages: list = []

    async def capturing_stream(messages, **kwargs):
        captured_messages.extend(messages)
        yield "ok"

    monkeypatch.setattr(
        "app.services.openrouter_client.stream_chat_completion",
        capturing_stream,
    )

    await _collect(
        career_mentor_agent.stream_response(
            user_message="What should I do next?",
            context=CONTEXT_WITH_SKILL_GAP,
            history=HISTORY_TURNS,
        )
    )

    contents = [m["content"] for m in captured_messages]

    assert "What is my readiness score?" in contents
    assert "Your readiness score is 65/100." in contents
    # Current user message must be last.
    assert captured_messages[-1]["role"] == "user"
    assert captured_messages[-1]["content"] == "What should I do next?"


# ---------------------------------------------------------------------------
# Tests: LLM call parameters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_response_uses_correct_temperature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The correct temperature is passed to the OpenRouter streaming client."""
    captured_kwargs: dict = {}

    async def capturing_stream(messages, **kwargs):
        captured_kwargs["messages"] = messages
        captured_kwargs.update(kwargs)
        yield "ok"

    monkeypatch.setattr(
        "app.services.openrouter_client.stream_chat_completion",
        capturing_stream,
    )

    await _collect(
        career_mentor_agent.stream_response(
            user_message="Hello.",
            context=CONTEXT_WITH_SKILL_GAP,
            history=[],
        )
    )

    assert captured_kwargs.get("temperature") == career_mentor_agent.TEMPERATURE
    assert captured_kwargs["messages"][0]["role"] == "system"


# ---------------------------------------------------------------------------
# Tests: error wrapping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_response_wraps_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenRouterTimeoutError is wrapped as CareerMentorTimeoutError."""

    async def timeout_stream(**kwargs):
        raise OpenRouterTimeoutError("timeout")
        yield  # make it a generator

    monkeypatch.setattr(
        "app.services.openrouter_client.stream_chat_completion",
        timeout_stream,
    )

    with pytest.raises(career_mentor_agent.CareerMentorTimeoutError):
        await _collect(
            career_mentor_agent.stream_response(
                user_message="Hello.",
                context=CONTEXT_WITH_SKILL_GAP,
                history=[],
            )
        )


@pytest.mark.asyncio
async def test_stream_response_wraps_server_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenRouterServerError is wrapped as LLMRequestError."""

    async def error_stream(**kwargs):
        raise OpenRouterServerError("server error")
        yield  # make it a generator

    monkeypatch.setattr(
        "app.services.openrouter_client.stream_chat_completion",
        error_stream,
    )

    with pytest.raises(career_mentor_agent.LLMRequestError):
        await _collect(
            career_mentor_agent.stream_response(
                user_message="Hello.",
                context=CONTEXT_WITH_SKILL_GAP,
                history=[],
            )
        )
