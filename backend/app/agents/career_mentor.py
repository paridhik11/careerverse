"""AI Career Mentor Agent.

The single conversational AI assistant in CareerVerse. Accepts a user
message, assembled project context, and recent conversation history, then
streams a natural-language mentor response token-by-token via OpenRouter.

Per `.cursorrules`, this is the only module that calls the LLM for career
mentor responses. Routes stay thin (HTTP concerns only) and services handle
orchestration; this module handles only the AI interaction.

Interview prep capability: when the user asks for interview questions, this
agent delivers them grounded in the chosen career's JD text (which is
included in the context block assembled by `app.services.mentor_context`).
This replaces the previously-planned standalone Interview Coach page —
interview prep is a conversational capability of this agent, not a
separate pipeline step.

Responsibilities:
    - Accept user message, conversation history, and assembled context.
    - Build the full messages list via the prompt module.
    - Call OpenRouter with streaming enabled.
    - Yield text chunks as they arrive.
    - Raise descriptive typed exceptions on every failure path so the API
      layer can log precisely and return the correct HTTP status code.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from app.prompts.career_mentor import build_mentor_user_prompt
from app.services import openrouter_client
from app.services.openrouter_client import (
    OpenRouterAuthError,
    OpenRouterError,
    OpenRouterRateLimitError,
    OpenRouterServerError,
    OpenRouterTimeoutError,
)

logger = logging.getLogger(__name__)

# Conversational warmth balanced against accuracy — between the analytical
# agents (0.3) and the simulation agent (0.7).
TEMPERATURE = 0.6

# Streaming can be long for detailed answers (interview prep, roadmap
# explanations). Allow a generous timeout.
REQUEST_TIMEOUT_SECONDS = 120.0


# ---------------------------------------------------------------------------
# Typed exception hierarchy
# ---------------------------------------------------------------------------


class CareerMentorAgentError(Exception):
    """Base class for every Career Mentor Agent failure."""


class LLMRequestError(CareerMentorAgentError):
    """The LLM API call failed (connection, auth, rate limit, server error)."""


class CareerMentorTimeoutError(CareerMentorAgentError):
    """The LLM API call did not complete within `REQUEST_TIMEOUT_SECONDS`."""


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


async def stream_response(
    user_message: str,
    context: str,
    history: list[dict[str, str]],
) -> AsyncGenerator[str, None]:
    """Stream the Career Mentor's response to `user_message`.

    Calls OpenRouter with streaming enabled and yields non-empty text chunks
    as they arrive.

    The prompt module returns OpenAI-compatible message dicts
    (``[{"role": ..., "content": ...}, ...]``) which are passed directly to
    the OpenRouter streaming client — no conversion required.

    Parameters
    ----------
    user_message:
        The candidate's latest message to the mentor.
    context:
        The assembled project context block from
        ``app.services.mentor_context.assemble_context``. Contains the
        resume, review, chosen career + JD, skill gap, and roadmap — all
        formatted as labelled sections with explicit "not yet available"
        placeholders when data is missing.
    history:
        Recent conversation history (up to the last N messages) as a list of
        ``{"role": ..., "content": ...}`` dicts. Provides conversational
        continuity without inflating the context with the full history.

    Yields
    ------
    str
        Non-empty text chunks from the model's streaming response.

    Raises
    ------
    CareerMentorTimeoutError
        The LLM API call did not complete within ``REQUEST_TIMEOUT_SECONDS``.
    LLMRequestError
        The LLM API call failed (network, auth, rate limit, or server error).
    """
    messages = build_mentor_user_prompt(
        user_message=user_message,
        context=context,
        history=history,
    )

    logger.info(
        "Career Mentor Agent: starting streaming response "
        "(history_turns=%d, context_length=%d).",
        len(history),
        len(context),
    )

    try:
        async for chunk in openrouter_client.stream_chat_completion(
            messages=messages,
            temperature=TEMPERATURE,
            timeout=REQUEST_TIMEOUT_SECONDS,
        ):
            yield chunk
    except OpenRouterTimeoutError as exc:
        raise CareerMentorTimeoutError(
            "Career Mentor Agent timed out during streaming."
        ) from exc
    except (OpenRouterAuthError, OpenRouterRateLimitError, OpenRouterServerError, OpenRouterError) as exc:
        logger.error("Career Mentor Agent LLM request failed: %s", exc)
        raise LLMRequestError(
            f"AI service request failed during mentor streaming: {exc}"
        ) from exc

    logger.info("Career Mentor Agent: streaming response complete.")
