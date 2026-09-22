"""Reusable OpenRouter HTTP client.

Wraps the OpenRouter OpenAI-compatible Chat Completions API
(https://openrouter.ai/api/v1) so every AI agent can make LLM calls through
a single, shared async HTTP client without reimplementing connection pooling,
retry logic, or header management.

Usage (non-streaming):
    from app.services.openrouter_client import chat_completion
    text = await chat_completion(messages, temperature=0.3, timeout=60.0)

Usage (streaming):
    from app.services.openrouter_client import stream_chat_completion
    async for chunk in stream_chat_completion(messages, temperature=0.6):
        yield chunk

All callers must import from this module only — agents never construct their
own httpx clients or build Authorization headers themselves.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Fallback when Settings.openrouter_model is blank. Prefer the value in .env /
# Settings (currently meta-llama/llama-3.1-8b-instruct).
DEFAULT_MODEL = "meta-llama/llama-3.1-8b-instruct"

# Module-level singleton — reused across all requests for connection pooling.
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    """Return the shared async HTTP client, creating it on first use."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            base_url=OPENROUTER_BASE_URL,
            # Per-request timeouts are passed at call time; this is the
            # connection / pool-level default.
            timeout=httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=5.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _http_client


def _build_headers() -> dict[str, str]:
    """Build the required OpenRouter request headers."""
    return {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "HTTP-Referer": settings.openrouter_referer,
        "X-Title": settings.openrouter_app_name,
        "Content-Type": "application/json",
    }


def _get_model() -> str:
    """Return the configured model name, falling back to the module default."""
    return settings.openrouter_model or DEFAULT_MODEL


# ---------------------------------------------------------------------------
# Typed exception hierarchy
# ---------------------------------------------------------------------------


class OpenRouterError(Exception):
    """Base class for all OpenRouter client errors."""


class OpenRouterRateLimitError(OpenRouterError):
    """Rate limit hit (HTTP 429). Transient — eligible for retry."""


class OpenRouterAuthError(OpenRouterError):
    """Authentication or authorisation failure (HTTP 401/403). Not retried."""


class OpenRouterServerError(OpenRouterError):
    """Transient server-side error (HTTP 5xx or connection failure)."""


class OpenRouterTimeoutError(OpenRouterError):
    """Request did not complete within the configured timeout."""


