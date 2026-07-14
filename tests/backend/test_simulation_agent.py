"""Unit tests for the AI Job Simulation Agent (OpenRouter is always mocked).

These tests verify:
- Valid VWE JSON is parsed and validated correctly.
- JSON wrapped in a code fence is handled by the fallback extractor.
- An empty JD text raises `InvalidSimulationResponseError` before any API call.
- Malformed JSON raises `InvalidSimulationResponseError`.
- Schema violations (too few tasks, missing fields, out-of-range scores) raise
  `InvalidSimulationResponseError`.
- `OpenRouterTimeoutError` is wrapped as `SimulationAgentTimeoutError`.
- `OpenRouterServerError` is wrapped as `LLMRequestError`.
- The messages list and temperature are passed to the OpenRouter client correctly.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from app.agents import simulation_agent
from app.services.openrouter_client import OpenRouterServerError, OpenRouterTimeoutError

# ---------------------------------------------------------------------------
# Sample valid VWE payload
# ---------------------------------------------------------------------------

SAMPLE_ROLE_TITLE = "Software Engineer"
SAMPLE_JD_TEXT = (
    "We are looking for a Software Engineer to design and build RESTful APIs, "
    "review pull requests, write unit tests, and collaborate with the product team "
    "to define technical requirements for new features."
)

VALID_SIMULATION_JSON: dict = {
    "job_title": "Software Engineer",
    "estimated_duration": "30-45 mins",
    "difficulty": "Intermediate",
    "overview": {
        "company_context": "A fast-growing fintech startup building payment infrastructure.",
        "team_context": "A cross-functional squad of 6 engineers, 1 PM, and 1 designer.",
        "your_role": "You design and build RESTful APIs and review pull requests.",
        "project_background": "A new payments API that needs to launch in two weeks.",
    },
    "what_youll_learn": [
        "How to review a pull request for correctness and security",
        "How to prioritise technical debt vs. feature work",
        "How to communicate a breaking change to stakeholders",
    ],
    "what_youll_do": [
        "Review a pull request diff",
        "Prioritise API tasks for the sprint",
        "Draft a stakeholder email about a breaking change",
        "Investigate a failing unit test",
    ],
    "tasks": [
        {
            "task_number": 1,
            "title": "Review Pull Request Diff",
            "estimated_time": "5-10 mins",
            "difficulty": "Easy",
            "objective": "Identify issues in a submitted pull request.",
            "context": "A teammate has submitted a PR for the new payments endpoint.",
            "resources": [
                {
                    "type": "Pull Request Diff",
                    "content": "+ def process_payment(amount, user_id):\n+     result = db.execute(f'SELECT * FROM payments WHERE user={user_id}')\n+     return result",
                }
            ],
            "activity": {
                "type": "multiple_choice",
                "question": "What is the most critical issue in this pull request?",
                "options": [
                    "A) The function name is too generic",
                    "B) The SQL query is vulnerable to SQL injection",
                    "C) The function does not return a status code",
                    "D) There is no docstring",
                ],
            },
            "expected_solution": "B) The SQL query is vulnerable to SQL injection.",
            "feedback": {
                "positive": "Identifying SQL injection shows you understand secure coding practices.",
                "improvement": "Also flag missing input validation and the absence of unit tests.",
                "real_world_importance": "SQL injection is one of the most common production vulnerabilities.",
            },
            "evaluation": {
                "communication": 7,
                "problem_solving": 8,
                "technical_judgment": 9,
                "collaboration": 6,
                "leadership": 5,
                "adaptability": 6,
            },
            "jd_reference": "review pull requests",
        },
        {
            "task_number": 2,
            "title": "Prioritise Sprint Backlog",
            "estimated_time": "5-10 mins",
            "difficulty": "Intermediate",
            "objective": "Rank the backlog items by business and technical priority.",
            "context": "Sprint planning is tomorrow.",
            "resources": [],
            "activity": {
                "type": "prioritize",
                "question": "Rank these tasks from highest to lowest priority:",
                "options": [
                    "Add rate limiting to the payments endpoint",
                    "Fix the authentication bug blocking QA",
                ],
            },
            "expected_solution": "Fix the authentication bug → Add rate limiting.",
            "feedback": {
                "positive": "Prioritising the QA blocker first shows team awareness.",
                "improvement": "Consider the effort-to-impact ratio.",
                "real_world_importance": "Effective backlog prioritisation directly affects team velocity.",
            },
            "evaluation": {
                "communication": 6,
                "problem_solving": 8,
                "technical_judgment": 7,
                "collaboration": 8,
                "leadership": 7,
                "adaptability": 7,
            },
            "jd_reference": "collaborate with the product team to define technical requirements",
        },
        {
            "task_number": 3,
            "title": "Draft Stakeholder Email",
            "estimated_time": "10 mins",
            "difficulty": "Intermediate",
            "objective": "Communicate a breaking API change to downstream teams.",
            "context": "You are deprecating the v1 payments endpoint.",
            "resources": [],
            "activity": {
                "type": "email",
                "question": "Write a brief email explaining the breaking change.",
                "options": [],
            },
            "expected_solution": "Subject: Action Required — v1 /payments endpoint deprecation.",
            "feedback": {
                "positive": "Clear subject lines reduce back-and-forth.",
                "improvement": "Always include a point of contact.",
                "real_world_importance": "Poor communication of breaking changes causes outages.",
            },
            "evaluation": {
                "communication": 9,
                "problem_solving": 6,
                "technical_judgment": 7,
                "collaboration": 8,
                "leadership": 7,
                "adaptability": 6,
            },
            "jd_reference": "collaborate with the product team to define technical requirements",
        },
        {
            "task_number": 4,
            "title": "Investigate Failing Unit Test",
            "estimated_time": "10-15 mins",
            "difficulty": "Hard",
            "objective": "Diagnose why a unit test is failing and propose a fix.",
            "context": "CI has been red for two hours.",
            "resources": [
                {
                    "type": "CI Log",
                    "content": "FAILED tests/test_payments.py::test_process_payment_returns_201\nAssertionError: assert 500 == 201",
                }
            ],
            "activity": {
                "type": "bug_analysis",
                "question": "What is the root cause and minimal fix?",
                "options": [],
            },
            "expected_solution": "Root cause: missing user_id in test payload.",
            "feedback": {
                "positive": "Reading the traceback before guessing is the right approach.",
                "improvement": "Add input schema validation at the API boundary.",
                "real_world_importance": "A red CI pipeline blocks the entire team.",
            },
            "evaluation": {
                "communication": 6,
                "problem_solving": 9,
                "technical_judgment": 9,
                "collaboration": 5,
                "leadership": 6,
                "adaptability": 8,
            },
            "jd_reference": "design and build RESTful APIs",
        },
    ],
}


def _mock_chat_completion(monkeypatch: pytest.MonkeyPatch, return_value: str) -> AsyncMock:
    mock = AsyncMock(return_value=return_value)
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)
    return mock


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_simulation_returns_valid_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid VWE JSON is parsed, validated, and returned as SimulationContent."""
    mock = _mock_chat_completion(monkeypatch, json.dumps(VALID_SIMULATION_JSON))

    result = await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)

    assert result.job_title == "Software Engineer"
    assert result.estimated_duration == "30-45 mins"
    assert result.difficulty == "Intermediate"
    assert len(result.tasks) == 4
    assert result.tasks[0].task_number == 1
    assert result.tasks[0].jd_reference == "review pull requests"
    for task in result.tasks:
        ev = task.evaluation
        for score in [
            ev.communication,
            ev.problem_solving,
            ev.technical_judgment,
            ev.collaboration,
            ev.leadership,
            ev.adaptability,
        ]:
            assert 0 <= score <= 10
    mock.assert_awaited_once()
    call_kwargs = mock.await_args.kwargs
    messages = call_kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert call_kwargs["temperature"] == simulation_agent.TEMPERATURE


