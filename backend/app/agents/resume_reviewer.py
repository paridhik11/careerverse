"""Resume Reviewer Agent.

Sends a parsed resume to OpenRouter and returns a validated, structured
evaluation (`ResumeReviewReport`). Per `.cursorrules`, this is the only
module allowed to call the LLM for resume review — routes stay thin and
services never talk to the AI client directly.

Responsibilities:
    - Receive a parsed resume (`app.models.resume.ParsedResume`).
    - Compute deterministic ATS scores via `app.services.ats_scorer`.
    - Call the LLM with the scores embedded in the prompt so it *explains*
      them rather than inventing new ones.
    - Validate the JSON response against `ResumeReviewReport`.
    - Handle malformed JSON / API failures gracefully via typed exceptions.
    - Return a structured `ResumeReviewReport`, never raw text.

Determinism guarantee
---------------------
`overall_score` and `ats_score` are computed rule-based BEFORE calling the
LLM, then injected into the prompt.  The model is instructed not to change
them.  The same resume therefore always gets the same scores.

Retry logic
-----------
Transient errors (5xx, rate limits) are retried up to MAX_RETRIES times with
exponential back-off inside the shared OpenRouter client before raising the
error to the caller here.
"""

from __future__ import annotations

import json
import logging
import re
import traceback

from pydantic import ValidationError

from app.models.report import ResumeReviewReport
from app.models.resume import ParsedResume
from app.prompts.resume_reviewer_prompt import (
    RESUME_REVIEWER_SYSTEM_PROMPT,
    build_resume_reviewer_user_prompt,
)
from app.services import openrouter_client
from app.services.ats_scorer import compute_ats_scores
from app.services.openrouter_client import (
    OpenRouterAuthError,
    OpenRouterError,
    OpenRouterInvalidResponseError,
    OpenRouterRateLimitError,
    OpenRouterServerError,
    OpenRouterTimeoutError,
)

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 45.0
MAX_RETRIES = 2
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)


class ResumeReviewerError(Exception):
    """Base class for every Resume Reviewer Agent failure."""


class LLMRequestError(ResumeReviewerError):
    """The LLM API call itself failed (connection, auth, rate limit, server error)."""


class ResumeReviewTimeoutError(ResumeReviewerError):
    """The LLM API call did not complete within `REQUEST_TIMEOUT_SECONDS`."""


class InvalidReviewResponseError(ResumeReviewerError):
    """The LLM response could not be parsed into a valid `ResumeReviewReport`."""


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


def _normalize_string_list(
    value: object,
    *,
    min_items: int,
    max_items: int,
    pad_label: str,
) -> list[str]:
    """Coerce LLM list fields to the ResumeReviewReport length constraints.

    Models often return 1 long bullet instead of 3-6 short ones. Without this
    step, Pydantic raises ValidationError (too_short) and the API returns 502.
    """
    if isinstance(value, str):
        items = [part.strip() for part in value.split("\n") if part.strip()]
    elif isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
    else:
        items = []

    # If the model returned one long sentence, split on common delimiters.
    if len(items) == 1 and min_items > 1:
        split_bits = [
            part.strip(" .-•;\t")
            for part in items[0].replace(";", ".").split(".")
            if part.strip(" .-•;\t")
        ]
        if len(split_bits) >= min_items:
            items = split_bits

    while len(items) < min_items:
        items.append(f"Additional {pad_label} inferred from the resume content.")

    return items[:max_items]


