"""Resume Reviewer Agent.

Sends a parsed resume to Gemini and returns a validated, structured
evaluation (`ResumeReviewReport`). Per `.cursorrules`, this is the only
module allowed to call Gemini for resume review — routes stay thin and
services never talk to the Gemini SDK directly.

Responsibilities:
    - Receive a parsed resume (`app.models.resume.ParsedResume`).
    - Compute deterministic ATS scores via `app.services.ats_scorer`.
    - Call Gemini with the scores embedded in the prompt so it *explains*
      them rather than inventing new ones.
    - Validate the JSON response against `ResumeReviewReport`.
    - Handle malformed JSON / API failures gracefully via typed exceptions.
    - Return a structured `ResumeReviewReport`, never raw text.

Determinism guarantee
---------------------
`overall_score` and `ats_score` are computed rule-based BEFORE calling
Gemini, then injected into the prompt.  Gemini is instructed not to change
them.  The same resume therefore always gets the same scores.

Retry logic
-----------
Transient Gemini errors (5xx, rate limits) are retried up to MAX_RETRIES
times with exponential back-off before raising the error to the caller.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re

import httpx
from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from app.core.config import settings
from app.models.report import ResumeReviewReport
from app.models.resume import ParsedResume
from app.prompts.resume_reviewer_prompt import (
    RESUME_REVIEWER_SYSTEM_PROMPT,
    build_resume_reviewer_user_prompt,
)
from app.services.ats_scorer import compute_ats_scores

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-2.5-flash"
REQUEST_TIMEOUT_SECONDS = 45.0
MAX_RETRIES = 2
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)


class ResumeReviewerError(Exception):
    """Base class for every Resume Reviewer Agent failure."""


class GeminiRequestError(ResumeReviewerError):
    """The Gemini API call itself failed (connection, auth, rate limit, server error)."""


class ResumeReviewTimeoutError(ResumeReviewerError):
    """The Gemini API call did not complete within `REQUEST_TIMEOUT_SECONDS`."""


class InvalidReviewResponseError(ResumeReviewerError):
    """Gemini's response could not be parsed into a valid `ResumeReviewReport`."""


def _get_client() -> genai.Client:
    """Build a Gemini client from the `GEMINI_API_KEY` environment variable."""
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=int(REQUEST_TIMEOUT_SECONDS * 1000)),
    )


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


def _parse_review_response(raw_text: str) -> ResumeReviewReport:
    """Parse and validate Gemini's raw output into a `ResumeReviewReport`."""
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

    Scores are deterministically computed BEFORE calling Gemini, which
    eliminates score variance across identical uploads.  Gemini's only job
    is to write the narrative explanation.

    Transient API failures are retried up to MAX_RETRIES times.

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
    GeminiRequestError
        The Gemini API call failed after all retries (network, auth, rate
        limit, server error).
    ResumeReviewTimeoutError
        The Gemini API call did not complete within the configured timeout.
    InvalidReviewResponseError
        Gemini's response could not be parsed into a valid `ResumeReviewReport`.
    """
    # ── Deterministic scores (no LLM) ──────────────────────────────────────
    scores = compute_ats_scores(parsed_resume)

    client = _get_client()
    user_prompt = build_resume_reviewer_user_prompt(parsed_resume, scores)

    last_error: Exception | None = None

    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            wait_seconds = 2 ** attempt
            logger.warning(
                "Resume Reviewer: retrying Gemini call (attempt %d/%d) after %ds back-off.",
                attempt + 1,
                MAX_RETRIES + 1,
                wait_seconds,
            )
            await asyncio.sleep(wait_seconds)

        try:
            response = await client.aio.models.generate_content(
                model=MODEL_NAME,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=RESUME_REVIEWER_SYSTEM_PROMPT,
                    # Temperature 0 for maximum determinism in the explanation.
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
        except httpx.TimeoutException as exc:
            raise ResumeReviewTimeoutError(
                "Resume review timed out. Please try again in a moment."
            ) from exc
        except errors.APIError as exc:
            # Retry on 5xx (server errors) and 429 (rate limit); raise immediately
            # on 4xx client errors (bad key, invalid request, etc.)
            status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            is_transient = status is None or (
                isinstance(status, int) and (status >= 500 or status == 429)
            )
            if is_transient and attempt < MAX_RETRIES:
                last_error = exc
                continue
            raise GeminiRequestError(
                "The AI service is temporarily unavailable. Please try again."
            ) from exc
        else:
            last_error = None
            break

    if last_error is not None:
        raise GeminiRequestError(
            "The AI service is temporarily unavailable. Please try again."
        ) from last_error

    raw_text = response.text  # type: ignore[union-attr]
    if not raw_text:
        raise InvalidReviewResponseError(
            "The AI service returned an empty response. Please try again."
        )

    report = _parse_review_response(raw_text)

    # Enforce the deterministic scores — overwrite anything Gemini changed.
    return report.model_copy(
        update={
            "overall_score": scores.overall_score,
            "ats_score": scores.ats_score,
        }
    )
