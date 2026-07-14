"""Unit tests for the Skill Gap Analysis Agent (OpenRouter is always mocked).

These tests verify:
- Valid JSON is parsed and validated correctly into SkillGapContent.
- JSON wrapped in a markdown code fence is handled by the fallback extractor.
- Empty JD text raises InvalidSkillGapResponseError before any API call.
- Empty resume text raises InvalidSkillGapResponseError before any API call.
- Malformed JSON raises InvalidSkillGapResponseError.
- Schema violations (out-of-range score, missing required fields) raise
  InvalidSkillGapResponseError.
- OpenRouterTimeoutError is wrapped as SkillGapAgentTimeoutError.
- OpenRouterServerError is wrapped as LLMRequestError.
- The messages list and temperature are passed to the OpenRouter client correctly.
- Optional inputs (resume_review_summary, simulation_metadata) are accepted
  without error.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from app.agents import skill_gap as skill_gap_agent
from app.services.openrouter_client import OpenRouterServerError, OpenRouterTimeoutError

# ---------------------------------------------------------------------------
# Sample inputs
# ---------------------------------------------------------------------------

SAMPLE_ROLE = "Data Analyst"
SAMPLE_JD = (
    "We are looking for a Data Analyst proficient in Python, SQL, and Tableau. "
    "The role requires strong analytical thinking, clear communication, and the "
    "ability to collaborate with cross-functional teams. Experience with pandas, "
    "data cleaning, and building dashboards is essential."
)
SAMPLE_RESUME = (
    "John Doe — Data & Analytics\n"
    "Skills: Python, SQL, Excel, basic Tableau\n"
    "Experience: 1 year as a junior analyst at FinCo, built weekly reports, "
    "cleaned datasets using pandas.\n"
    "Education: BSc Computer Science."
)

VALID_SKILL_GAP_JSON: dict = {
    "readiness_score": 72,
    "summary": (
        "John demonstrates solid Python and SQL skills that align well with the "
        "Data Analyst role. The primary gap is deeper Tableau proficiency and "
        "formal cross-functional collaboration experience."
    ),
    "existing_skills": [
        "Python",
        "SQL",
        "Tableau (basic)",
        "pandas",
        "data cleaning",
    ],
    "missing_technical_skills": [
        "Advanced Tableau dashboard development",
        "Statistical modelling",
    ],
    "missing_soft_skills": [
        "Cross-functional collaboration at scale",
        "Executive-level communication of data insights",
    ],
    "recommended_next_steps": [
        "Complete Tableau Desktop Specialist certification and build 2 portfolio dashboards.",
        "Contribute to an open-source data project to demonstrate cross-team collaboration.",
        "Practice explaining analytical findings in non-technical language.",
    ],
}


def _mock_chat_completion(monkeypatch: pytest.MonkeyPatch, return_value: str) -> AsyncMock:
    mock = AsyncMock(return_value=return_value)
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)
    return mock


# ---------------------------------------------------------------------------
# Happy path — valid payload
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyse_skill_gap_returns_valid_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid skill gap JSON is parsed, validated, and returned as SkillGapContent."""
    mock = _mock_chat_completion(monkeypatch, json.dumps(VALID_SKILL_GAP_JSON))

    result = await skill_gap_agent.analyse_skill_gap(
        resume_text=SAMPLE_RESUME,
        jd_text=SAMPLE_JD,
        role_title=SAMPLE_ROLE,
    )

    assert result.readiness_score == 72
    assert 0 <= result.readiness_score <= 100
    assert result.summary
    assert len(result.existing_skills) >= 1
    assert isinstance(result.missing_technical_skills, list)
    assert isinstance(result.missing_soft_skills, list)
    assert len(result.recommended_next_steps) >= 1
    mock.assert_awaited_once()
    call_kwargs = mock.await_args.kwargs
    messages = call_kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert call_kwargs["temperature"] == skill_gap_agent.TEMPERATURE


