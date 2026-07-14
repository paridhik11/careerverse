"""Unit tests for the Learning Roadmap Agent (OpenRouter is always mocked).

These tests verify:
- Valid JSON is parsed and validated correctly into RoadmapContent.
- JSON wrapped in a markdown code fence is handled by the fallback extractor.
- Empty JD text raises InvalidLearningPlanResponseError before any API call.
- Empty resume text raises InvalidLearningPlanResponseError before any API call.
- Empty skill gap summary raises InvalidLearningPlanResponseError before API call.
- Malformed JSON raises InvalidLearningPlanResponseError.
- Schema violations (missing month_1, missing focus field) raise
  InvalidLearningPlanResponseError.
- OpenRouterTimeoutError is wrapped as LearningPlanAgentTimeoutError.
- OpenRouterServerError is wrapped as LLMRequestError.
- The messages list and temperature are passed to the OpenRouter client correctly.
- All three months are present and have the correct structure.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from app.agents import learning_plan as learning_plan_agent
from app.services.openrouter_client import OpenRouterServerError, OpenRouterTimeoutError

# ---------------------------------------------------------------------------
# Sample inputs
# ---------------------------------------------------------------------------

SAMPLE_ROLE = "Data Engineer"
SAMPLE_JD = (
    "We are looking for a Data Engineer proficient in Python, SQL, Apache Spark, "
    "and cloud platforms (AWS or GCP). The role requires strong problem-solving, "
    "communication with cross-functional teams, and experience designing ETL "
    "pipelines, data warehousing (Redshift or BigQuery), and Airflow orchestration."
)
SAMPLE_RESUME = (
    "Jane Smith — Software Developer\n"
    "Skills: Python, SQL, basic AWS (S3, EC2), pandas\n"
    "Experience: 2 years as a backend developer at TechCo, built REST APIs, "
    "wrote SQL queries, used pandas for data transformation.\n"
    "Education: BSc Computer Science."
)
SAMPLE_SKILL_GAP = json.dumps(
    {
        "role_title": "Data Engineer",
        "readiness_score": 48,
        "skill_gap_summary": (
            "Jane has solid Python and SQL skills that partially align with "
            "the Data Engineer role. The primary gaps are Apache Spark, "
            "Airflow, and BigQuery/Redshift experience."
        ),
        "existing_skills": ["Python", "SQL", "AWS (basic)", "pandas"],
        "missing_technical_skills": ["Apache Spark", "Airflow", "BigQuery", "ETL pipeline design"],
        "missing_soft_skills": ["Cross-functional data communication"],
        "recommended_next_steps": [
            "Complete a Spark + PySpark hands-on course and build a batch pipeline.",
            "Set up Airflow locally and orchestrate a multi-step ETL workflow.",
            "Complete the BigQuery Fundamentals course on Google Cloud Skills Boost.",
        ],
    }
)

VALID_ROADMAP_JSON: dict = {
    "month_1": {
        "focus": "Build Apache Spark and ETL pipeline foundations required by the Data Engineer JD.",
        "topics": [
            "PySpark fundamentals (RDDs, DataFrames, transformations, actions)",
            "ETL pipeline design patterns",
            "AWS S3 as a data lake layer",
            "SQL window functions and query optimisation",
        ],
        "projects": [
            "Build a PySpark batch pipeline that reads a CSV from S3, transforms it, "
            "and writes Parquet output back to S3."
        ],
        "resources": [
            "Apache Spark Documentation — spark.apache.org/docs/latest",
            "Learning Spark (O'Reilly, free preview) — learningspark.io",
            "AWS S3 Developer Guide — docs.aws.amazon.com/s3",
        ],
        "milestones": [
            "Can write a PySpark DataFrame transformation without reference material.",
            "Can explain the difference between narrow and wide transformations.",
        ],
    },
    "month_2": {
        "focus": "Deepen ETL competency and introduce Airflow orchestration and BigQuery.",
        "topics": [
            "Apache Airflow DAG design and scheduling",
            "BigQuery fundamentals (tables, partitioning, cost management)",
            "Data warehouse schema design (star schema, slowly changing dimensions)",
            "Spark performance tuning (partitioning, caching)",
        ],
        "projects": [
            "Build an Airflow DAG that orchestrates a multi-step Spark pipeline "
            "with error handling and retries.",
            "Load processed data from the Month 1 project into a BigQuery dataset.",
        ],
        "resources": [
            "Apache Airflow Documentation — airflow.apache.org/docs",
            "Google Cloud Skills Boost — BigQuery Fundamentals (free)",
            "Data Engineering Zoomcamp — github.com/DataTalksClub/data-engineering-zoomcamp",
        ],
        "milestones": [
            "Can build and deploy an Airflow DAG with at least three dependent tasks.",
            "Can query and explain a BigQuery partitioned table cost-effectively.",
        ],
    },
    "month_3": {
        "focus": "Polish portfolio projects, prepare for interviews, and become job-ready.",
        "topics": [
            "End-to-end pipeline documentation and README writing",
            "Data engineering interview patterns (system design, SQL, architecture)",
            "Cross-functional data communication (presenting pipeline decisions to stakeholders)",
            "Cloud cost estimation and optimisation for data pipelines",
        ],
        "projects": [
            "Polish the Month 1 + Month 2 pipeline projects with production-quality "
            "READMEs, architecture diagrams, and GitHub portfolio presentation.",
        ],
        "resources": [
            "Data Engineering Interview Questions — dataengineeringinterview.com",
            "System Design Primer — github.com/donnemartin/system-design-primer",
            "Towards Data Science (Medium) — towardsdatascience.com",
        ],
        "milestones": [
            "Can walk through an end-to-end data pipeline design in a 20-minute technical interview.",
            "Portfolio contains two deployable, documented data engineering projects.",
            "Can answer cross-functional communication scenarios from the JD context.",
        ],
    },
}


def _mock_chat_completion(monkeypatch: pytest.MonkeyPatch, return_value: str) -> AsyncMock:
    mock = AsyncMock(return_value=return_value)
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)
    return mock


# ---------------------------------------------------------------------------
# Happy path — valid payload
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_learning_plan_returns_valid_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid roadmap JSON is parsed, validated, and returned as RoadmapContent."""
    mock = _mock_chat_completion(monkeypatch, json.dumps(VALID_ROADMAP_JSON))

    result = await learning_plan_agent.generate_learning_plan(
        resume_text=SAMPLE_RESUME,
        jd_text=SAMPLE_JD,
        role_title=SAMPLE_ROLE,
        skill_gap_summary=SAMPLE_SKILL_GAP,
    )

    assert result.month_1.focus
    assert len(result.month_1.topics) >= 1
    assert len(result.month_1.projects) >= 1
    assert len(result.month_1.resources) >= 1
    assert len(result.month_1.milestones) >= 1
    assert result.month_2.focus
    assert len(result.month_2.topics) >= 1
    assert result.month_3.focus
    assert len(result.month_3.topics) >= 1
    mock.assert_awaited_once()
    call_kwargs = mock.await_args.kwargs
    messages = call_kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert call_kwargs["temperature"] == learning_plan_agent.TEMPERATURE


