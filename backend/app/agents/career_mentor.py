"""AI Career Mentor Agent.

The single conversational AI assistant in CareerVerse. Accepts a user
message, assembled project context, and recent conversation history, then
streams a natural-language mentor response token-by-token from Gemini.

Per `.cursorrules`, this is the only module that calls Gemini for career
mentor responses. Routes stay thin (HTTP concerns only) and services handle
orchestration; this module handles only the Gemini interaction.

Interview prep capability: when the user asks for interview questions, this
agent delivers them grounded in the chosen career's JD text (which is
included in the context block assembled by `app.services.mentor_context`).
This replaces the previously-planned standalone Interview Coach page —
interview prep is a conversational capability of this agent, not a
separate pipeline step.

Responsibilities:
    - Accept user message, conversation history, and assembled context.
    - Build the full messages list via the prompt module.
    - Call Gemini with streaming enabled.
    - Yield text chunks as they arrive.
    - Raise descriptive typed exceptions on every failure path so the API
      layer can log precisely and return the correct HTTP status code.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

import httpx
from google import genai
from google.genai import errors, types

from app.core.config import settings
from app.prompts.career_mentor import build_mentor_user_prompt

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-2.5-flash"

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


class GeminiRequestError(CareerMentorAgentError):
    """The Gemini API call failed (connection, auth, rate limit, server error)."""


class CareerMentorTimeoutError(CareerMentorAgentError):
    """The Gemini API call did not complete within `REQUEST_TIMEOUT_SECONDS`."""


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


def _to_gemini_contents(
    messages: list[dict[str, str]],
) -> tuple[str | None, list[types.Content]]:
    """Split prompt message dicts into Gemini system_instruction + contents.

    The prompt module still returns role/content message dicts
    (system / user / assistant). Gemini uses ``system_instruction`` plus
    ``user``/``model`` content turns.
    """
    system_instruction: str | None = None
    contents: list[types.Content] = []

    for message in messages:
        role = message["role"]
        text = message["content"]
        if role == "system":
            system_instruction = (
                text if system_instruction is None else f"{system_instruction}\n\n{text}"
            )
            continue
        gemini_role = "user" if role == "user" else "model"
        contents.append(
            types.Content(role=gemini_role, parts=[types.Part.from_text(text=text)])
        )

    return system_instruction, contents


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


async def stream_response(
    user_message: str,
    context: str,
    history: list[dict[str, str]],
) -> AsyncGenerator[str, None]:
    """Stream the Career Mentor's response to `user_message`.

    Calls Gemini with streaming enabled and yields non-empty text chunks as
    they arrive from the Gemini streaming API.

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
        The Gemini API call did not complete within ``REQUEST_TIMEOUT_SECONDS``.
    GeminiRequestError
        The Gemini API call failed (network, auth, rate limit, or server error).
    """
    client = _get_client()
    messages = build_mentor_user_prompt(
        user_message=user_message,
        context=context,
        history=history,
    )
    system_instruction, contents = _to_gemini_contents(messages)

    logger.info(
        "Career Mentor Agent: starting streaming response "
        "(history_turns=%d, context_length=%d).",
        len(history),
        len(context),
    )

    try:
        stream = await client.aio.models.generate_content_stream(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=TEMPERATURE,
            ),
        )
    except httpx.TimeoutException as exc:
        raise CareerMentorTimeoutError(
            "Career Mentor Agent timed out while starting the stream."
        ) from exc
    except errors.APIError as exc:
        raise GeminiRequestError(
            f"Gemini request failed during mentor streaming: {exc}"
        ) from exc

    try:
        async for chunk in stream:
            text = chunk.text
            if text:
                yield text
    except httpx.TimeoutException as exc:
        raise CareerMentorTimeoutError(
            "Career Mentor Agent timed out during streaming."
        ) from exc
    except errors.APIError as exc:
        raise GeminiRequestError(
            f"Gemini stream failed during mentor response: {exc}"
        ) from exc

    logger.info("Career Mentor Agent: streaming response complete.")
