"""Unit tests for the Career Recommendation Agent (OpenRouter is always mocked)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from app.agents import career_advisor
from app.services.openrouter_client import OpenRouterServerError, OpenRouterTimeoutError

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


def _mock_chat_completion(monkeypatch: pytest.MonkeyPatch, return_value: str) -> AsyncMock:
    mock = AsyncMock(return_value=return_value)
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)
    return mock


@pytest.mark.asyncio
async def test_generate_career_matches_returns_three_ranked_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = _mock_chat_completion(monkeypatch, json.dumps(VALID_MATCHES_JSON))

    matches = await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)

    assert len(matches) == 3
    assert [m.rank for m in matches] == [1, 2, 3]
    assert {m.job_description_id for m in matches} == {"1", "2", "3"}
    assert all(0 <= m.match_percent <= 100 for m in matches)
    mock.assert_awaited_once()
    call_kwargs = mock.await_args.kwargs
    messages = call_kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert call_kwargs["temperature"] == 0.3


@pytest.mark.asyncio
async def test_generate_career_matches_extracts_json_from_code_fence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fenced = f"```json\n{json.dumps(VALID_MATCHES_JSON)}\n```"
    _mock_chat_completion(monkeypatch, fenced)

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
    _mock_chat_completion(monkeypatch, "not json at all")

    with pytest.raises(career_advisor.InvalidCareerAdvisorResponseError):
        await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)


@pytest.mark.asyncio
async def test_generate_career_matches_raises_on_fewer_than_three_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad_payload = {"matches": VALID_MATCHES_JSON["matches"][:2]}
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(career_advisor.InvalidCareerAdvisorResponseError):
        await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)


@pytest.mark.asyncio
async def test_generate_career_matches_raises_on_duplicate_ranks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad_payload = json.loads(json.dumps(VALID_MATCHES_JSON))
    bad_payload["matches"][1]["rank"] = 1  # duplicate rank
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(career_advisor.InvalidCareerAdvisorResponseError):
        await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)


@pytest.mark.asyncio
async def test_generate_career_matches_raises_on_duplicate_job_description_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad_payload = json.loads(json.dumps(VALID_MATCHES_JSON))
    bad_payload["matches"][1]["job_description_id"] = "1"  # duplicate JD
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(career_advisor.InvalidCareerAdvisorResponseError):
        await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)


@pytest.mark.asyncio
async def test_generate_career_matches_raises_when_jd_not_retrieved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A model hallucinating a job_description_id outside the retrieved set must be rejected."""
    bad_payload = json.loads(json.dumps(VALID_MATCHES_JSON))
    bad_payload["matches"][0]["job_description_id"] = "999"  # never retrieved
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(career_advisor.InvalidCareerAdvisorResponseError):
        await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)


@pytest.mark.asyncio
async def test_generate_career_matches_raises_on_out_of_range_match_percent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad_payload = json.loads(json.dumps(VALID_MATCHES_JSON))
    bad_payload["matches"][0]["match_percent"] = 150
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(career_advisor.InvalidCareerAdvisorResponseError):
        await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)


@pytest.mark.asyncio
async def test_generate_career_matches_raises_timeout_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=OpenRouterTimeoutError("timeout"))
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(career_advisor.CareerAdvisorTimeoutError):
        await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)


@pytest.mark.asyncio
async def test_generate_career_matches_raises_llm_request_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=OpenRouterServerError("server error"))
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(career_advisor.LLMRequestError):
        await career_advisor.generate_career_matches(SAMPLE_RESUME_TEXT, RETRIEVED_JDS)