@pytest.mark.asyncio
async def test_generate_simulation_returns_overview_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Overview fields are populated and the VWE metadata is present."""
    _mock_chat_completion(monkeypatch, json.dumps(VALID_SIMULATION_JSON))

    result = await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)

    assert result.overview.company_context
    assert result.overview.team_context
    assert result.overview.your_role
    assert result.overview.project_background
    assert len(result.what_youll_learn) >= 3
    assert len(result.what_youll_do) >= 3


@pytest.mark.asyncio
async def test_generate_simulation_task_feedback_fields_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every task's feedback block contains all three required fields."""
    _mock_chat_completion(monkeypatch, json.dumps(VALID_SIMULATION_JSON))

    result = await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)

    for task in result.tasks:
        assert task.feedback.positive
        assert task.feedback.improvement
        assert task.feedback.real_world_importance


@pytest.mark.asyncio
async def test_generate_simulation_extracts_json_from_code_fence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """JSON wrapped in a markdown code fence is handled by the fallback extractor."""
    fenced = f"```json\n{json.dumps(VALID_SIMULATION_JSON)}\n```"
    _mock_chat_completion(monkeypatch, fenced)

    result = await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)

    assert len(result.tasks) == 4


# ---------------------------------------------------------------------------
# Guard: empty JD raises before any API call
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_simulation_raises_on_empty_jd_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty JD text raises InvalidSimulationResponseError without calling the LLM."""
    mock = AsyncMock()
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(simulation_agent.InvalidSimulationResponseError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, "")

    mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_generate_simulation_raises_on_whitespace_only_jd(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Whitespace-only JD text is treated the same as empty."""
    mock = AsyncMock()
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(simulation_agent.InvalidSimulationResponseError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, "   \n\t  ")

    mock.assert_not_awaited()


