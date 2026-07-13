"""Unit tests for the Career Mentor Agent.

Gemini is always mocked — these tests verify:
- The agent streams text chunks when the skill gap context is present.
- The mentor prompt contains the "not yet generated" note for skill gap when
  the context block carries that annotation (hallucination guard).
- The mentor can be asked for interview questions and returns a response
  grounded in the assembled context (prompt includes JD text).
- httpx.TimeoutException is wrapped as CareerMentorTimeoutError.
- errors.APIError is wrapped as GeminiRequestError.
- The model name and temperature are passed to Gemini as specified.
- Conversation history is forwarded correctly in the messages list.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from google.genai import errors

from app.agents import career_mentor as career_mentor_agent
from app.prompts.career_mentor import CAREER_MENTOR_SYSTEM_PROMPT, build_mentor_user_prompt

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
# Helpers — fake streaming client
# ---------------------------------------------------------------------------


def _make_fake_chunk(text: str) -> SimpleNamespace:
    """Build a minimal streaming chunk object that mirrors Gemini's real shape."""
    return SimpleNamespace(text=text)


def _make_fake_stream(chunks: list[str]):
    """Return an async context manager / async iterator that yields fake chunks."""

    async def _aiter():
        for text in chunks:
            yield _make_fake_chunk(text)

    # The agent calls `await client.aio.models.generate_content_stream(...)` and
    # then iterates the returned object with `async for`. We need the stream
    # call to return an async iterable — we use a simple async generator.
    return _aiter()


def _install_fake_streaming_client(
    monkeypatch: pytest.MonkeyPatch,
    chunks: list[str],
) -> AsyncMock:
    """Monkeypatch the agent's `_get_client` to return a fake streaming client."""
    stream = _make_fake_stream(chunks)
    stream_mock = AsyncMock(return_value=stream)
    fake_client = SimpleNamespace(
        aio=SimpleNamespace(models=SimpleNamespace(generate_content_stream=stream_mock))
    )
    monkeypatch.setattr(career_mentor_agent, "_get_client", lambda: fake_client)
    return stream_mock


# ---------------------------------------------------------------------------
# Helper: collect all streamed chunks
# ---------------------------------------------------------------------------


async def _collect(gen) -> list[str]:
    """Drain an async generator and return all yielded values."""
    result = []
    async for chunk in gen:
        result.append(chunk)
    return result


def _content_text(content) -> str:
    return "".join(part.text or "" for part in content.parts)


def _contents_text(contents) -> str:
    return " ".join(_content_text(content) for content in contents)


# ---------------------------------------------------------------------------
# Tests: streaming output
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_response_yields_chunks_when_skill_gap_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When skill gap context is present, the agent streams non-empty chunks."""
    expected = ["Your readiness", " score is 65/100.", " TensorFlow is the key gap."]
    _install_fake_streaming_client(monkeypatch, expected)

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
    """When skill gap is missing from context, the agent still streams a response.

    The mentor should state the gap is missing rather than hallucinating.
    The test verifies the agent streams successfully — the prompt design
    (in `prompts/career_mentor.py`) enforces the "say what's missing" rule.
    """
    expected = ["The Skill Gap Agent has not run yet."]
    _install_fake_streaming_client(monkeypatch, expected)

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
async def test_stream_response_includes_skill_gap_context_in_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The skill gap data appears in the user turn sent to Gemini."""
    captured_kwargs: dict = {}

    async def capturing_stream(**kwargs):
        captured_kwargs.update(kwargs)
        return _make_fake_stream(["ok"])

    fake_client = SimpleNamespace(
        aio=SimpleNamespace(models=SimpleNamespace(generate_content_stream=capturing_stream))
    )
    monkeypatch.setattr(career_mentor_agent, "_get_client", lambda: fake_client)

    await _collect(
        career_mentor_agent.stream_response(
            user_message="Explain my gaps.",
            context=CONTEXT_WITH_SKILL_GAP,
            history=[],
        )
    )

    full_prompt = _contents_text(captured_kwargs["contents"])
    assert "TensorFlow" in full_prompt
    assert "SKILL GAP ANALYSIS" in full_prompt
    assert "Readiness Score: 65/100" in full_prompt


