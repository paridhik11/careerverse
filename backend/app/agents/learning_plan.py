"""AI Learning Roadmap Agent.

Generates a personalised 3-Month Learning Roadmap for the user's chosen career
by calling GPT-4o with the selected Job Description, Skill Gap Analysis, and
resume text.

Per `.cursorrules`, this is the only module that calls OpenAI for roadmap
generation. Routes and services stay thin and never touch the OpenAI SDK
directly.

The roadmap is grounded exclusively in:
- The uploaded Job Description (primary source of truth for role requirements).
- The Skill Gap Analysis (drives the month-by-month topic progression).
- The candidate's resume (context on existing competencies).

Only one career is ever processed (the chosen `JobMatch`). The agent is NEVER
run against the other two recommendations.

Responsibilities:
    - Accept resume text, JD text, role title, and skill gap summary.
    - Call GPT-4o with the Learning Plan prompt (system + user).
    - Extract and validate the JSON response into `RoadmapContent`.
    - Return the validated `RoadmapContent` — never raw text.
    - Raise descriptive, typed exceptions on every failure path so the
      service layer can log precisely and the API layer can return the
      correct HTTP status code.
"""

from __future__ import annotations

import json
import logging
import re

from openai import APIConnectionError, APIError, APITimeoutError, AsyncOpenAI, RateLimitError
from pydantic import ValidationError

from app.core.config import settings
from app.models.learning_roadmap import RoadmapContent
from app.prompts.learning_plan import (
    LEARNING_PLAN_SYSTEM_PROMPT,
    build_learning_plan_user_prompt,
)

logger = logging.getLogger(__name__)

MODEL_NAME = "gpt-4o"

# Roadmap generation is analytical but benefits from slight creative variety
# in resource and project suggestions — 0.4 balances precision with diversity.
TEMPERATURE = 0.4

# The roadmap response is moderately sized JSON; 90 s covers long JD + resume
# inputs without unnecessary timeout risk.
REQUEST_TIMEOUT_SECONDS = 90.0

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)


# ---------------------------------------------------------------------------
# Typed exception hierarchy
# ---------------------------------------------------------------------------


class LearningPlanAgentError(Exception):
    """Base class for every Learning Roadmap Agent failure."""


class OpenAIRequestError(LearningPlanAgentError):
    """The OpenAI API call itself failed (connection, auth, rate limit, server error)."""


class LearningPlanAgentTimeoutError(LearningPlanAgentError):
    """The OpenAI API call did not complete within `REQUEST_TIMEOUT_SECONDS`."""


