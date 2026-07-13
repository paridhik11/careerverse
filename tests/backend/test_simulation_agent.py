"""Unit tests for the AI Job Simulation Agent (Virtual Work Experience format).

Gemini is always mocked — these tests verify:
- Valid VWE JSON is parsed and validated correctly.
- JSON wrapped in a code fence is handled by the fallback extractor.
- An empty JD text raises `InvalidSimulationResponseError` before any API call.
- Malformed JSON raises `InvalidSimulationResponseError`.
- Schema violations (too few tasks, missing fields, out-of-range scores) raise
  `InvalidSimulationResponseError`.
- `httpx.TimeoutException` is wrapped as `SimulationAgentTimeoutError`.
- `errors.APIError` is wrapped as `GeminiRequestError`.
- The model, temperature, and response_mime_type are passed to the Gemini client
  exactly as specified.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from google.genai import errors

from app.agents import simulation_agent

# ---------------------------------------------------------------------------
# Sample valid VWE payload
# ---------------------------------------------------------------------------

SAMPLE_ROLE_TITLE = "Software Engineer"
SAMPLE_JD_TEXT = (
    "We are looking for a Software Engineer to design and build RESTful APIs, "
    "review pull requests, write unit tests, and collaborate with the product team "
    "to define technical requirements for new features."
)

# Minimal valid payload — 4 tasks (the minimum), each with all required fields.
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
            "context": (
                "A teammate has submitted a PR for the new payments endpoint. "
                "Your tech lead has asked you to review it before it merges."
            ),
            "resources": [
                {
                    "type": "Pull Request Diff",
                    "content": (
                        "+ def process_payment(amount, user_id):\n"
                        "+     result = db.execute(f'SELECT * FROM payments WHERE user={user_id}')\n"
                        "+     return result"
                    ),
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
            "expected_solution": (
                "B) The SQL query is vulnerable to SQL injection. "
                "User input is interpolated directly into the query string."
            ),
            "feedback": {
                "positive": (
                    "Identifying SQL injection shows you understand secure coding practices."
                ),
                "improvement": (
                    "Also flag missing input validation and the absence of unit tests."
                ),
                "real_world_importance": (
                    "SQL injection is one of the most common production vulnerabilities. "
                    "Catching it in code review prevents security incidents."
                ),
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
            "context": (
                "Sprint planning is tomorrow. The PM has asked you to rank the "
                "outstanding API tasks so the team can commit to the right scope."
            ),
            "resources": [],
            "activity": {
                "type": "prioritize",
                "question": "Rank these tasks from highest to lowest priority for the sprint:",
                "options": [
                    "Add rate limiting to the payments endpoint",
                    "Write API documentation",
                    "Fix the authentication bug blocking QA",
                    "Refactor the legacy adapter",
                ],
            },
            "expected_solution": (
                "Fix the authentication bug blocking QA → Add rate limiting → "
                "Write API documentation → Refactor the legacy adapter. "
                "Blockers for other teams take precedence; documentation and refactoring "
                "can ship in the next sprint."
            ),
            "feedback": {
                "positive": "Prioritising the QA blocker first shows team awareness.",
                "improvement": "Consider the effort-to-impact ratio, not just urgency.",
                "real_world_importance": (
                    "Effective backlog prioritisation directly affects team velocity "
                    "and shipping dates."
                ),
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
            "context": (
                "You are deprecating the v1 payments endpoint in favour of v2. "
                "Three teams depend on v1 and need advance notice."
            ),
            "resources": [
                {
                    "type": "Breaking Change Summary",
                    "content": (
                        "v1 /payments endpoint will be removed on 2026-08-01. "
                        "v2 requires an Authorization header and returns JSON instead of XML."
                    ),
                }
            ],
            "activity": {
                "type": "email",
                "question": (
                    "Write a brief email to the dependent teams explaining the breaking change, "
                    "the migration steps, and the deadline."
                ),
                "options": [],
            },
            "expected_solution": (
                "Subject: Action Required — v1 /payments endpoint deprecation on 2026-08-01\n"
                "The email should include: deprecation date, what changes (auth header, JSON response), "
                "migration steps (update Authorization header, parse JSON), and offer to help."
            ),
            "feedback": {
                "positive": "Clear subject lines and a migration checklist reduce back-and-forth.",
                "improvement": "Always include a point of contact and a rollback plan.",
                "real_world_importance": (
                    "Poor communication of breaking changes is a leading cause of production outages."
                ),
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
            "context": (
                "CI has been red for two hours. The failing test is "
                "`test_process_payment_returns_201`. You need to find the root cause."
            ),
            "resources": [
                {
                    "type": "CI Log",
                    "content": (
                        "FAILED tests/test_payments.py::test_process_payment_returns_201\n"
                        "AssertionError: assert 500 == 201\n"
                        "  Where 500 = response.status_code\n"
                        "Traceback: KeyError: 'user_id' at payments.py:42"
                    ),
                }
            ],
            "activity": {
                "type": "bug_analysis",
                "question": (
                    "Based on the CI log, what is the root cause of the failure and "
                    "what is the minimal fix?"
                ),
                "options": [],
            },
            "expected_solution": (
                "Root cause: the test payload is missing the `user_id` key, causing a KeyError "
                "at line 42 which is caught and returned as a 500. "
                "Fix: add input validation that returns 400 for missing required fields, "
                "and update the test to send a complete payload."
            ),
            "feedback": {
                "positive": "Reading the traceback before guessing is the right debugging instinct.",
                "improvement": "Add input schema validation at the API boundary to prevent KeyErrors.",
                "real_world_importance": (
                    "A red CI pipeline blocks the entire team. Fast, accurate diagnosis "
                    "is one of the highest-value skills in a software engineer."
                ),
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


# ---------------------------------------------------------------------------
# Helpers (mirror the pattern in test_career_advisor_agent.py)
# ---------------------------------------------------------------------------


def _fake_response(content: str) -> SimpleNamespace:
    return SimpleNamespace(text=content)


def _install_fake_client(monkeypatch: pytest.MonkeyPatch, generate_mock: AsyncMock) -> None:
    fake_client = SimpleNamespace(
        aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate_mock))
    )
    monkeypatch.setattr(simulation_agent, "_get_client", lambda: fake_client)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_simulation_returns_valid_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid VWE JSON is parsed, validated, and returned as SimulationContent."""
    generate_mock = AsyncMock(return_value=_fake_response(json.dumps(VALID_SIMULATION_JSON)))
    _install_fake_client(monkeypatch, generate_mock)

    result = await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)

    assert result.job_title == "Software Engineer"
    assert result.estimated_duration == "30-45 mins"
    assert result.difficulty == "Intermediate"
    assert len(result.tasks) == 4
    assert result.tasks[0].task_number == 1
    assert result.tasks[0].jd_reference == "review pull requests"
    # Evaluation scores present and in range
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
    # Verify the Gemini client was called with the correct parameters
    generate_mock.assert_awaited_once()
    call_kwargs = generate_mock.await_args.kwargs
    assert call_kwargs["model"] == "gemini-2.5-flash"
    assert isinstance(call_kwargs["contents"], str)
    assert call_kwargs["config"].temperature == simulation_agent.TEMPERATURE
    assert call_kwargs["config"].response_mime_type == "application/json"


