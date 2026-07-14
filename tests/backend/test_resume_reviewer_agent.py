"""Unit tests for the Resume Reviewer Agent (OpenRouter is always mocked)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents import resume_reviewer
from app.models.resume import ParsedResume
from app.services.ats_scorer import ATSScoreBreakdown
from app.services.openrouter_client import OpenRouterServerError, OpenRouterTimeoutError

VALID_REVIEW_JSON = {
    "overall_score": 78,
    "ats_score": 65,
    "summary": "A solid early-career resume with strong project work but light on quantified impact.",
    "strengths": ["Strong technical projects", "Good programming skills", "Relevant coursework"],
    "weaknesses": ["Missing quantified achievements", "Weak project descriptions", "No internship experience"],
    "ats_issues": ["Missing keywords", "No dedicated technical skills section"],
    "suggestions": ["Quantify project impact.", "Add a technical skills section."],
    "recommended_roles": ["Software Engineer", "Backend Developer", "Data Analyst"],
}


def _sample_parsed_resume() -> ParsedResume:
    return ParsedResume(
        full_text="Jane Doe\njane@example.com\n\nSkills\nPython, FastAPI\n",
        name="Jane Doe",
        email="jane@example.com",
        phone=None,
        skills="Python, FastAPI",
        education="B.S. Computer Science",
        experience="",
        projects="CareerVerse AI",
    )


def _mock_chat_completion(monkeypatch: pytest.MonkeyPatch, return_value: str) -> AsyncMock:
    mock = AsyncMock(return_value=return_value)
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)
    return mock


def _mock_ats_scores(
    monkeypatch: pytest.MonkeyPatch,
    overall_score: int,
    ats_score: int,
) -> MagicMock:
    """Patch compute_ats_scores so the deterministic override uses predictable values."""
    fake = ATSScoreBreakdown(
        overall_score=overall_score,
        ats_score=ats_score,
        structure_score=0,
        skills_score=0,
        experience_score=0,
        projects_score=0,
        education_score=0,
        formatting_score=0,
        sections_present=[],
        sections_missing=[],
        action_verb_count=0,
        metric_count=0,
        word_count=0,
    )
    mock = MagicMock(return_value=fake)
    monkeypatch.setattr("app.agents.resume_reviewer.compute_ats_scores", mock)
    return mock


@pytest.mark.asyncio
async def test_review_resume_returns_validated_report(monkeypatch: pytest.MonkeyPatch) -> None:
    mock = _mock_chat_completion(monkeypatch, json.dumps(VALID_REVIEW_JSON))
    _mock_ats_scores(monkeypatch, overall_score=78, ats_score=65)

    report = await resume_reviewer.review_resume(_sample_parsed_resume())

    assert report.overall_score == 78
    assert report.ats_score == 65
    assert len(report.strengths) == 3
    assert report.recommended_roles == ["Software Engineer", "Backend Developer", "Data Analyst"]
    mock.assert_awaited_once()
    call_kwargs = mock.await_args.kwargs
    messages = call_kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert call_kwargs["temperature"] == 0.1


@pytest.mark.asyncio
async def test_review_resume_extracts_json_from_code_fence(monkeypatch: pytest.MonkeyPatch) -> None:
    fenced = f"```json\n{json.dumps(VALID_REVIEW_JSON)}\n```"
    _mock_chat_completion(monkeypatch, fenced)
    _mock_ats_scores(monkeypatch, overall_score=78, ats_score=65)

    report = await resume_reviewer.review_resume(_sample_parsed_resume())

    assert report.overall_score == 78


@pytest.mark.asyncio
async def test_review_resume_raises_on_malformed_json(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_chat_completion(monkeypatch, "not json at all")

    with pytest.raises(resume_reviewer.InvalidReviewResponseError):
        await resume_reviewer.review_resume(_sample_parsed_resume())


@pytest.mark.asyncio
async def test_review_resume_pads_short_strengths_and_weaknesses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenRouter 200 + under-length lists must not become InvalidReviewResponseError."""
    short_payload = dict(VALID_REVIEW_JSON)
    short_payload["strengths"] = ["Only one strength"]
    short_payload["weaknesses"] = ["Only one weakness"]
    short_payload["recommended_roles"] = ["Software Engineer"]
    _mock_chat_completion(monkeypatch, json.dumps(short_payload))
    _mock_ats_scores(monkeypatch, overall_score=78, ats_score=65)

    report = await resume_reviewer.review_resume(_sample_parsed_resume())

    assert len(report.strengths) >= 3
    assert len(report.weaknesses) >= 3
    assert len(report.recommended_roles) >= 3
    assert report.overall_score == 78
    assert report.ats_score == 65


@pytest.mark.asyncio
async def test_review_resume_coerces_out_of_range_scores(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad_payload = dict(VALID_REVIEW_JSON)
    bad_payload["overall_score"] = 150  # out of the 0-100 range — coerced then overwritten
    bad_payload["ats_score"] = -5
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))
    _mock_ats_scores(monkeypatch, overall_score=78, ats_score=65)

    report = await resume_reviewer.review_resume(_sample_parsed_resume())

    # Deterministic ATS override wins after parse.
    assert report.overall_score == 78
    assert report.ats_score == 65


@pytest.mark.asyncio
async def test_review_resume_raises_on_empty_response(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_chat_completion(monkeypatch, "")

    with pytest.raises(resume_reviewer.InvalidReviewResponseError):
        await resume_reviewer.review_resume(_sample_parsed_resume())


@pytest.mark.asyncio
async def test_review_resume_raises_timeout_error(monkeypatch: pytest.MonkeyPatch) -> None:
    mock = AsyncMock(side_effect=OpenRouterTimeoutError("timeout"))
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(resume_reviewer.ResumeReviewTimeoutError):
        await resume_reviewer.review_resume(_sample_parsed_resume())


@pytest.mark.asyncio
async def test_review_resume_raises_llm_request_error(monkeypatch: pytest.MonkeyPatch) -> None:
    mock = AsyncMock(side_effect=OpenRouterServerError("server error"))
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(resume_reviewer.LLMRequestError):
        await resume_reviewer.review_resume(_sample_parsed_resume())
