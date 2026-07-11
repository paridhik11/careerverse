"""AI Job Simulation Agent.

Generates a realistic first-day workplace simulation for a single career
match by sending the full `JobDescription.parsed_text` to GPT-4o and
validating the response against `SimulationContent`.

Per `.cursorrules`, this is the only module that calls OpenAI for
simulation generation. Routes and services stay thin and never touch the
OpenAI SDK directly. The simulation is grounded exclusively in the uploaded
Job Description — no generic role templates, no hallucinated responsibilities.

Responsibilities:
    - Accept a `role_title` and the full `jd_text` (the matched JD's
      `parsed_text`) as input.
    - Call GPT-4o with the Simulation Agent prompt.
    - Extract and validate the JSON response into `SimulationContent`.
    - Return the validated `SimulationContent` — never raw text.
    - Raise descriptive, typed exceptions on every failure path so the
      service layer can log precisely and the API layer can return the
      right HTTP status code.

This function is designed to be called from `asyncio.gather()` by the
simulation service — three concurrent calls, one per career match.
"""

from __future__ import annotations

import json
import logging
import re

from openai import APIConnectionError, APIError, APITimeoutError, AsyncOpenAI, RateLimitError
from pydantic import ValidationError

from app.core.config import settings
from app.models.job_simulation import SimulationContent
from app.prompts.simulation_agent import (
    SIMULATION_AGENT_SYSTEM_PROMPT,
    build_simulation_agent_user_prompt,
)

logger = logging.getLogger(__name__)

MODEL_NAME = "gpt-4o"
# Simulation generation involves 5–7 decision points with 2–4 options each,
# plus evaluation metadata on every option — this is a large, structured
# response. 90 seconds gives adequate headroom without hanging the request
# pool.
REQUEST_TIMEOUT_SECONDS = 90.0

# Slight creative temperature for varied, realistic scenarios. Lower than
# 1.0 to preserve grounding; higher than career matching (0.3) because
# simulation quality benefits from narrative variety.
TEMPERATURE = 0.7

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)


# ---------------------------------------------------------------------------
# Typed exception hierarchy
# ---------------------------------------------------------------------------


class SimulationAgentError(Exception):
    """Base class for every Simulation Agent failure."""


class OpenAIRequestError(SimulationAgentError):
    """The OpenAI API call itself failed (connection, auth, rate limit, server error)."""


class SimulationAgentTimeoutError(SimulationAgentError):
    """The OpenAI API call did not complete within `REQUEST_TIMEOUT_SECONDS`."""


class InvalidSimulationResponseError(SimulationAgentError):
    """GPT-4o's response could not be parsed or validated into `SimulationContent`."""


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
    a markdown code fence or adds stray commentary anyway — matching the
    pattern used in `app.agents.career_advisor`.
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


def _parse_and_validate(raw_text: str, role_title: str) -> SimulationContent:
    """Parse GPT-4o's raw text into a validated `SimulationContent`.

    Parameters
    ----------
    raw_text:
        The raw string returned by `response.choices[0].message.content`.
    role_title:
        Included in error messages for debuggability in concurrent runs.

    Returns
    -------
    SimulationContent
        Fully validated simulation content.

    Raises
    ------
    InvalidSimulationResponseError
        If JSON parsing or Pydantic validation fails for any reason.
    """
    candidate = _extract_json_object(raw_text)

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise InvalidSimulationResponseError(
            f"Simulation Agent for role '{role_title}' returned malformed JSON: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise InvalidSimulationResponseError(
            f"Simulation Agent for role '{role_title}' returned valid JSON but not a "
            f"JSON object — got {type(payload).__name__}."
        )

    try:
        return SimulationContent.model_validate(payload)
    except ValidationError as exc:
        raise InvalidSimulationResponseError(
            f"Simulation Agent for role '{role_title}' response failed schema "
            f"validation: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


async def generate_simulation(role_title: str, jd_text: str) -> SimulationContent:
    """Run the Simulation Agent for one career match.

    Sends the role title and full JD text to GPT-4o and returns a
    fully validated `SimulationContent`. Designed to be awaited inside
    `asyncio.gather()` in the simulation service for concurrent generation
    of all three simulations.

    Parameters
    ----------
    role_title:
        The role title from the matched `JobMatch` record.
    jd_text:
        The full `JobDescription.parsed_text` for this career match — the
        ONLY source of truth for simulation scenarios.

    Returns
    -------
    SimulationContent
        4–6 independent workplace tasks grounded in the uploaded JD.

    Raises
    ------
    OpenAIRequestError
        The OpenAI API call failed (network, authentication, rate limit,
        or server error).
    SimulationAgentTimeoutError
        The OpenAI API call did not complete within `REQUEST_TIMEOUT_SECONDS`.
    InvalidSimulationResponseError
        GPT-4o's response could not be parsed or validated.
    """
    if not jd_text or not jd_text.strip():
        raise InvalidSimulationResponseError(
            f"Cannot generate a simulation for role '{role_title}': "
            f"the Job Description text is empty."
        )

    client = _get_client()
    user_prompt = build_simulation_agent_user_prompt(role_title, jd_text)

    logger.info("Simulation Agent starting generation for role: '%s'.", role_title)

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SIMULATION_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
    except APITimeoutError as exc:
        raise SimulationAgentTimeoutError(
            f"Simulation Agent timed out generating simulation for role '{role_title}'."
        ) from exc
    except (APIConnectionError, RateLimitError, APIError) as exc:
        raise OpenAIRequestError(
            f"OpenAI request failed while generating simulation for role "
            f"'{role_title}': {exc}"
        ) from exc

    raw_text = response.choices[0].message.content if response.choices else None
    if not raw_text:
        raise InvalidSimulationResponseError(
            f"Simulation Agent returned an empty response for role '{role_title}'."
        )

    simulation = _parse_and_validate(raw_text, role_title)

    logger.info(
        "Simulation Agent completed generation for role '%s': %d tasks.",
        role_title,
        len(simulation.tasks),
    )

    return simulation