@pytest.mark.asyncio
async def test_generate_simulation_returns_overview_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Overview fields are populated and the VWE metadata is present."""
    generate_mock = AsyncMock(return_value=_fake_response(json.dumps(VALID_SIMULATION_JSON)))
    _install_fake_client(monkeypatch, generate_mock)

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
    generate_mock = AsyncMock(return_value=_fake_response(json.dumps(VALID_SIMULATION_JSON)))
    _install_fake_client(monkeypatch, generate_mock)

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
    generate_mock = AsyncMock(return_value=_fake_response(fenced))
    _install_fake_client(monkeypatch, generate_mock)

    result = await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)

    assert len(result.tasks) == 4


# ---------------------------------------------------------------------------
# Guard: empty JD raises before any API call
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_simulation_raises_on_empty_jd_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty JD text raises InvalidSimulationResponseError without calling Gemini."""
    generate_mock = AsyncMock()
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(simulation_agent.InvalidSimulationResponseError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, "")

    generate_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_generate_simulation_raises_on_whitespace_only_jd(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Whitespace-only JD text is treated the same as empty."""
    generate_mock = AsyncMock()
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(simulation_agent.InvalidSimulationResponseError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, "   \n\t  ")

    generate_mock.assert_not_awaited()


# ---------------------------------------------------------------------------
# JSON parsing errors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_simulation_raises_on_malformed_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-JSON response raises InvalidSimulationResponseError."""
    generate_mock = AsyncMock(return_value=_fake_response("this is not json at all"))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(simulation_agent.InvalidSimulationResponseError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)


@pytest.mark.asyncio
async def test_generate_simulation_raises_on_empty_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty response content raises InvalidSimulationResponseError."""
    generate_mock = AsyncMock(return_value=_fake_response(""))
    _install_fake_client(monkeypatch, generate_mock)

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
    bad_payload["tasks"] = VALID_SIMULATION_JSON["tasks"][:3]  # only 3 tasks
    generate_mock = AsyncMock(return_value=_fake_response(json.dumps(bad_payload)))
    _install_fake_client(monkeypatch, generate_mock)

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
    generate_mock = AsyncMock(return_value=_fake_response(json.dumps(bad_payload)))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(simulation_agent.InvalidSimulationResponseError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)


@pytest.mark.asyncio
async def test_generate_simulation_raises_on_out_of_range_eval_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An evaluation score outside 0–10 fails Pydantic validation."""
    import copy

    bad_payload = copy.deepcopy(VALID_SIMULATION_JSON)
    bad_payload["tasks"][0]["evaluation"]["problem_solving"] = 11  # out of range
    generate_mock = AsyncMock(return_value=_fake_response(json.dumps(bad_payload)))
    _install_fake_client(monkeypatch, generate_mock)

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
    generate_mock = AsyncMock(return_value=_fake_response(json.dumps(bad_payload)))
    _install_fake_client(monkeypatch, generate_mock)

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
    generate_mock = AsyncMock(return_value=_fake_response(json.dumps(bad_payload)))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(simulation_agent.InvalidSimulationResponseError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)


@pytest.mark.asyncio
async def test_generate_simulation_raises_on_too_few_learning_outcomes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fewer than 3 items in what_youll_learn fails Pydantic validation."""
    import copy

    bad_payload = copy.deepcopy(VALID_SIMULATION_JSON)
    bad_payload["what_youll_learn"] = ["Only one outcome"]  # min is 3
    generate_mock = AsyncMock(return_value=_fake_response(json.dumps(bad_payload)))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(simulation_agent.InvalidSimulationResponseError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)


# ---------------------------------------------------------------------------
# Gemini error wrapping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_simulation_raises_timeout_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """httpx.TimeoutException is wrapped as SimulationAgentTimeoutError."""
    generate_mock = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(simulation_agent.SimulationAgentTimeoutError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)


@pytest.mark.asyncio
async def test_generate_simulation_raises_gemini_request_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """errors.APIError is wrapped as GeminiRequestError."""
    generate_mock = AsyncMock(side_effect=errors.APIError(500, {"error": {"message": "boom"}}))
    _install_fake_client(monkeypatch, generate_mock)

    with pytest.raises(simulation_agent.GeminiRequestError):
        await simulation_agent.generate_simulation(SAMPLE_ROLE_TITLE, SAMPLE_JD_TEXT)