@pytest.mark.asyncio
async def test_stream_response_context_notes_missing_skill_gap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When skill gap is missing, the 'Not yet generated' note reaches the prompt."""
    captured_kwargs: dict = {}

    async def capturing_stream(**kwargs):
        captured_kwargs.update(kwargs)
        return _make_fake_stream(["ok"])

    fake_client = SimpleNamespace(
        aio=SimpleNamespace(models=SimpleNamespace(generate_content_stream=capturing_stream))
    )
    monkeypatch.setattr(career_mentor_agent, "_get_client", lambda: fake_client)

    await _collect(
        career_mentor_agent.stream_response(
            user_message="What are my missing skills?",
            context=CONTEXT_WITHOUT_SKILL_GAP,
            history=[],
        )
    )

    full_prompt = _contents_text(captured_kwargs["contents"])
    assert "Not yet generated" in full_prompt


@pytest.mark.asyncio
async def test_stream_response_interview_questions_grounded_in_jd(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Interview question requests include the JD text in the prompt sent to Gemini."""
    captured_kwargs: dict = {}

    async def capturing_stream(**kwargs):
        captured_kwargs.update(kwargs)
        return _make_fake_stream(["1. Tell me about a REST API project."])

    fake_client = SimpleNamespace(
        aio=SimpleNamespace(models=SimpleNamespace(generate_content_stream=capturing_stream))
    )
    monkeypatch.setattr(career_mentor_agent, "_get_client", lambda: fake_client)

    await _collect(
        career_mentor_agent.stream_response(
            user_message="Give me interview questions for my chosen role.",
            context=CONTEXT_WITH_CAREER_FOR_INTERVIEW,
            history=[],
        )
    )

    full_prompt = _contents_text(captured_kwargs["contents"])
    # The JD text mentions REST APIs — it must be in the prompt.
    assert "REST API" in full_prompt
    assert "Software Engineer" in full_prompt


# ---------------------------------------------------------------------------
# Tests: conversation history forwarded to Gemini
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_response_forwards_conversation_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prior conversation turns appear in the messages list sent to Gemini."""
    captured_kwargs: dict = {}

    async def capturing_stream(**kwargs):
        captured_kwargs.update(kwargs)
        return _make_fake_stream(["ok"])

    fake_client = SimpleNamespace(
        aio=SimpleNamespace(models=SimpleNamespace(generate_content_stream=capturing_stream))
    )
    monkeypatch.setattr(career_mentor_agent, "_get_client", lambda: fake_client)

    await _collect(
        career_mentor_agent.stream_response(
            user_message="What should I do next?",
            context=CONTEXT_WITH_SKILL_GAP,
            history=HISTORY_TURNS,
        )
    )

    contents = captured_kwargs["contents"]
    content_texts = [_content_text(content) for content in contents]

    # Both history turns must appear.
    assert "What is my readiness score?" in content_texts
    assert "Your readiness score is 65/100." in content_texts
    # The current user message must be the final Gemini content turn.
    assert contents[-1].role == "user"
    assert content_texts[-1] == "What should I do next?"


# ---------------------------------------------------------------------------
# Tests: Gemini call parameters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_response_uses_correct_model_and_temperature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The correct model name, temperature, and stream=True are passed to Gemini."""
    captured_kwargs: dict = {}

    async def capturing_stream(**kwargs):
        captured_kwargs.update(kwargs)
        return _make_fake_stream(["ok"])

    fake_client = SimpleNamespace(
        aio=SimpleNamespace(models=SimpleNamespace(generate_content_stream=capturing_stream))
    )
    monkeypatch.setattr(career_mentor_agent, "_get_client", lambda: fake_client)

    await _collect(
        career_mentor_agent.stream_response(
            user_message="Hello.",
            context=CONTEXT_WITH_SKILL_GAP,
            history=[],
        )
    )

    assert captured_kwargs["model"] == "gemini-2.5-flash"
    assert captured_kwargs["config"].temperature == career_mentor_agent.TEMPERATURE
    assert captured_kwargs["config"].system_instruction


# ---------------------------------------------------------------------------
# Tests: error wrapping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_response_wraps_timeout_on_create(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """httpx.TimeoutException raised during create is wrapped as CareerMentorTimeoutError."""
    stream_mock = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
    fake_client = SimpleNamespace(
        aio=SimpleNamespace(models=SimpleNamespace(generate_content_stream=stream_mock))
    )
    monkeypatch.setattr(career_mentor_agent, "_get_client", lambda: fake_client)

    with pytest.raises(career_mentor_agent.CareerMentorTimeoutError):
        await _collect(
            career_mentor_agent.stream_response(
                user_message="Hello.",
                context=CONTEXT_WITH_SKILL_GAP,
                history=[],
            )
        )


@pytest.mark.asyncio
async def test_stream_response_wraps_connection_error_on_create(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """errors.APIError raised during create is wrapped as GeminiRequestError."""
    stream_mock = AsyncMock(side_effect=errors.APIError(500, {"error": {"message": "boom"}}))
    fake_client = SimpleNamespace(
        aio=SimpleNamespace(models=SimpleNamespace(generate_content_stream=stream_mock))
    )
    monkeypatch.setattr(career_mentor_agent, "_get_client", lambda: fake_client)

    with pytest.raises(career_mentor_agent.GeminiRequestError):
        await _collect(
            career_mentor_agent.stream_response(
                user_message="Hello.",
                context=CONTEXT_WITH_SKILL_GAP,
                history=[],
            )
        )
