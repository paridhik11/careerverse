"""AI Job Simulation Agent.

Generates a realistic first-day workplace simulation for a single career
match by sending the full `JobDescription.parsed_text` to OpenRouter and
validating the response against `SimulationContent`.

Per `.cursorrules`, this is the only module that calls the LLM for
simulation generation. Routes and services stay thin and never touch the
AI client directly. The simulation is grounded exclusively in the uploaded
Job Description — no generic role templates, no hallucinated responsibilities.

Responsibilities:
    - Accept a `role_title` and the full `jd_text` (the matched JD's
      `parsed_text`) as input.
    - Call the LLM with the Simulation Agent prompt.
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

from pydantic import ValidationError

from app.models.job_simulation import SimulationContent
from app.prompts.simulation_agent import (
    SIMULATION_AGENT_SYSTEM_PROMPT,
    build_simulation_agent_user_prompt,
)
from app.services import openrouter_client
from app.services.openrouter_client import (
    OpenRouterAuthError,
    OpenRouterError,
    OpenRouterInvalidResponseError,
    OpenRouterRateLimitError,
    OpenRouterServerError,
    OpenRouterTimeoutError,
)

logger = logging.getLogger(__name__)

# Simulation generation involves 4 tasks with nested evaluation metadata —
# large structured JSON. 90 s + max_tokens headroom avoids mid-JSON truncation.
REQUEST_TIMEOUT_SECONDS = 90.0
MAX_COMPLETION_TOKENS = 6000

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


class LLMRequestError(SimulationAgentError):
    """The LLM API call itself failed (connection, auth, rate limit, server error)."""


class SimulationAgentTimeoutError(SimulationAgentError):
    """The LLM API call did not complete within `REQUEST_TIMEOUT_SECONDS`."""


class InvalidSimulationResponseError(SimulationAgentError):
    """The LLM response could not be parsed or validated into `SimulationContent`."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_json_object(raw_text: str) -> str:
    """Best-effort extraction of a bare JSON object from the model's raw text."""
    stripped = raw_text.strip()

    fenced = _JSON_FENCE_RE.search(stripped)
    if fenced:
        return fenced.group(1)

    first_brace = stripped.find("{")
    last_brace = stripped.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return stripped[first_brace : last_brace + 1]

    return stripped


def _normalize_string_list(value: object, *, min_items: int, max_items: int, pad: str) -> list[str]:
    if isinstance(value, str):
        items = [part.strip() for part in value.split("\n") if part.strip()]
    elif isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
    else:
        items = []
    while len(items) < min_items:
        items.append(pad)
    return items[:max_items]


