"""AI Career Mentor Agent.

The single conversational AI assistant in CareerVerse. Accepts a user
message, assembled project context, and recent conversation history, then
streams a natural-language mentor response token-by-token from GPT-4o.

Per `.cursorrules`, this is the only module that calls OpenAI for career
mentor responses. Routes stay thin (HTTP concerns only) and services handle
orchestration; this module handles only the OpenAI interaction.

Interview prep capability: when the user asks for interview questions, this
agent delivers them grounded in the chosen career's JD text (which is
included in the context block assembled by `app.services.mentor_context`).
This replaces the previously-planned standalone Interview Coach page —
interview prep is a conversational capability of this agent, not a
separate pipeline step.

Responsibilities:
    - Accept user message, conversation history, and assembled context.
    - Build the full messages list via the prompt module.
    - Call GPT-4o with streaming enabled.
    - Yield text chunks as they arrive.
    - Raise descriptive typed exceptions on every failure path so the API
      layer can log precisely and return the correct HTTP status code.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from openai import APIConnectionError, APIError, APITimeoutError, AsyncOpenAI, RateLimitError

from app.core.config import settings
from app.prompts.career_mentor import build_mentor_user_prompt

logger = logging.getLogger(__name__)

MODEL_NAME = "gpt-4o"

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


class OpenAIRequestError(CareerMentorAgentError):
    """The OpenAI API call failed (connection, auth, rate limit, server error)."""


class CareerMentorTimeoutError(CareerMentorAgentError):
    """The OpenAI API call did not complete within `REQUEST_TIMEOUT_SECONDS`."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_client() -> AsyncOpenAI:
    """Build an AsyncOpenAI client from settings.

    Constructed at call time (not module level) so tests can monkeypatch
    `settings.openai_api_key` without reloading the module.
    """
    return AsyncOpenAI(api_key=settings.openai_api_key, timeout=REQUEST_TIMEOUT_SECONDS)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


async def stream_response(
    user_message: str,
    context: str,
    history: list[dict[str, str]],
) -> AsyncGenerator[str, None]:
    """Stream the Career Mentor's response to `user_message`.

    Calls GPT-4o with streaming enabled and yields non-empty text chunks as
    they arrive from the OpenAI streaming API.

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
        The OpenAI API call did not complete within ``REQUEST_TIMEOUT_SECONDS``.
    OpenAIRequestError
        The OpenAI API call failed (network, auth, rate limit, or server error).
    """
    client = _get_client()
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
        stream = await client.chat.completions.create(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            messages=messages,
            stream=True,
        )
    except APITimeoutError as exc:
        raise CareerMentorTimeoutError(
            "Career Mentor Agent timed out while starting the stream."
        ) from exc
    except (APIConnectionError, RateLimitError, APIError) as exc:
        raise OpenAIRequestError(
            f"OpenAI request failed during mentor streaming: {exc}"
        ) from exc

    try:
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content
    except APITimeoutError as exc:
        raise CareerMentorTimeoutError(
            "Career Mentor Agent timed out during streaming."
        ) from exc
    except (APIConnectionError, RateLimitError, APIError) as exc:
        raise OpenAIRequestError(
            f"OpenAI stream failed during mentor response: {exc}"
        ) from exc

    logger.info("Career Mentor Agent: streaming response complete.")
