"""AI Job Simulation Agent.

Generates a realistic first-day workplace simulation for a single career
match by sending the full `JobDescription.parsed_text` to Gemini and
validating the response against `SimulationContent`.

Per `.cursorrules`, this is the only module that calls Gemini for
simulation generation. Routes and services stay thin and never touch the
Gemini SDK directly. The simulation is grounded exclusively in the uploaded
Job Description — no generic role templates, no hallucinated responsibilities.

Responsibilities:
    - Accept a `role_title` and the full `jd_text` (the matched JD's
      `parsed_text`) as input.
    - Call Gemini with the Simulation Agent prompt.
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

import httpx
from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from app.core.config import settings
from app.models.job_simulation import SimulationContent
from app.prompts.simulation_agent import (
    SIMULATION_AGENT_SYSTEM_PROMPT,
    build_simulation_agent_user_prompt,
)

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-2.5-flash"
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


class GeminiRequestError(SimulationAgentError):
    """The Gemini API call itself failed (connection, auth, rate limit, server error)."""


class SimulationAgentTimeoutError(SimulationAgentError):
    """The Gemini API call did not complete within `REQUEST_TIMEOUT_SECONDS`."""


class InvalidSimulationResponseError(SimulationAgentError):
    """Gemini's response could not be parsed or validated into `SimulationContent`."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_client() -> genai.Client:
    """Build a Gemini client from settings.

    Constructed at call time (not module level) so tests can monkeypatch
    `settings.gemini_api_key` without reloading the module.
    """
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=int(REQUEST_TIMEOUT_SECONDS * 1000)),
    )


def _extract_json_object(raw_text: str) -> str:
    """Best-effort extraction of a bare JSON object from the model's raw text.

    `response_mime_type="application/json"` should guarantee bare JSON,
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
    """Parse Gemini's raw text into a validated `SimulationContent`.

    Parameters
    ----------
    raw_text:
        The raw string returned by `response.text`.
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

    Sends the role title and full JD text to Gemini and returns a
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
    GeminiRequestError
        The Gemini API call failed (network, authentication, rate limit,
        or server error).
    SimulationAgentTimeoutError
        The Gemini API call did not complete within `REQUEST_TIMEOUT_SECONDS`.
    InvalidSimulationResponseError
        Gemini's response could not be parsed or validated.
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
        response = await client.aio.models.generate_content(
            model=MODEL_NAME,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SIMULATION_AGENT_SYSTEM_PROMPT,
                temperature=TEMPERATURE,
                response_mime_type="application/json",
            ),
        )
    except httpx.TimeoutException as exc:
        raise SimulationAgentTimeoutError(
            f"Simulation Agent timed out generating simulation for role '{role_title}'."
        ) from exc
    except errors.APIError as exc:
        raise GeminiRequestError(
            f"Gemini request failed while generating simulation for role "
            f"'{role_title}': {exc}"
        ) from exc

    raw_text = response.text
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