# ---------------------------------------------------------------------------
# JSON parsing errors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_simulation_raises_on_malformed_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-JSON response raises InvalidSimulationResponseError."""
    _mock_chat_completion(monkeypatch, "this is not json at all")

    with pytest.raises(simulation_agent.InvalidSimulationResponseError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)


@pytest.mark.asyncio
async def test_generate_simulation_raises_on_empty_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty response content raises InvalidSimulationResponseError."""
    _mock_chat_completion(monkeypatch, "")

    with pytest.raises(simulation_agent.InvalidSimulationResponseError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)


# ---------------------------------------------------------------------------
# Schema validation errors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_simulation_raises_on_too_few_tasks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A payload with fewer than 4 tasks fails Pydantic validation."""
    bad_payload = dict(VALID_SIMULATION_JSON)
    bad_payload["tasks"] = VALID_SIMULATION_JSON["tasks"][:3]
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(simulation_agent.InvalidSimulationResponseError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)


@pytest.mark.asyncio
async def test_generate_simulation_raises_on_too_many_tasks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A payload with more than 6 tasks fails Pydantic validation."""
    extra_task = dict(VALID_SIMULATION_JSON["tasks"][0])
    extra_task["task_number"] = 7
    bad_payload = dict(VALID_SIMULATION_JSON)
    bad_payload["tasks"] = VALID_SIMULATION_JSON["tasks"] + [extra_task] * 3
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(simulation_agent.InvalidSimulationResponseError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)


@pytest.mark.asyncio
async def test_generate_simulation_raises_on_out_of_range_eval_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An evaluation score outside 0-10 fails Pydantic validation."""
    import copy

    bad_payload = copy.deepcopy(VALID_SIMULATION_JSON)
    bad_payload["tasks"][0]["evaluation"]["problem_solving"] = 11
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(simulation_agent.InvalidSimulationResponseError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)


@pytest.mark.asyncio
async def test_generate_simulation_raises_on_missing_jd_reference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A task with a missing jd_reference fails Pydantic validation."""
    import copy

    bad_payload = copy.deepcopy(VALID_SIMULATION_JSON)
    del bad_payload["tasks"][0]["jd_reference"]
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(simulation_agent.InvalidSimulationResponseError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)


@pytest.mark.asyncio
async def test_generate_simulation_raises_on_missing_overview(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A payload missing the overview block fails Pydantic validation."""
    import copy

    bad_payload = copy.deepcopy(VALID_SIMULATION_JSON)
    del bad_payload["overview"]
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(simulation_agent.InvalidSimulationResponseError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)


@pytest.mark.asyncio
async def test_generate_simulation_raises_on_too_few_learning_outcomes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fewer than 3 items in what_youll_learn fails Pydantic validation."""
    import copy

    bad_payload = copy.deepcopy(VALID_SIMULATION_JSON)
    bad_payload["what_youll_learn"] = ["Only one outcome"]
    _mock_chat_completion(monkeypatch, json.dumps(bad_payload))

    with pytest.raises(simulation_agent.InvalidSimulationResponseError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)


# ---------------------------------------------------------------------------
# Error wrapping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_simulation_raises_timeout_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenRouterTimeoutError is wrapped as SimulationAgentTimeoutError."""
    mock = AsyncMock(side_effect=OpenRouterTimeoutError("timeout"))
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(simulation_agent.SimulationAgentTimeoutError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)


@pytest.mark.asyncio
async def test_generate_simulation_raises_llm_request_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenRouterServerError is wrapped as LLMRequestError."""
    mock = AsyncMock(side_effect=OpenRouterServerError("server error"))
    monkeypatch.setattr("app.services.openrouter_client.chat_completion", mock)

    with pytest.raises(simulation_agent.LLMRequestError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)