@pytest.mark.asyncio
async def test_generate_learning_plan_all_three_months_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All three months are present in the returned RoadmapContent."""
    _mock_chat_completion(monkeypatch, json.dumps(VALID_ROADMAP_JSON))

    result = await learning_plan_agent.generate_learning_plan(
        resume_text=SAMPLE_RESUME,
        jd_text=SAMPLE_JD,
        role_title=SAMPLE_ROLE,
        skill_gap_summary=SAMPLE_SKILL_GAP,
    )

    assert result.month_1 is not None
    assert result.month_2 is not None
    assert result.month_3 is not None


@pytest.mark.asyncio
async def test_generate_learning_plan_extracts_json_from_code_fence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """JSON wrapped in a markdown code fence is extracted by the fallback."""
    fenced = f"```json\n{json.dumps(VALID_ROADMAP_JSON)}\n```"
    _mock_chat_completion(monkeypatch, fenced)

    result = await learning_plan_agent.generate_learning_plan(
        resume_text=SAMPLE_RESUME,
        jd_text=SAMPLE_JD,
        role_title=SAMPLE_ROLE,
        skill_gap_summary=SAMPLE_SKILL_GAP,
    )

    assert result.month_1.focus


# ---------------------------------------------------------------------------
# Guard: empty inputs raise before any API call
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_learning_plan_raises_on_empty_jd_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty JD text raises InvalidLearningPlanResponseError without calling the LLM."""
    mock = AsyncMock()
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(learning_plan_agent.InvalidLearningPlanResponseError):
        await learning_plan_agent.generate_learning_plan(
            resume_text=SAMPLE_RESUME,
            jd_text="",
            role_title=SAMPLE_ROLE,
            skill_gap_summary=SAMPLE_SKILL_GAP,
        )

    mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_generate_learning_plan_raises_on_whitespace_jd(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Whitespace-only JD text raises without calling the LLM."""
    mock = AsyncMock()
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(learning_plan_agent.InvalidLearningPlanResponseError):
        await learning_plan_agent.generate_learning_plan(
            resume_text=SAMPLE_RESUME,
            jd_text="   \n\t  ",
            role_title=SAMPLE_ROLE,
            skill_gap_summary=SAMPLE_SKILL_GAP,
        )

    mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_generate_learning_plan_raises_on_empty_resume(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty resume text raises InvalidLearningPlanResponseError without LLM call."""
    mock = AsyncMock()
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(learning_plan_agent.InvalidLearningPlanResponseError):
        await learning_plan_agent.generate_learning_plan(
            resume_text="",
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
            skill_gap_summary=SAMPLE_SKILL_GAP,
        )

    mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_generate_learning_plan_raises_on_empty_skill_gap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty skill gap summary raises InvalidLearningPlanResponseError."""
    mock = AsyncMock()
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(learning_plan_agent.InvalidLearningPlanResponseError):
        await learning_plan_agent.generate_learning_plan(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
            skill_gap_summary="",
        )

    mock.assert_not_awaited()


# ---------------------------------------------------------------------------
# JSON parsing errors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_learning_plan_raises_on_malformed_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-JSON response raises InvalidLearningPlanResponseError."""
    _mock_chat_completion(monkeypatch, "not valid json")

    with pytest.raises(learning_plan_agent.InvalidLearningPlanResponseError):
        await learning_plan_agent.generate_learning_plan(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
            skill_gap_summary=SAMPLE_SKILL_GAP,
        )


@pytest.mark.asyncio
async def test_generate_learning_plan_raises_on_empty_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty response raises InvalidLearningPlanResponseError."""
    _mock_chat_completion(monkeypatch, "")

    with pytest.raises(learning_plan_agent.InvalidLearningPlanResponseError):
        await learning_plan_agent.generate_learning_plan(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
            skill_gap_summary=SAMPLE_SKILL_GAP,
        )


# ---------------------------------------------------------------------------
# Schema validation errors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_learning_plan_raises_on_missing_month_1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A payload missing month_1 fails Pydantic validation."""
    import copy

    bad_payload = copy.deepcopy(VALID_ROADMAP_JSON)
    del bad_payload["month_1"]
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(learning_plan_agent.InvalidLearningPlanResponseError):
        await learning_plan_agent.generate_learning_plan(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
            skill_gap_summary=SAMPLE_SKILL_GAP,
        )


@pytest.mark.asyncio
async def test_generate_learning_plan_raises_on_missing_focus_in_month(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A month missing the focus field fails Pydantic validation."""
    import copy

    bad_payload = copy.deepcopy(VALID_ROADMAP_JSON)
    del bad_payload["month_2"]["focus"]
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(learning_plan_agent.InvalidLearningPlanResponseError):
        await learning_plan_agent.generate_learning_plan(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
            skill_gap_summary=SAMPLE_SKILL_GAP,
        )


@pytest.mark.asyncio
async def test_generate_learning_plan_raises_on_missing_topics_in_month(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A month missing the topics list fails Pydantic validation."""
    import copy

    bad_payload = copy.deepcopy(VALID_ROADMAP_JSON)
    del bad_payload["month_3"]["topics"]
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(learning_plan_agent.InvalidLearningPlanResponseError):
        await learning_plan_agent.generate_learning_plan(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
            skill_gap_summary=SAMPLE_SKILL_GAP,
        )


@pytest.mark.asyncio
async def test_generate_learning_plan_raises_on_non_list_topics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A month with topics as a string instead of list fails validation."""
    import copy

    bad_payload = copy.deepcopy(VALID_ROADMAP_JSON)
    bad_payload["month_1"]["topics"] = "This should be a list"
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(learning_plan_agent.InvalidLearningPlanResponseError):
        await learning_plan_agent.generate_learning_plan(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
            skill_gap_summary=SAMPLE_SKILL_GAP,
        )


# ---------------------------------------------------------------------------
# Error wrapping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_learning_plan_raises_timeout_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenRouterTimeoutError is wrapped as LearningPlanAgentTimeoutError."""
    mock = AsyncMock(side_effect=OpenRouterTimeoutError("timeout"))
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(learning_plan_agent.LearningPlanAgentTimeoutError):
        await learning_plan_agent.generate_learning_plan(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
            skill_gap_summary=SAMPLE_SKILL_GAP,
        )


@pytest.mark.asyncio
async def test_generate_learning_plan_raises_llm_request_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenRouterServerError is wrapped as LLMRequestError."""
    mock = AsyncMock(side_effect=OpenRouterServerError("server error"))
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(learning_plan_agent.LLMRequestError):
        await learning_plan_agent.generate_learning_plan(
            resume_text=SAMPLE_RESUME,
            jd_text=SAMPLE_JD,
            role_title=SAMPLE_ROLE,
            skill_gap_summary=SAMPLE_SKILL_GAP,
        )


# ---------------------------------------------------------------------------
# Saved roadmap matches what was generated
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_learning_plan_month1_focus_matches_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Month 1 focus from the parsed result matches the payload exactly."""
    _mock_chat_completion(monkeypatch, json.dumps(VALID_ROADMAP_JSON))

    result = await learning_plan_agent.generate_learning_plan(
        resume_text=SAMPLE_RESUME,
        jd_text=SAMPLE_JD,
        role_title=SAMPLE_ROLE,
        skill_gap_summary=SAMPLE_SKILL_GAP,
    )

    assert result.month_1.focus == VALID_ROADMAP_JSON["month_1"]["focus"]
    assert result.month_2.focus == VALID_ROADMAP_JSON["month_2"]["focus"]
    assert result.month_3.focus == VALID_ROADMAP_JSON["month_3"]["focus"]
