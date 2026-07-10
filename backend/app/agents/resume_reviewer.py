"""Resume Reviewer Agent.

Sends a parsed resume to OpenAI GPT-4o and returns a validated, structured
evaluation (`ResumeReviewReport`). Per `.cursorrules`, this is the only
module allowed to call OpenAI for resume review — routes stay thin and
services never talk to the OpenAI SDK directly.

Responsibilities:
    - Receive a parsed resume (`app.models.resume.ParsedResume`).
    - Call GPT-4o with the Resume Reviewer prompt.
    - Validate the JSON response against `ResumeReviewReport`.
    - Handle malformed JSON / API failures gracefully via typed exceptions.
    - Return a structured `ResumeReviewReport`, never raw text.
"""

from __future__ import annotations

import json
import re

from openai import APIConnectionError, APIError, APITimeoutError, AsyncOpenAI, RateLimitError
from pydantic import ValidationError

from app.core.config import settings
from app.models.report import ResumeReviewReport
from app.models.resume import ParsedResume
from app.prompts.resume_reviewer_prompt import (
    RESUME_REVIEWER_SYSTEM_PROMPT,
    build_resume_reviewer_user_prompt,
)

MODEL_NAME = "gpt-4o"
REQUEST_TIMEOUT_SECONDS = 45.0
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)


class ResumeReviewerError(Exception):
    """Base class for every Resume Reviewer Agent failure."""


class OpenAIRequestError(ResumeReviewerError):
    """The OpenAI API call itself failed (connection, auth, rate limit, server error)."""


class ResumeReviewTimeoutError(ResumeReviewerError):
    """The OpenAI API call did not complete within `REQUEST_TIMEOUT_SECONDS`."""


class InvalidReviewResponseError(ResumeReviewerError):
    """GPT-4o's response could not be parsed into a valid `ResumeReviewReport`."""


def _get_client() -> AsyncOpenAI:
    """Build an OpenAI client from the `OPENAI_API_KEY` environment variable.

    Not module-level so tests can monkeypatch `settings.openai_api_key`
    without having to reload this module.
    """
    return AsyncOpenAI(api_key=settings.openai_api_key, timeout=REQUEST_TIMEOUT_SECONDS)


def _extract_json_object(raw_text: str) -> str:
    """Best-effort extraction of a bare JSON object from the model's raw text.

    `response_format={"type": "json_object"}` should already guarantee bare
    JSON, but this guards against the model wrapping it in a code fence or
    adding stray text anyway, instead of failing the whole request.
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


def _parse_review_response(raw_text: str) -> ResumeReviewReport:
    """Parse and validate GPT-4o's raw output into a `ResumeReviewReport`."""
    candidate = _extract_json_object(raw_text)

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise InvalidReviewResponseError(
            f"Resume Reviewer Agent returned malformed JSON: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise InvalidReviewResponseError(
            "Resume Reviewer Agent response was valid JSON but not a JSON object."
        )

    try:
        return ResumeReviewReport.model_validate(payload)
    except ValidationError as exc:
        raise InvalidReviewResponseError(
            f"Resume Reviewer Agent response failed schema validation: {exc}"
        ) from exc


async def review_resume(parsed_resume: ParsedResume) -> ResumeReviewReport:
    """Run the Resume Reviewer Agent over a parsed resume.

    Parameters
    ----------
    parsed_resume:
        Structured resume fields produced by `app.services.resume_parser`.

    Returns
    -------
    ResumeReviewReport
        Validated structured evaluation (scores, strengths, weaknesses,
        ATS issues, suggestions, recommended roles).

    Raises
    ------
    OpenAIRequestError
        The OpenAI API call failed (network, auth, rate limit, server error).
    ResumeReviewTimeoutError
        The OpenAI API call did not complete within the configured timeout.
    InvalidReviewResponseError
        GPT-4o's response could not be parsed into a valid `ResumeReviewReport`.
    """
    client = _get_client()

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": RESUME_REVIEWER_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_resume_reviewer_user_prompt(parsed_resume),
                },
            ],
        )
    except APITimeoutError as exc:
        raise ResumeReviewTimeoutError(
            "Resume Reviewer Agent timed out waiting for OpenAI."
        ) from exc
    except (APIConnectionError, RateLimitError, APIError) as exc:
        raise OpenAIRequestError(f"OpenAI request failed: {exc}") from exc

    raw_text = response.choices[0].message.content if response.choices else None
    if not raw_text:
        raise InvalidReviewResponseError("Resume Reviewer Agent returned an empty response.")

    return _parse_review_response(raw_text)
