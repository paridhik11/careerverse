"""Unit tests for the Resume Reviewer Agent (Gemini is always mocked)."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from google.genai import errors

from app.agents import resume_reviewer
from app.models.resume import ParsedResume

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


def _fake_response(content: str) -> SimpleNamespace:
    return SimpleNamespace(text=content)


def _install_fake_client(monkeypatch: pytest.MonkeyPatch, generate_mock: AsyncMock) -> None:
    fake_client = SimpleNamespace(
        aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate_mock))
    )
    monkeypatch.setattr(resume_reviewer, "_get_client", lambda: fake_client)


@pytest.mark.asyncio
async def test_review_resume_returns_validated_report(monkeypatch: pytest.MonkeyPatch) -> None:
    generate_mock = AsyncMock(return_value=_fake_response(json.dumps(VALID_REVIEW_JSON)))
    _install_fake_client(monkeypatch, generate_mock)

    report = await resume_reviewer.review_resume(_sample_parsed_resume())

    assert report.overall_score == 78
    assert report.ats_score == 65
    assert len(report.strengths) == 3
    assert report.recommended_roles == ["Software Engineer", "Backend Developer", "Data Analyst"]
    generate_mock.assert_awaited_once()
    call_kwargs = generate_mock.await_args.kwargs
    assert call_kwargs["model"] == "gemini-2.5-flash"
    assert isinstance(call_kwargs["contents"], str)
    assert call_kwargs["config"].temperature == 0.3
    assert call_kwargs["config"].response_mime_type == "application/json"


@pytest.mark.asyncio
async def test_review_resume_extracts_json_from_code_fence(monkeypatch: pytest.MonkeyPatch) -> None:
    fenced = f"```json\n{json.dumps(VALID_REVIEW_JSON)}\n```"
    generate_mock = AsyncMock(return_value=_fake_response(fenced))
    _install_fake_client(monkeypatch, generate_mock)

    report = await resume_reviewer.review_resume(_sample_parsed_resume())

    assert report.overall_score == 78


@pytest.mark.asyncio
async def test_review_resume_raises_on_malformed_json(monkeypatch: pytest.MonkeyPatch) -> None:
    generate_mock = AsyncMock(return_value=_fake_response("not json at all"))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(resume_reviewer.InvalidReviewResponseError):
        await resume_reviewer.review_resume(_sample_parsed_resume())


@pytest.mark.asyncio
async def test_review_resume_raises_on_schema_violation(monkeypatch: pytest.MonkeyPatch) -> None:
    bad_payload = dict(VALID_REVIEW_JSON)
    bad_payload["overall_score"] = 150  # out of the 0-100 range
    generate_mock = AsyncMock(return_value=_fake_response(json.dumps(bad_payload)))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(resume_reviewer.InvalidReviewResponseError):
        await resume_reviewer.review_resume(_sample_parsed_resume())


@pytest.mark.asyncio
async def test_review_resume_raises_on_empty_response(monkeypatch: pytest.MonkeyPatch) -> None:
    generate_mock = AsyncMock(return_value=_fake_response(""))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(resume_reviewer.InvalidReviewResponseError):
        await resume_reviewer.review_resume(_sample_parsed_resume())


@pytest.mark.asyncio
async def test_review_resume_raises_timeout_error(monkeypatch: pytest.MonkeyPatch) -> None:
    generate_mock = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(resume_reviewer.ResumeReviewTimeoutError):
        await resume_reviewer.review_resume(_sample_parsed_resume())


@pytest.mark.asyncio
async def test_review_resume_raises_gemini_request_error(monkeypatch: pytest.MonkeyPatch) -> None:
    generate_mock = AsyncMock(side_effect=errors.APIError(500, {"error": {"message": "boom"}}))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(resume_reviewer.GeminiRequestError):
        await resume_reviewer.review_resume(_sample_parsed_resume())