class InvalidLearningPlanResponseError(LearningPlanAgentError):
    """GPT-4o's response could not be parsed or validated into `RoadmapContent`."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_client() -> AsyncOpenAI:
    """Build an AsyncOpenAI client from settings.

    Constructed at call time (not module level) so tests can monkeypatch
    `settings.openai_api_key` without reloading the module.
    """
    return AsyncOpenAI(api_key=settings.openai_api_key, timeout=REQUEST_TIMEOUT_SECONDS)


def _extract_json_object(raw_text: str) -> str:
    """Best-effort extraction of a bare JSON object from the model's raw text.

    `response_format={"type": "json_object"}` should guarantee bare JSON,
    but this guard handles the rare case where the model wraps its output in
    a markdown code fence or adds stray commentary — matching the pattern
    used in `app.agents.skill_gap` and `app.agents.career_advisor`.
    """
    stripped = raw_text.strip()

    fenced = _JSON_FENCE_RE.search(stripped)
    if fenced:
        return fenced.group(1)

    first_brace = stripped.find("{")
    last_brace = stripped.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return stripped[first_brace : last_brace + 1]

    return stripped


def _parse_and_validate(raw_text: str) -> RoadmapContent:
    """Parse GPT-4o's raw text into a validated `RoadmapContent`.

    Parameters
    ----------
    raw_text:
        The raw string returned by `response.choices[0].message.content`.

    Returns
    -------
    RoadmapContent
        Fully validated 3-month learning roadmap.

    Raises
    ------
    InvalidLearningPlanResponseError
        If JSON parsing or Pydantic validation fails for any reason.
    """
    candidate = _extract_json_object(raw_text)

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise InvalidLearningPlanResponseError(
            f"Learning Roadmap Agent returned malformed JSON: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise InvalidLearningPlanResponseError(
            f"Learning Roadmap Agent returned valid JSON but not a JSON object — "
            f"got {type(payload).__name__}."
        )

    try:
        return RoadmapContent.model_validate(payload)
    except ValidationError as exc:
        raise InvalidLearningPlanResponseError(
            f"Learning Roadmap Agent response failed schema validation: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


async def generate_learning_plan(
    resume_text: str,
    jd_text: str,
    role_title: str,
    skill_gap_summary: str,
) -> RoadmapContent:
    """Run the Learning Roadmap Agent for the user's chosen career.

    Sends the resume, Job Description, role title, and Skill Gap Analysis
    to GPT-4o and returns a fully validated `RoadmapContent` with all three
    months of the personalised learning plan.

    The JD is the primary source of truth for role requirements. The Skill Gap
    Analysis drives the month-by-month progression. Only the chosen career's
    data is supplied; the agent is unaware of the other two recommendations.

    Parameters
    ----------
    resume_text:
        Full parsed text of the candidate's resume.
    jd_text:
        Full parsed text of the selected Job Description. This is the ONLY
        source of truth for required skills and role expectations.
    role_title:
        The role title from the chosen `JobMatch` record.
    skill_gap_summary:
        JSON-serialised summary of the Skill Gap Analysis. Drives the
        month-by-month topic and project selection.

    Returns
    -------
    RoadmapContent
        Fully validated 3-month roadmap with focus, topics, projects,
        resources, and milestones for each month.

    Raises
    ------
    InvalidLearningPlanResponseError
        If required inputs are empty, or if GPT-4o's response cannot be
        parsed or validated.
    OpenAIRequestError
        The OpenAI API call failed (network, authentication, rate limit,
        or server error).
    LearningPlanAgentTimeoutError
        The OpenAI API call did not complete within `REQUEST_TIMEOUT_SECONDS`.
    """
    if not jd_text or not jd_text.strip():
        raise InvalidLearningPlanResponseError(
            f"Cannot generate learning roadmap for role '{role_title}': "
            f"the Job Description text is empty."
        )

    if not resume_text or not resume_text.strip():
        raise InvalidLearningPlanResponseError(
            f"Cannot generate learning roadmap for role '{role_title}': "
            f"the resume text is empty."
        )

    if not skill_gap_summary or not skill_gap_summary.strip():
        raise InvalidLearningPlanResponseError(
            f"Cannot generate learning roadmap for role '{role_title}': "
            f"the skill gap summary is empty."
        )

    client = _get_client()
    user_prompt = build_learning_plan_user_prompt(
        resume_text=resume_text,
        jd_text=jd_text,
        role_title=role_title,
        skill_gap_summary=skill_gap_summary,
    )

    logger.info(
        "Learning Roadmap Agent starting generation for role: '%s'.", role_title
    )

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": LEARNING_PLAN_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
    except APITimeoutError as exc:
        raise LearningPlanAgentTimeoutError(
            f"Learning Roadmap Agent timed out generating plan for role '{role_title}'."
        ) from exc
    except (APIConnectionError, RateLimitError, APIError) as exc:
        raise OpenAIRequestError(
            f"OpenAI request failed during roadmap generation for role "
            f"'{role_title}': {exc}"
        ) from exc

    raw_text = response.choices[0].message.content if response.choices else None
    if not raw_text:
        raise InvalidLearningPlanResponseError(
            f"Learning Roadmap Agent returned an empty response for role '{role_title}'."
        )

    result = _parse_and_validate(raw_text)

    logger.info(
        "Learning Roadmap Agent completed roadmap for role '%s': "
        "%d Month-1 topics, %d Month-2 topics, %d Month-3 topics.",
        role_title,
        len(result.month_1.topics),
        len(result.month_2.topics),
        len(result.month_3.topics),
    )

    return result