class OpenRouterInvalidResponseError(OpenRouterError):
    """Response was not valid JSON or lacked the expected structure."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _estimate_tokens(messages: list[dict[str, str]]) -> tuple[int, int]:
    """Return (total_chars, estimated_tokens) for a message list.

    Estimation: 1 token ≈ 4 chars (conservative for English prose).
    """
    total_chars = sum(len(m.get("content", "") or "") for m in messages)
    return total_chars, total_chars // 4


def _classify_body_error(data: dict, model: str, attempt: int) -> Exception | None:
    """Classify an OpenRouter body-level error, or return None if none present.

    OpenRouter sometimes returns HTTP 200 with an error payload, e.g.::

        {"error": {"message": "The operation was aborted", "code": 504}}

    This must be checked BEFORE accessing ``data["choices"]`` to avoid hiding
    the real failure behind a misleading KeyError / InvalidResponseError.
    """
    if "error" not in data:
        return None

    err = data["error"]
    code = int(err.get("code", 0)) if isinstance(err, dict) else 0
    msg = str(err.get("message", err) if isinstance(err, dict) else err)

    logger.error(
        "OpenRouter returned body-level error — model=%s attempt=%d code=%s msg=%s",
        model,
        attempt + 1,
        code,
        msg,
    )

    if code in (401, 403):
        return OpenRouterAuthError(
            f"OpenRouter authentication failed (body error code={code}): {msg}. "
            "Check OPENROUTER_API_KEY in your .env file."
        )

    if code == 429:
        return OpenRouterRateLimitError(
            f"OpenRouter rate limit hit (body error code=429): {msg}"
        )

    # 504 / "aborted" / "timeout" → model-side gateway timeout.
    # Not retried — retrying usually hits the same timeout again.
    if code == 504 or "abort" in msg.lower() or "timeout" in msg.lower():
        return OpenRouterTimeoutError(
            f"OpenRouter model timed out (body error code={code}): {msg}. "
            "The model took too long to respond. "
            "Try reducing prompt size or switching to a faster model."
        )

    return OpenRouterServerError(f"OpenRouter body error (code={code}): {msg}")


# ---------------------------------------------------------------------------
# Non-streaming completion
# ---------------------------------------------------------------------------


async def chat_completion(
    messages: list[dict[str, str]],
    temperature: float = 0.3,
    timeout: float = 60.0,
    max_retries: int = 2,
    max_tokens: int | None = None,
) -> str:
    """Call OpenRouter Chat Completions and return the assistant's text content.

    Retries ONLY on transient failures (HTTP 5xx, body-level server errors,
    rate limits, connection errors) up to ``max_retries`` times with
    exponential back-off.

    Timeouts (both network-level ``httpx.TimeoutException`` and OpenRouter's
    HTTP-200 body error with code 504) are NOT retried — they indicate the
    model is too slow for this prompt size; retrying will just time out again.

    Authentication errors (401/403) are never retried.

    Parameters
    ----------
    messages:
        OpenAI-compatible message list (``[{"role": ..., "content": ...}, ...]``).
    temperature:
        Sampling temperature forwarded to the model.
    timeout:
        Per-request timeout in seconds.
    max_retries:
        Maximum number of retry attempts after the first failure.
    max_tokens:
        Optional completion token budget. Agents pass this to avoid truncated
        JSON on larger structured outputs (simulations, roadmaps).

    Returns
    -------
    str
        The assistant's response text (``choices[0].message.content``).

    Raises
    ------
    OpenRouterTimeoutError
        The request did not complete within ``timeout`` seconds, or OpenRouter
        returned a body-level 504 error.
    OpenRouterAuthError
        The API key is missing or invalid (HTTP 401/403 or body error).
    OpenRouterRateLimitError
        Rate limit exceeded after all retry attempts.
    OpenRouterServerError
        Server or connection error after all retry attempts.
    OpenRouterInvalidResponseError
        The response could not be parsed or lacked the expected structure.
    """
    if not (settings.openrouter_api_key or "").strip():
        raise OpenRouterAuthError(
            "OPENROUTER_API_KEY is not set. Add it to backend/.env before "
            "calling AI agents."
        )

    client = _get_http_client()
    model = _get_model()
    payload: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    total_chars, est_tokens = _estimate_tokens(messages)
    logger.info(
        "OpenRouter request — model=%s  prompt_chars=%d  est_tokens≈%d  "
        "timeout=%.0fs  max_retries=%d  max_tokens=%s",
        model,
        total_chars,
        est_tokens,
        timeout,
        max_retries,
        max_tokens,
    )

    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        if attempt > 0:
            wait_seconds = 2**attempt
            logger.warning(
                "OpenRouter: retrying (attempt %d/%d) after %ds back-off.",
                attempt + 1,
                max_retries + 1,
                wait_seconds,
            )
            await asyncio.sleep(wait_seconds)

        try:
            response = await client.post(
                "/chat/completions",
                headers=_build_headers(),
                json=payload,
                timeout=timeout,
            )
        except httpx.TimeoutException as exc:
            # Network-level timeout — do NOT retry; just raise immediately.
            raise OpenRouterTimeoutError(
                f"OpenRouter request timed out after {timeout:.0f}s "
                f"(model={model}, est_tokens≈{est_tokens}). "
                "Try reducing prompt size or switching to a faster model."
            ) from exc
        except httpx.RequestError as exc:
            # Transient connection error — eligible for retry.
            if attempt < max_retries:
                last_error = exc
                logger.warning(
                    "OpenRouter: connection error on attempt %d: %s",
                    attempt + 1,
                    exc,
                )
                continue
            raise OpenRouterServerError(
                "The AI service is temporarily unreachable. Please try again."
            ) from exc

        status = response.status_code
        logger.debug(
            "OpenRouter: HTTP %d received (model=%s, attempt=%d).",
            status,
            model,
            attempt + 1,
        )

        if status in (401, 403):
            raise OpenRouterAuthError(
                f"OpenRouter authentication failed (HTTP {status}). "
                "Check OPENROUTER_API_KEY in your .env file."
            )

        if status == 429:
            if attempt < max_retries:
                last_error = OpenRouterRateLimitError("Rate limit hit.")
                logger.warning(
                    "OpenRouter: rate limit hit on attempt %d.", attempt + 1
                )
                continue
            raise OpenRouterRateLimitError(
                "The AI service is currently rate-limited. Please try again in a moment."
            )

        if status >= 500:
            if attempt < max_retries:
                last_error = OpenRouterServerError(f"HTTP {status}")
                logger.warning(
                    "OpenRouter: server error %d on attempt %d.",
                    status,
                    attempt + 1,
                )
                continue
            raise OpenRouterServerError(
                f"The AI service returned a server error (HTTP {status}). Please try again."
            )

        if status != 200:
            error_body = response.text[:500]
            logger.error(
                "OpenRouter unexpected status %d (model=%s): %s",
                status,
                model,
                error_body,
            )
            raise OpenRouterError(
                f"OpenRouter returned an unexpected status code {status}: {error_body}"
            )

        # --- Parse JSON ---
        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise OpenRouterInvalidResponseError(
                f"OpenRouter returned invalid JSON: {exc}"
            ) from exc

        logger.debug(
            "OpenRouter response body (first 500 chars): %s", str(data)[:500]
        )

        # --- Check for body-level error BEFORE accessing choices ---
        body_error = _classify_body_error(data, model, attempt)
        if body_error is not None:
            # Auth / timeout: never retry.
            if isinstance(body_error, (OpenRouterAuthError, OpenRouterTimeoutError)):
                raise body_error
            # Rate limit / server: retry while attempts remain.
            if attempt < max_retries and isinstance(
                body_error, (OpenRouterRateLimitError, OpenRouterServerError)
            ):
                last_error = body_error
                continue
            raise body_error

        # --- Extract content ---
        try:
            content: str = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise OpenRouterInvalidResponseError(
                f"OpenRouter response missing expected fields: {exc}. "
                f"Response snippet: {str(data)[:300]}"
            ) from exc

        if not content:
            raise OpenRouterInvalidResponseError(
                "The AI service returned an empty response. Please try again."
            )

        logger.info(
            "OpenRouter: success — model=%s  response_chars=%d.",
            model,
            len(content),
        )
        return content

    raise OpenRouterServerError(
        "The AI service is temporarily unavailable after multiple retries. "
        "Please try again later."
    ) from last_error


# ---------------------------------------------------------------------------
# Streaming completion
# ---------------------------------------------------------------------------


async def stream_chat_completion(
    messages: list[dict[str, str]],
    temperature: float = 0.6,
    timeout: float = 120.0,
) -> AsyncGenerator[str, None]:
    """Stream a Chat Completion response from OpenRouter via Server-Sent Events.

    Yields non-empty text delta chunks as they arrive. No retries are applied
    to streaming calls — the connection is already open when chunks start
    flowing, and partial retries could produce duplicate output.

    Parameters
    ----------
    messages:
        OpenAI-compatible message list.
    temperature:
        Sampling temperature forwarded to the model.
    timeout:
        Total timeout for the streaming request in seconds.

    Yields
    ------
    str
        Non-empty text chunks from the model's ``choices[0].delta.content``.

    Raises
    ------
    OpenRouterTimeoutError
        The stream did not complete within ``timeout`` seconds.
    OpenRouterAuthError
        The API key is missing or invalid (HTTP 401/403).
    OpenRouterRateLimitError
        Rate limit hit before the stream started.
    OpenRouterServerError
        Server or connection error.
    """
    if not (settings.openrouter_api_key or "").strip():
        raise OpenRouterAuthError(
            "OPENROUTER_API_KEY is not set. Add it to backend/.env before "
            "calling AI agents."
        )

    client = _get_http_client()
    model = _get_model()
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }

    total_chars, est_tokens = _estimate_tokens(messages)
    logger.info(
        "OpenRouter stream request — model=%s  prompt_chars=%d  est_tokens≈%d  "
        "timeout=%.0fs",
        model,
        total_chars,
        est_tokens,
        timeout,
    )

    try:
        async with client.stream(
            "POST",
            "/chat/completions",
            headers=_build_headers(),
            json=payload,
            timeout=timeout,
        ) as response:
            status = response.status_code

            if status in (401, 403):
                raise OpenRouterAuthError(
                    f"OpenRouter authentication failed (HTTP {status})."
                )
            if status == 429:
                raise OpenRouterRateLimitError(
                    "The AI service is currently rate-limited. Please try again."
                )
            if status >= 500:
                raise OpenRouterServerError(
                    f"The AI service returned a server error (HTTP {status})."
                )
            if status != 200:
                body = (await response.aread())[:500].decode("utf-8", errors="replace")
                logger.error(
                    "OpenRouter stream unexpected status %d (model=%s): %s",
                    status,
                    model,
                    body,
                )
                raise OpenRouterError(
                    f"OpenRouter returned unexpected status {status}: {body}"
                )

            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]  # strip "data: " prefix
                if data_str.strip() == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    # Check for body-level error in SSE chunk
                    if "error" in data:
                        err = data["error"]
                        code = int(err.get("code", 0)) if isinstance(err, dict) else 0
                        msg = str(
                            err.get("message", err) if isinstance(err, dict) else err
                        )
                        logger.error(
                            "OpenRouter stream body error — model=%s code=%s msg=%s",
                            model,
                            code,
                            msg,
                        )
                        if (
                            code == 504
                            or "abort" in msg.lower()
                            or "timeout" in msg.lower()
                        ):
                            raise OpenRouterTimeoutError(
                                f"OpenRouter stream timed out (code={code}): {msg}"
                            )
                        if code in (401, 403):
                            raise OpenRouterAuthError(
                                f"OpenRouter stream auth failed (code={code}): {msg}"
                            )
                        if code == 429:
                            raise OpenRouterRateLimitError(
                                f"OpenRouter stream rate-limited: {msg}"
                            )
                        raise OpenRouterServerError(
                            f"OpenRouter stream error (code={code}): {msg}"
                        )
                    delta = data["choices"][0]["delta"].get("content") or ""
                    if delta:
                        yield delta
                except (
                    OpenRouterTimeoutError,
                    OpenRouterAuthError,
                    OpenRouterRateLimitError,
                    OpenRouterServerError,
                    OpenRouterError,
                ):
                    raise
                except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                    # Malformed SSE chunks are silently skipped — the stream
                    # continues; partial output is better than aborting.
                    continue

    except httpx.TimeoutException as exc:
        raise OpenRouterTimeoutError(
            "The AI service stream timed out. Please try again."
        ) from exc
    except httpx.RequestError as exc:
        raise OpenRouterServerError(
            f"The AI service stream failed: {exc}"
        ) from exc

    logger.debug("OpenRouter: streaming response complete (model=%s).", model)
