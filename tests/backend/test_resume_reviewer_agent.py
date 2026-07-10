"""Unit tests for the Resume Reviewer Agent (OpenAI is always mocked)."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from openai import APIConnectionError, APITimeoutError

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


def _fake_completion(content: str) -> SimpleNamespace:
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


def _install_fake_client(monkeypatch: pytest.MonkeyPatch, create_mock: AsyncMock) -> None:
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create_mock))
    )
    monkeypatch.setattr(resume_reviewer, "_get_client", lambda: fake_client)


@pytest.mark.asyncio
async def test_review_resume_returns_validated_report(monkeypatch: pytest.MonkeyPatch) -> None:
    create_mock = AsyncMock(return_value=_fake_completion(json.dumps(VALID_REVIEW_JSON)))
    _install_fake_client(monkeypatch, create_mock)

    report = await resume_reviewer.review_resume(_sample_parsed_resume())

    assert report.overall_score == 78
    assert report.ats_score == 65
    assert len(report.strengths) == 3
    assert report.recommended_roles == ["Software Engineer", "Backend Developer", "Data Analyst"]
    create_mock.assert_awaited_once()
    call_kwargs = create_mock.await_args.kwargs
    assert call_kwargs["model"] == "gpt-4o"
    assert call_kwargs["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_review_resume_extracts_json_from_code_fence(monkeypatch: pytest.MonkeyPatch) -> None:
    fenced = f"```json\n{json.dumps(VALID_REVIEW_JSON)}\n```"
    create_mock = AsyncMock(return_value=_fake_completion(fenced))
    _install_fake_client(monkeypatch, create_mock)

    report = await resume_reviewer.review_resume(_sample_parsed_resume())

    assert report.overall_score == 78


@pytest.mark.asyncio
async def test_review_resume_raises_on_malformed_json(monkeypatch: pytest.MonkeyPatch) -> None:
    create_mock = AsyncMock(return_value=_fake_completion("not json at all"))
    _install_fake_client(monkeypatch, create_mock)

    with pytest.raises(resume_reviewer.InvalidReviewResponseError):
        await resume_reviewer.review_resume(_sample_parsed_resume())


@pytest.mark.asyncio
async def test_review_resume_raises_on_schema_violation(monkeypatch: pytest.MonkeyPatch) -> None:
    bad_payload = dict(VALID_REVIEW_JSON)
    bad_payload["overall_score"] = 150  # out of the 0-100 range
    create_mock = AsyncMock(return_value=_fake_completion(json.dumps(bad_payload)))
    _install_fake_client(monkeypatch, create_mock)

    with pytest.raises(resume_reviewer.InvalidReviewResponseError):
        await resume_reviewer.review_resume(_sample_parsed_resume())


@pytest.mark.asyncio
async def test_review_resume_raises_on_empty_response(monkeypatch: pytest.MonkeyPatch) -> None:
    create_mock = AsyncMock(return_value=_fake_completion(""))
    _install_fake_client(monkeypatch, create_mock)

    with pytest.raises(resume_reviewer.InvalidReviewResponseError):
        await resume_reviewer.review_resume(_sample_parsed_resume())


@pytest.mark.asyncio
async def test_review_resume_raises_timeout_error(monkeypatch: pytest.MonkeyPatch) -> None:
    request = SimpleNamespace()
    create_mock = AsyncMock(side_effect=APITimeoutError(request=request))
    _install_fake_client(monkeypatch, create_mock)

    with pytest.raises(resume_reviewer.ResumeReviewTimeoutError):
        await resume_reviewer.review_resume(_sample_parsed_resume())


@pytest.mark.asyncio
async def test_review_resume_raises_openai_request_error(monkeypatch: pytest.MonkeyPatch) -> None:
    request = SimpleNamespace()
    create_mock = AsyncMock(side_effect=APIConnectionError(request=request))
    _install_fake_client(monkeypatch, create_mock)

    with pytest.raises(resume_reviewer.OpenAIRequestError):
        await resume_reviewer.review_resume(_sample_parsed_resume())
