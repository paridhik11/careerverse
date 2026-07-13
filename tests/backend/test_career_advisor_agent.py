"""Unit tests for the Career Recommendation Agent (Gemini is always mocked)."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from google.genai import errors

from app.agents import career_advisor

RETRIEVED_JDS = [
    {
        "job_description_id": "1",
        "role_title": "Software Engineer",
        "chunks": ["We are looking for a Software Engineer skilled in Python and FastAPI."],
    },
    {
        "job_description_id": "2",
        "role_title": "Data Scientist",
        "chunks": ["We are looking for a Data Scientist skilled in pandas and modeling."],
    },
    {
        "job_description_id": "3",
        "role_title": "Product Manager",
        "chunks": ["We are looking for a Product Manager to run sprint planning."],
    },
]

VALID_MATCHES_JSON = {
    "matches": [
        {
            "job_description_id": "1",
            "role_title": "Software Engineer",
            "match_percent": 91,
            "confidence_score": "High",
            "reasoning": "Strong Python and FastAPI experience directly matches the JD requirements.",
            "career_overview": "Builds and maintains backend services and APIs for the product.",
            "missing_skills": ["Kubernetes", "GraphQL"],
            "rank": 1,
        },
        {
            "job_description_id": "2",
            "role_title": "Data Scientist",
            "match_percent": 68,
            "confidence_score": "Medium",
            "reasoning": "Some data analysis exposure but limited modeling experience.",
            "career_overview": "Analyzes datasets and builds predictive models for the business.",
            "missing_skills": ["scikit-learn", "Statistics"],
            "rank": 2,
        },
        {
            "job_description_id": "3",
            "role_title": "Product Manager",
            "match_percent": 45,
            "confidence_score": "Low",
            "reasoning": "Resume shows little product or stakeholder management experience.",
            "career_overview": "Owns the roadmap and coordinates sprint planning across teams.",
            "missing_skills": ["Stakeholder management", "Roadmapping"],
            "rank": 3,
        },
    ]
}

SAMPLE_RESUME_TEXT = "Jane Doe\nSkills: Python, FastAPI, PostgreSQL\nExperience: Backend intern."


def _fake_response(content: str) -> SimpleNamespace:
    return SimpleNamespace(text=content)


def _install_fake_client(monkeypatch: pytest.MonkeyPatch, generate_mock: AsyncMock) -> None:
    fake_client = SimpleNamespace(
        aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate_mock))
    )
    monkeypatch.setattr(career_advisor, "_get_client", lambda: fake_client)


@pytest.mark.asyncio
async def test_generate_career_matches_returns_three_ranked_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generate_mock = AsyncMock(return_value=_fake_response(json.dumps(VALID_MATCHES_JSON)))
    _install_fake_client(monkeypatch, generate_mock)

    matches = await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)

    assert len(matches) == 3
    assert [m.rank for m in matches] == [1, 2, 3]
    assert {m.job_description_id for m in matches} == {"1", "2", "3"}
    assert all(0 <= m.match_percent <= 100 for m in matches)
    generate_mock.assert_awaited_once()
    call_kwargs = generate_mock.await_args.kwargs
    assert call_kwargs["model"] == "gemini-2.5-flash"
    assert isinstance(call_kwargs["contents"], str)
    assert call_kwargs["config"].temperature == 0.3
    assert call_kwargs["config"].response_mime_type == "application/json"


@pytest.mark.asyncio
async def test_generate_career_matches_extracts_json_from_code_fence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fenced = f"```json\n{json.dumps(VALID_MATCHES_JSON)}\n```"
    generate_mock = AsyncMock(return_value=_fake_response(fenced))
    _install_fake_client(monkeypatch, generate_mock)

    matches = await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)

    assert len(matches) == 3


@pytest.mark.asyncio
async def test_generate_career_matches_raises_when_no_jds_retrieved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(career_advisor.NoRetrievedJobDescriptionsError):
        await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, [])


@pytest.mark.asyncio
async def test_generate_career_matches_raises_on_malformed_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generate_mock = AsyncMock(return_value=_fake_response("not json at all"))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(career_advisor.InvalidCareerAdvisorResponseError):
        await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)


@pytest.mark.asyncio
async def test_generate_career_matches_raises_on_fewer_than_three_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad_payload = {"matches": VALID_MATCHES_JSON["matches"][:2]}
    generate_mock = AsyncMock(return_value=_fake_response(json.dumps(bad_payload)))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(career_advisor.InvalidCareerAdvisorResponseError):
        await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)


@pytest.mark.asyncio
async def test_generate_career_matches_raises_on_duplicate_ranks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad_payload = json.loads(json.dumps(VALID_MATCHES_JSON))
    bad_payload["matches"][1]["rank"] = 1  # duplicate rank
    generate_mock = AsyncMock(return_value=_fake_response(json.dumps(bad_payload)))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(career_advisor.InvalidCareerAdvisorResponseError):
        await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)


@pytest.mark.asyncio
async def test_generate_career_matches_raises_on_duplicate_job_description_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad_payload = json.loads(json.dumps(VALID_MATCHES_JSON))
    bad_payload["matches"][1]["job_description_id"] = "1"  # duplicate JD
    generate_mock = AsyncMock(return_value=_fake_response(json.dumps(bad_payload)))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(career_advisor.InvalidCareerAdvisorResponseError):
        await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)


@pytest.mark.asyncio
async def test_generate_career_matches_raises_when_jd_not_retrieved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A model hallucinating a job_description_id outside the retrieved set must be rejected."""
    bad_payload = json.loads(json.dumps(VALID_MATCHES_JSON))
    bad_payload["matches"][0]["job_description_id"] = "999"  # never retrieved
    generate_mock = AsyncMock(return_value=_fake_response(json.dumps(bad_payload)))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(career_advisor.InvalidCareerAdvisorResponseError):
        await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)


@pytest.mark.asyncio
async def test_generate_career_matches_raises_on_out_of_range_match_percent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad_payload = json.loads(json.dumps(VALID_MATCHES_JSON))
    bad_payload["matches"][0]["match_percent"] = 150
    generate_mock = AsyncMock(return_value=_fake_response(json.dumps(bad_payload)))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(career_advisor.InvalidCareerAdvisorResponseError):
        await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)


@pytest.mark.asyncio
async def test_generate_career_matches_raises_timeout_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generate_mock = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(career_advisor.CareerAdvisorTimeoutError):
        await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)


@pytest.mark.asyncio
async def test_generate_career_matches_raises_gemini_request_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generate_mock = AsyncMock(side_effect=errors.APIError(500, {"error": {"message": "boom"}}))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(career_advisor.GeminiRequestError):
        await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)
