"""AI Skill Gap Analysis Agent.

Compares a candidate's resume against the selected Job Description (and
optionally the VWE performance summary) to produce a structured Skill Gap
Analysis via GPT-4o.

Per `.cursorrules`, this is the only module that calls OpenAI for skill gap
generation. Routes and services stay thin and never touch the OpenAI SDK
directly.

The analysis is grounded exclusively in the uploaded Job Description — the
model is instructed never to report skills that are not present in the JD
text. Only one career is ever analysed (the chosen `JobMatch`). The agent is
NEVER run against the other two recommendations.

Responsibilities:
    - Accept resume text, JD text, role title, and optional enrichment inputs.
    - Call GPT-4o with the Skill Gap prompt (system + user).
    - Extract and validate the JSON response into `SkillGapContent`.
    - Return the validated `SkillGapContent` — never raw text.
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
from app.models.skill_gap import SkillGapContent
from app.prompts.skill_gap import SKILL_GAP_SYSTEM_PROMPT, build_skill_gap_user_prompt

logger = logging.getLogger(__name__)

MODEL_NAME = "gpt-4o"

# Skill gap analysis is analytical — lower temperature produces more
# consistent, calibrated outputs than the Simulation Agent (0.7).
TEMPERATURE = 0.3

# The skill gap response is a relatively compact JSON object, but we allow
# generous headroom because the JD and resume texts can be long.
REQUEST_TIMEOUT_SECONDS = 60.0

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)


# ---------------------------------------------------------------------------
# Typed exception hierarchy
# ---------------------------------------------------------------------------


class SkillGapAgentError(Exception):
    """Base class for every Skill Gap Agent failure."""


class OpenAIRequestError(SkillGapAgentError):
    """The OpenAI API call itself failed (connection, auth, rate limit, server error)."""


class SkillGapAgentTimeoutError(SkillGapAgentError):
    """The OpenAI API call did not complete within `REQUEST_TIMEOUT_SECONDS`."""


class InvalidSkillGapResponseError(SkillGapAgentError):
    """GPT-4o's response could not be parsed or validated into `SkillGapContent`."""


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
    used in `app.agents.simulation_agent` and `app.agents.career_advisor`.
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


def _parse_and_validate(raw_text: str) -> SkillGapContent:
    """Parse GPT-4o's raw text into a validated `SkillGapContent`.

    Parameters
    ----------
    raw_text:
        The raw string returned by `response.choices[0].message.content`.

    Returns
    -------
    SkillGapContent
        Fully validated skill gap analysis.

    Raises
    ------
    InvalidSkillGapResponseError
        If JSON parsing or Pydantic validation fails for any reason.
    """
    candidate = _extract_json_object(raw_text)

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise InvalidSkillGapResponseError(
            f"Skill Gap Agent returned malformed JSON: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise InvalidSkillGapResponseError(
            f"Skill Gap Agent returned valid JSON but not a JSON object — "
            f"got {type(payload).__name__}."
        )

    try:
        return SkillGapContent.model_validate(payload)
    except ValidationError as exc:
        raise InvalidSkillGapResponseError(
            f"Skill Gap Agent response failed schema validation: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


async def analyse_skill_gap(
    resume_text: str,
    jd_text: str,
    role_title: str,
    resume_review_summary: str | None = None,
    simulation_metadata: str | None = None,
) -> SkillGapContent:
    """Run the Skill Gap Agent for the user's chosen career.

    Sends the resume, Job Description, role title, and any optional enrichment
    inputs to GPT-4o and returns a fully validated `SkillGapContent`.

    The JD is the primary source of truth — skills are never reported unless
    they appear in the JD text. Only the chosen career's JD is supplied;
    the agent is unaware of the other two recommendations.

    Parameters
    ----------
    resume_text:
        Full parsed text of the candidate's resume.
    jd_text:
        Full parsed text of the selected Job Description. This is the ONLY
        source of truth for required skills.
    role_title:
        The role title from the chosen `JobMatch` record.
    resume_review_summary:
        Optional pre-analysed resume summary from the Resume Reviewer Agent.
        When provided, it enriches the model's understanding of the
        candidate's strengths and weaknesses without requiring it to re-infer
        everything from raw resume text.
    simulation_metadata:
        Optional VWE performance summary (scores + feedback). When provided,
        the model uses it for the 10 % simulation adjustment to the readiness
        score and to sharpen the recommended next steps.

    Returns
    -------
    SkillGapContent
        Fully validated skill gap analysis with readiness score, summary,
        skills lists, and recommended next steps.

    Raises
    ------
    InvalidSkillGapResponseError
        If the JD text is empty, or if GPT-4o's response cannot be parsed
        or validated.
    OpenAIRequestError
        The OpenAI API call failed (network, authentication, rate limit,
        or server error).
    SkillGapAgentTimeoutError
        The OpenAI API call did not complete within `REQUEST_TIMEOUT_SECONDS`.
    """
    if not jd_text or not jd_text.strip():
        raise InvalidSkillGapResponseError(
            f"Cannot analyse skill gap for role '{role_title}': "
            f"the Job Description text is empty."
        )

    if not resume_text or not resume_text.strip():
        raise InvalidSkillGapResponseError(
            f"Cannot analyse skill gap for role '{role_title}': "
            f"the resume text is empty."
        )

    client = _get_client()
    user_prompt = build_skill_gap_user_prompt(
        resume_text=resume_text,
        jd_text=jd_text,
        role_title=role_title,
        resume_review_summary=resume_review_summary,
        simulation_metadata=simulation_metadata,
    )

    logger.info("Skill Gap Agent starting analysis for role: '%s'.", role_title)

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SKILL_GAP_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
    except APITimeoutError as exc:
        raise SkillGapAgentTimeoutError(
            f"Skill Gap Agent timed out analysing role '{role_title}'."
        ) from exc
    except (APIConnectionError, RateLimitError, APIError) as exc:
        raise OpenAIRequestError(
            f"OpenAI request failed during skill gap analysis for role "
            f"'{role_title}': {exc}"
        ) from exc

    raw_text = response.choices[0].message.content if response.choices else None
    if not raw_text:
        raise InvalidSkillGapResponseError(
            f"Skill Gap Agent returned an empty response for role '{role_title}'."
        )

    result = _parse_and_validate(raw_text)

    logger.info(
        "Skill Gap Agent completed analysis for role '%s': readiness_score=%d, "
        "%d existing skills, %d missing technical, %d missing soft.",
        role_title,
        result.readiness_score,
        len(result.existing_skills),
        len(result.missing_technical_skills),
        len(result.missing_soft_skills),
    )

    return result