def _parse_review_response(raw_text: str) -> ResumeReviewReport:
    """Parse and validate the LLM's raw output into a `ResumeReviewReport`."""
    candidate = _extract_json_object(raw_text)
    logger.info(
        "Resume Reviewer parsed candidate JSON (chars=%d): %s",
        len(candidate),
        candidate[:1000],
    )

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        tb = traceback.extract_tb(exc.__traceback__)
        frame = tb[-1] if tb else None
        logger.exception(
            "Resume Reviewer JSON parse failure type=%s msg=%s file=%s line=%s",
            type(exc).__name__,
            exc,
            frame.filename if frame else "?",
            frame.lineno if frame else "?",
        )
        traceback.print_exc()
        raise InvalidReviewResponseError(
            f"Resume Reviewer Agent returned malformed JSON: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise InvalidReviewResponseError(
            "Resume Reviewer Agent response was valid JSON but not a JSON object."
        )

    # Normalize BEFORE schema validation so under-length / mistyped model
    # output becomes a 200, not a 502 InvalidReviewResponseError.
    def _coerce_score(value: object, fallback: int = 0) -> int:
        try:
            score = int(round(float(value)))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            score = fallback
        return max(0, min(100, score))

    payload["overall_score"] = _coerce_score(payload.get("overall_score"))
    payload["ats_score"] = _coerce_score(payload.get("ats_score"))

    summary = payload.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        payload["summary"] = (
            "Resume review completed; see strengths, weaknesses, and suggestions below."
        )
    else:
        payload["summary"] = summary.strip()

    payload["strengths"] = _normalize_string_list(
        payload.get("strengths"), min_items=3, max_items=6, pad_label="strength"
    )
    payload["weaknesses"] = _normalize_string_list(
        payload.get("weaknesses"), min_items=3, max_items=6, pad_label="weakness"
    )
    payload["recommended_roles"] = _normalize_string_list(
        payload.get("recommended_roles"),
        min_items=3,
        max_items=5,
        pad_label="recommended role",
    )
    payload["ats_issues"] = [
        str(item).strip()
        for item in (payload.get("ats_issues") or [])
        if str(item).strip()
    ]
    payload["suggestions"] = [
        str(item).strip()
        for item in (payload.get("suggestions") or [])
        if str(item).strip()
    ]
    if not payload["suggestions"]:
        payload["suggestions"] = [
            "Add quantified impact metrics to experience bullets.",
            "Ensure Skills, Education, and Experience section headings are ATS-readable.",
        ]

    try:
        report = ResumeReviewReport.model_validate(payload)
        logger.info("Resume Reviewer schema validation OK: %s", report.model_dump())
        return report
    except ValidationError as exc:
        logger.exception(
            "Resume Reviewer schema mismatch type=%s msg=%s payload=%s",
            type(exc).__name__,
            exc,
            payload,
        )
        traceback.print_exc()
        raise InvalidReviewResponseError(
            f"Resume Reviewer Agent response failed schema validation: {exc}"
        ) from exc


async def review_resume(parsed_resume: ParsedResume) -> ResumeReviewReport:
    """Run the Resume Reviewer Agent over a parsed resume.

    Scores are deterministically computed BEFORE calling the LLM, which
    eliminates score variance across identical uploads.  The LLM's only job
    is to write the narrative explanation.

    Transient API failures are retried up to MAX_RETRIES times by the shared
    OpenRouter client.

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
    LLMRequestError
        The LLM API call failed after all retries (network, auth, rate
        limit, server error).
    ResumeReviewTimeoutError
        The LLM API call did not complete within the configured timeout.
    InvalidReviewResponseError
        The LLM response could not be parsed into a valid `ResumeReviewReport`.
    """
    # ── Deterministic scores (no LLM) ──────────────────────────────────────
    scores = compute_ats_scores(parsed_resume)

    user_prompt = build_resume_reviewer_user_prompt(parsed_resume, scores)
    messages = [
        {"role": "system", "content": RESUME_REVIEWER_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        raw_text = await openrouter_client.chat_completion(
            messages=messages,
            temperature=0.1,
            timeout=REQUEST_TIMEOUT_SECONDS,
            max_retries=MAX_RETRIES,
            max_tokens=2048,
        )
    except OpenRouterTimeoutError as exc:
        tb = traceback.extract_tb(exc.__traceback__)
        frame = tb[-1] if tb else None
        logger.exception(
            "Resume Reviewer timeout — type=%s msg=%s file=%s line=%s",
            type(exc).__name__,
            exc,
            frame.filename if frame else "?",
            frame.lineno if frame else "?",
        )
        traceback.print_exc()
        raise ResumeReviewTimeoutError(str(exc)) from exc
    except (
        OpenRouterAuthError,
        OpenRouterRateLimitError,
        OpenRouterServerError,
        OpenRouterInvalidResponseError,
        OpenRouterError,
    ) as exc:
        tb = traceback.extract_tb(exc.__traceback__)
        frame = tb[-1] if tb else None
        logger.exception(
            "Resume Reviewer OpenRouter failure — type=%s msg=%s file=%s line=%s",
            type(exc).__name__,
            exc,
            frame.filename if frame else "?",
            frame.lineno if frame else "?",
        )
        traceback.print_exc()
        raise LLMRequestError(str(exc)) from exc

    if not raw_text:
        raise InvalidReviewResponseError(
            "OpenRouter returned an empty response body for resume review."
        )

    logger.info("Resume Reviewer raw LLM text (chars=%d): %s", len(raw_text), raw_text[:1000])
    report = _parse_review_response(raw_text)

    # Enforce the deterministic scores — overwrite anything the model changed.
    return report.model_copy(
        update={
            "overall_score": scores.overall_score,
            "ats_score": scores.ats_score,
        }
    )