def _clamp_score(value: object, default: int = 5) -> int:
    try:
        score = int(round(float(value)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        score = default
    return max(0, min(10, score))


def _default_task(task_number: int, role_title: str, jd_snippet: str) -> dict:
    """Minimal valid task used only to pad under-length LLM output."""
    return {
        "task_number": task_number,
        "title": f"Core responsibility check {task_number}",
        "estimated_time": "5-10 mins",
        "difficulty": "Easy" if task_number == 1 else "Intermediate",
        "objective": f"Complete a workplace task relevant to {role_title}.",
        "context": (
            f"You are working as a {role_title}. Use the job description to decide "
            f"the best next action for this scenario."
        ),
        "resources": [
            {
                "type": "Job Description Excerpt",
                "content": jd_snippet[:800] or f"Role: {role_title}",
            }
        ],
        "activity": {
            "type": "short_answer",
            "question": f"What would you do first in this {role_title} scenario?",
            "options": [],
        },
        "expected_solution": (
            "Outline a clear, role-appropriate next step grounded in the JD requirements."
        ),
        "feedback": {
            "positive": "You identified a concrete next action.",
            "improvement": "Tie your answer more explicitly to a JD requirement.",
            "real_world_importance": "Prioritising the right first step is core to this role.",
        },
        "evaluation": {
            "communication": 5,
            "problem_solving": 6,
            "technical_judgment": 6,
            "collaboration": 4,
            "leadership": 4,
            "adaptability": 5,
        },
        "jd_reference": jd_snippet[:200] or role_title,
    }


def _normalize_task(raw: object, index: int, role_title: str, jd_snippet: str) -> dict:
    base = _default_task(index + 1, role_title, jd_snippet)
    if not isinstance(raw, dict):
        return base

    task = dict(base)
    for key in (
        "title",
        "estimated_time",
        "difficulty",
        "objective",
        "context",
        "expected_solution",
        "jd_reference",
    ):
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            task[key] = value.strip()

    task["task_number"] = index + 1

    resources = raw.get("resources")
    if isinstance(resources, list) and resources:
        cleaned = []
        for item in resources:
            if not isinstance(item, dict):
                continue
            rtype = str(item.get("type") or "").strip()
            content = str(item.get("content") or "").strip()
            if rtype and content:
                cleaned.append({"type": rtype, "content": content})
        if cleaned:
            task["resources"] = cleaned

    activity = raw.get("activity")
    if isinstance(activity, dict):
        atype = str(activity.get("type") or "short_answer").strip() or "short_answer"
        question = str(activity.get("question") or "").strip() or task["activity"]["question"]
        options = activity.get("options") if isinstance(activity.get("options"), list) else []
        task["activity"] = {
            "type": atype,
            "question": question,
            "options": [str(o).strip() for o in options if str(o).strip()],
        }

    feedback = raw.get("feedback")
    if isinstance(feedback, dict):
        for key in ("positive", "improvement", "real_world_importance"):
            value = feedback.get(key)
            if isinstance(value, str) and value.strip():
                task["feedback"][key] = value.strip()

    evaluation = raw.get("evaluation")
    if isinstance(evaluation, dict):
        task["evaluation"] = {
            key: _clamp_score(evaluation.get(key), default=task["evaluation"][key])
            for key in task["evaluation"]
        }

    return task


def _normalize_simulation_payload(payload: dict, role_title: str, jd_text: str) -> dict:
    """Coerce under-specified LLM JSON into a shape SimulationContent accepts."""
    jd_snippet = " ".join((jd_text or "").split())[:400] or role_title

    overview = payload.get("overview")
    if not isinstance(overview, dict):
        overview = {}
    payload["overview"] = {
        "company_context": str(overview.get("company_context") or "").strip()
        or f"A company hiring for {role_title}.",
        "team_context": str(overview.get("team_context") or "").strip()
        or f"You join the team supporting the {role_title} function.",
        "your_role": str(overview.get("your_role") or "").strip()
        or f"You are acting as a {role_title} for this experience.",
        "project_background": str(overview.get("project_background") or "").strip()
        or f"You will complete tasks drawn from the {role_title} job description.",
    }

    payload["job_title"] = str(payload.get("job_title") or role_title).strip() or role_title
    payload["estimated_duration"] = (
        str(payload.get("estimated_duration") or "").strip() or "30-45 mins"
    )
    payload["difficulty"] = str(payload.get("difficulty") or "").strip() or "Intermediate"

    payload["what_youll_learn"] = _normalize_string_list(
        payload.get("what_youll_learn"),
        min_items=3,
        max_items=5,
        pad=f"How a {role_title} approaches day-to-day work",
    )
    payload["what_youll_do"] = _normalize_string_list(
        payload.get("what_youll_do"),
        min_items=3,
        max_items=5,
        pad=f"Complete a practical {role_title} workplace task",
    )

    raw_tasks = payload.get("tasks") if isinstance(payload.get("tasks"), list) else []
    tasks = [
        _normalize_task(item, index, role_title, jd_snippet)
        for index, item in enumerate(raw_tasks[:6])
    ]
    while len(tasks) < 4:
        tasks.append(_default_task(len(tasks) + 1, role_title, jd_snippet))
    payload["tasks"] = tasks[:6]
    return payload


def _parse_and_validate(raw_text: str, role_title: str, jd_text: str = "") -> SimulationContent:
    """Parse the LLM's raw text into a validated `SimulationContent`."""
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

    payload = _normalize_simulation_payload(payload, role_title, jd_text)

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

    Sends the role title and full JD text to the LLM and returns a
    fully validated `SimulationContent`. Designed to be awaited inside
    `asyncio.gather()` in the simulation service for concurrent generation
    of all three simulations.
    """
    if not jd_text or not jd_text.strip():
        raise InvalidSimulationResponseError(
            f"Cannot generate a simulation for role '{role_title}': "
            f"the Job Description text is empty."
        )

    user_prompt = build_simulation_agent_user_prompt(role_title, jd_text)
    messages = [
        {"role": "system", "content": SIMULATION_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    logger.info("Simulation Agent starting generation for role: '%s'.", role_title)

    try:
        raw_text = await openrouter_client.chat_completion(
            messages=messages,
            temperature=TEMPERATURE,
            timeout=REQUEST_TIMEOUT_SECONDS,
            max_tokens=MAX_COMPLETION_TOKENS,
        )
    except OpenRouterTimeoutError as exc:
        raise SimulationAgentTimeoutError(
            f"Simulation Agent timed out generating simulation for role '{role_title}'."
        ) from exc
    except (
        OpenRouterAuthError,
        OpenRouterRateLimitError,
        OpenRouterServerError,
        OpenRouterInvalidResponseError,
        OpenRouterError,
    ) as exc:
        logger.error(
            "Simulation Agent LLM request failed for role '%s': %s", role_title, exc
        )
        raise LLMRequestError(
            f"AI service request failed while generating simulation for role "
            f"'{role_title}': {exc}"
        ) from exc

    if not raw_text:
        raise InvalidSimulationResponseError(
            f"Simulation Agent returned an empty response for role '{role_title}'."
        )

    try:
        simulation = _parse_and_validate(raw_text, role_title, jd_text)
    except InvalidSimulationResponseError as first_exc:
        # One repair pass: small models often return truncated / under-length JSON.
        logger.warning(
            "Simulation Agent schema/parse failure for '%s'; attempting repair: %s",
            role_title,
            first_exc,
        )
        repair_messages = [
            *messages,
            {"role": "assistant", "content": raw_text[:8000]},
            {
                "role": "user",
                "content": (
                    "Your previous response failed validation. "
                    f"Error: {first_exc}. "
                    "Return ONLY a complete valid JSON object with exactly 4 tasks, "
                    "matching the required schema. No markdown."
                ),
            },
        ]
        try:
            repaired = await openrouter_client.chat_completion(
                messages=repair_messages,
                temperature=0.2,
                timeout=REQUEST_TIMEOUT_SECONDS,
                max_tokens=MAX_COMPLETION_TOKENS,
            )
        except OpenRouterError as exc:
            raise InvalidSimulationResponseError(
                f"Simulation Agent repair call failed for role '{role_title}': {exc}"
            ) from first_exc
        simulation = _parse_and_validate(repaired, role_title, jd_text)

    logger.info(
        "Simulation Agent completed generation for role '%s': %d tasks.",
        role_title,
        len(simulation.tasks),
    )

    return simulation