@pytest.mark.asyncio
async def test_analyse_skill_gap_accepts_optional_enrichment_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The agent accepts resume_review_summary and simulation_metadata without error."""
    _mock_chat_completion(monkeypatch, json.dumps(VALID_SKILL_GAP_JSON))

    result = await skill_gap_agent.analyse_skill_gap(
        resume_text=SAMPLE_RESUME,
        jd_text=SAMPLE_JD,
        role_title=SAMPLE_ROLE,
        resume_review_summary="Strong Python skills, weak on visualisation tools.",
        simulation_metadata='{"tasks_completed": 4, "average_competency_scores_out_of_10": {"communication": 7.5}}',
    )

    assert result.readiness_score == 72


@pytest.mark.asyncio
async def test_analyse_skill_gap_handles_empty_optional_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """None values for optional inputs are handled without error."""
    _mock_chat_completion(monkeypatch, json.dumps(VALID_SKILL_GAP_JSON))

    result = await skill_gap_agent.analyse_skill_gap(
        resume_text=SAMPLE_RESUME,
        jd_text=SAMPLE_JD,
        role_title=SAMPLE_ROLE,
        resume_review_summary=None,
        simulation_metadata=None,
    )

    assert result.readiness_score == 72


@pytest.mark.asyncio
async def test_analyse_skill_gap_extracts_json_from_code_fence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """JSON wrapped in a markdown code fence is handled by the fallback extractor."""
    fenced = f"```json\n{json.dumps(VALID_SKILL_GAP_JSON)}\n```"
    _mock_chat_completion(monkeypatch, fenced)

    result = await skill_gap_agent.analyse_skill_gap(
        resume_text=SAMPLE_RESUME,
        jd_text=SAMPLE_JD,
        role_title=SAMPLE_ROLE,
    )

    assert result.readiness_score == 72


# ---------------------------------------------------------------------------
# Guard: empty inputs raise before any API call
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyse_skill_gap_raises_on_empty_jd_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty JD text raises InvalidSkillGapResponseError without calling the LLM."""
    mock = AsyncMock()
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(skill_gap_agent.InvalidSkillGapResponseError):
        await skill_gap_agent.analyse_skill_gap(
            resume_text=SAMPLE_RESUME,
            jd_text="",
            role_title=SAMPLE_ROLE,
        )

    mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_analyse_skill_gap_raises_on_whitespace_only_jd(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Whitespace-only JD text raises without calling the LLM."""
    mock = AsyncMock()
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(skill_gap_agent.InvalidSkillGapResponseError):
        await skill_gap_agent.analyse_skill_gap(
            resume_text=SAMPLE_RESUME,
            jd_text="   \n\t  ",
            role_title=SAMPLE_ROLE,
        )

    mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_analyse_skill_gap_raises_on_empty_resume_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty resume text raises InvalidSkillGapResponseError without calling the LLM."""
    mock = AsyncMock()
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(skill_gap_agent.InvalidSkillGapResponseError):
        await skill_gap_agent.analyse_skill_gap(
            resume_text="",
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
        )

    mock.assert_not_awaited()


# ---------------------------------------------------------------------------
# JSON parsing errors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyse_skill_gap_raises_on_malformed_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-JSON response raises InvalidSkillGapResponseError."""
    _mock_chat_completion(monkeypatch, "this is not json at all")

    with pytest.raises(skill_gap_agent.InvalidSkillGapResponseError):
        await skill_gap_agent.analyse_skill_gap(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
        )


@pytest.mark.asyncio
async def test_analyse_skill_gap_raises_on_empty_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty response raises InvalidSkillGapResponseError."""
    _mock_chat_completion(monkeypatch, "")

    with pytest.raises(skill_gap_agent.InvalidSkillGapResponseError):
        await skill_gap_agent.analyse_skill_gap(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
        )


# ---------------------------------------------------------------------------
# Schema validation errors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyse_skill_gap_raises_on_out_of_range_readiness_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A readiness_score > 100 fails Pydantic validation."""
    import copy

    bad_payload = copy.deepcopy(VALID_SKILL_GAP_JSON)
    bad_payload["readiness_score"] = 150
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(skill_gap_agent.InvalidSkillGapResponseError):
        await skill_gap_agent.analyse_skill_gap(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
        )


@pytest.mark.asyncio
async def test_analyse_skill_gap_raises_on_negative_readiness_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A negative readiness_score fails Pydantic validation."""
    import copy

    bad_payload = copy.deepcopy(VALID_SKILL_GAP_JSON)
    bad_payload["readiness_score"] = -1
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(skill_gap_agent.InvalidSkillGapResponseError):
        await skill_gap_agent.analyse_skill_gap(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
        )


@pytest.mark.asyncio
async def test_analyse_skill_gap_raises_on_missing_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A payload missing the summary field fails Pydantic validation."""
    import copy

    bad_payload = copy.deepcopy(VALID_SKILL_GAP_JSON)
    del bad_payload["summary"]
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(skill_gap_agent.InvalidSkillGapResponseError):
        await skill_gap_agent.analyse_skill_gap(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
        )


@pytest.mark.asyncio
async def test_analyse_skill_gap_raises_on_missing_existing_skills(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A payload missing existing_skills fails Pydantic validation."""
    import copy

    bad_payload = copy.deepcopy(VALID_SKILL_GAP_JSON)
    del bad_payload["existing_skills"]
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(skill_gap_agent.InvalidSkillGapResponseError):
        await skill_gap_agent.analyse_skill_gap(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
        )


@pytest.mark.asyncio
async def test_analyse_skill_gap_raises_on_missing_recommended_next_steps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A payload missing recommended_next_steps fails Pydantic validation."""
    import copy

    bad_payload = copy.deepcopy(VALID_SKILL_GAP_JSON)
    del bad_payload["recommended_next_steps"]
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(skill_gap_agent.InvalidSkillGapResponseError):
        await skill_gap_agent.analyse_skill_gap(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
        )


@pytest.mark.asyncio
async def test_analyse_skill_gap_allows_empty_missing_skills_lists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty missing_technical_skills and missing_soft_skills are valid (no gaps)."""
    import copy

    payload = copy.deepcopy(VALID_SKILL_GAP_JSON)
    payload["missing_technical_skills"] = []
    payload["missing_soft_skills"] = []
    _mock_chat_completion(monkeypatch, json.dumps(payload))

    result = await skill_gap_agent.analyse_skill_gap(
        resume_text=SAMPLE_RESUME,
        jd_text=SAMPLE_JD,
        role_title=SAMPLE_ROLE,
    )

    assert result.missing_technical_skills == []
    assert result.missing_soft_skills == []


# ---------------------------------------------------------------------------
# Boundary: readiness score 0 and 100 are valid
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyse_skill_gap_accepts_score_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A readiness_score of 0 is a valid boundary value."""
    import copy

    payload = copy.deepcopy(VALID_SKILL_GAP_JSON)
    payload["readiness_score"] = 0
    _mock_chat_completion(monkeypatch, json.dumps(payload))

    result = await skill_gap_agent.analyse_skill_gap(
        resume_text=SAMPLE_RESUME,
        jd_text=SAMPLE_JD,
        role_title=SAMPLE_ROLE,
    )

    assert result.readiness_score == 0


@pytest.mark.asyncio
async def test_analyse_skill_gap_accepts_score_100(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A readiness_score of 100 is a valid boundary value."""
    import copy

    payload = copy.deepcopy(VALID_SKILL_GAP_JSON)
    payload["readiness_score"] = 100
    _mock_chat_completion(monkeypatch, json.dumps(payload))

    result = await skill_gap_agent.analyse_skill_gap(
        resume_text=SAMPLE_RESUME,
        jd_text=SAMPLE_JD,
        role_title=SAMPLE_ROLE,
    )

    assert result.readiness_score == 100


# ---------------------------------------------------------------------------
# Error wrapping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyse_skill_gap_raises_timeout_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenRouterTimeoutError is wrapped as SkillGapAgentTimeoutError."""
    mock = AsyncMock(side_effect=OpenRouterTimeoutError("timeout"))
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(skill_gap_agent.SkillGapAgentTimeoutError):
        await skill_gap_agent.analyse_skill_gap(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
        )


@pytest.mark.asyncio
async def test_analyse_skill_gap_raises_llm_request_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenRouterServerError is wrapped as LLMRequestError."""
    mock = AsyncMock(side_effect=OpenRouterServerError("server error"))
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(skill_gap_agent.LLMRequestError):
        await skill_gap_agent.analyse_skill_gap(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
        )
