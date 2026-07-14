"""Career Recommendation Agent.

Sends a parsed resume + RAG-retrieved Job Description context to OpenRouter
and returns exactly three validated, structured career matches
(`CareerAdvisorAgentResponse`). Per `.cursorrules`, this is the only module
allowed to call the LLM for career recommendations — routes and services stay
thin and never talk to the AI client directly.

Responsibilities:
    - Receive parsed resume text, an optional resume review summary, and the
      Top-K retrieved Job Description chunks from ChromaDB (via
      `app.rag.retriever.retrieve_relevant_job_descriptions`).
    - Call the LLM with the Career Recommendation prompt.
    - Validate the JSON response against `CareerAdvisorAgentResponse`.
    - Enforce that every recommendation is grounded in a JD that was actually
      retrieved — the agent never trusts the model to have followed that
      instruction on its own.
    - Return exactly three structured matches, never raw text.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from pydantic import ValidationError

logger = logging.getLogger(__name__)

from app.models.job_match import CareerAdvisorAgentResponse, CareerMatchRecommendation
from app.prompts.career_advisor import (
    CAREER_ADVISOR_SYSTEM_PROMPT,
    build_career_advisor_user_prompt,
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

REQUEST_TIMEOUT_SECONDS = 45.0
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)


class CareerAdvisorError(Exception):
    """Base class for every Career Recommendation Agent failure."""


class LLMRequestError(CareerAdvisorError):
    """The LLM API call itself failed (connection, auth, rate limit, server error)."""


class CareerAdvisorTimeoutError(CareerAdvisorError):
    """The LLM API call did not complete within `REQUEST_TIMEOUT_SECONDS`."""


class InvalidCareerAdvisorResponseError(CareerAdvisorError):
    """The LLM response could not be parsed into three valid, retrieval-grounded matches."""


class NoRetrievedJobDescriptionsError(CareerAdvisorError):
    """There is nothing retrieved from RAG to compare the resume against."""


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


def _parse_agent_response(raw_text: str) -> CareerAdvisorAgentResponse:
    """Parse and validate the LLM's raw output into a `CareerAdvisorAgentResponse`."""
    candidate = _extract_json_object(raw_text)

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise InvalidCareerAdvisorResponseError(
            f"Career Recommendation Agent returned malformed JSON: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise InvalidCareerAdvisorResponseError(
            "Career Recommendation Agent response was valid JSON but not a JSON object."
        )

    try:
        return CareerAdvisorAgentResponse.model_validate(payload)
    except ValidationError as exc:
        raise InvalidCareerAdvisorResponseError(
            f"Career Recommendation Agent response failed schema validation: {exc}"
        ) from exc


def _enforce_retrieval_grounding(
    matches: list[CareerMatchRecommendation],
    retrieved_job_descriptions: list[dict[str, Any]],
) -> None:
    """Reject any recommendation that references a JD id we never retrieved.

    This is a hard guarantee, not just a prompt instruction: the RAG context
    is the only source of truth, so a recommendation whose
    `job_description_id` falls outside the retrieved set means the model
    hallucinated a career that was never uploaded.
    """
    retrieved_ids = {str(jd.get("job_description_id")) for jd in retrieved_job_descriptions}
    for match in matches:
        if match.job_description_id not in retrieved_ids:
            raise InvalidCareerAdvisorResponseError(
                f"Career Recommendation Agent referenced job_description_id="
                f"{match.job_description_id!r}, which was not among the retrieved "
                f"Job Descriptions {sorted(retrieved_ids)!r}."
            )


async def generate_career_matches(
    resume_text: str,
    retrieved_job_descriptions: list[dict[str, Any]],
    resume_review_summary: str | None = None,
) -> list[CareerMatchRecommendation]:
    """Run the Career Recommendation Agent over a resume and RAG-retrieved JDs.

    Parameters
    ----------
    resume_text:
        Full parsed resume text.
    retrieved_job_descriptions:
        Top-K retrieved Job Description chunks grouped by JD, as returned by
        `app.rag.retriever.retrieve_relevant_job_descriptions`. This is the
        ONLY source of truth for which careers may be recommended.
    resume_review_summary:
        Optional context from the Resume Reviewer Agent's report (e.g. its
        `summary` field).

    Returns
    -------
    list[CareerMatchRecommendation]
        Exactly three matches, ranked 1-3, each grounded in a distinct
        retrieved Job Description.

    Raises
    ------
    NoRetrievedJobDescriptionsError
        `retrieved_job_descriptions` is empty — there is nothing to compare
        the resume against.
    LLMRequestError
        The LLM API call failed (network, auth, rate limit, server error).
    CareerAdvisorTimeoutError
        The LLM API call did not complete within the configured timeout.
    InvalidCareerAdvisorResponseError
        The LLM response could not be parsed into three valid,
        retrieval-grounded matches.
    """
    if not retrieved_job_descriptions:
        raise NoRetrievedJobDescriptionsError(
            "No job descriptions were retrieved — upload job descriptions before "
            "requesting career recommendations."
        )

    user_prompt = build_career_advisor_user_prompt(
        resume_text,
        retrieved_job_descriptions,
        resume_review_summary=resume_review_summary,
    )
    messages = [
        {"role": "system", "content": CAREER_ADVISOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        raw_text = await openrouter_client.chat_completion(
            messages=messages,
            temperature=0.3,
            timeout=REQUEST_TIMEOUT_SECONDS,
            max_tokens=2048,
        )
    except OpenRouterTimeoutError as exc:
        raise CareerAdvisorTimeoutError(
            "Career Recommendation Agent timed out waiting for the AI service."
        ) from exc
    except (OpenRouterAuthError, OpenRouterRateLimitError, OpenRouterServerError, OpenRouterError) as exc:
        logger.error("Career Recommendation Agent LLM request failed: %s", exc)
        raise LLMRequestError(f"AI service request failed: {exc}") from exc

    if not raw_text:
        raise InvalidCareerAdvisorResponseError(
            "Career Recommendation Agent returned an empty response."
        )

    parsed = _parse_agent_response(raw_text)
    _enforce_retrieval_grounding(parsed.matches, retrieved_job_descriptions)

    return sorted(parsed.matches, key=lambda match: match.rank)
