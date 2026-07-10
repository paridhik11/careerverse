"""Embedding generation and text chunking for the RAG pipeline.

Uses OpenAI text-embedding-3-small (1 536 dimensions, cheap and fast).

Chunking strategy
-----------------
Text is split on sentence and bullet-point boundaries, then grouped into
chunks targeting ~500 tokens (~2 000 chars at 4 chars/token).  The last
~50 tokens (~200 chars) of every chunk are carried forward as overlap so
context is not lost at chunk boundaries.

Public API
----------
chunk_text(text, *, job_description_id, filename, role_title, ...) -> list[dict]
generate_embedding(text)            -> list[float]          (sync)
generate_embeddings(texts)          -> list[list[float]]    (sync, batched)
generate_embedding_async(text)      -> list[float]          (async)
generate_embeddings_async(texts)    -> list[list[float]]    (async, batched)
"""

from __future__ import annotations

import re
from typing import Any

from openai import AsyncOpenAI, OpenAI

from app.core.config import settings

EMBEDDING_MODEL = "text-embedding-3-small"

# 4 chars ≈ 1 token (rough English heuristic — no tiktoken dependency needed).
_CHARS_PER_TOKEN = 4
CHUNK_TARGET_CHARS: int = 500 * _CHARS_PER_TOKEN   # ≈ 2 000 characters
OVERLAP_CHARS: int = 50 * _CHARS_PER_TOKEN          # ≈ 200 characters

# Split after `.  !  ?` followed by whitespace + capital letter, OR
# at a blank line (paragraph break), OR before a bullet/numbered-list item.
_SENTENCE_SPLIT_RE = re.compile(
    r"(?<=[.!?])\s+(?=[A-Z])"         # sentence end → capital start
    r"|\n{2,}"                          # blank line / paragraph break
    r"|(?<=\n)(?=[-*•]\s)"             # bullet item start
    r"|(?<=\n)(?=\d+[.)]\s)",          # numbered list item start
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------


def _split_into_units(text: str) -> list[str]:
    """Split *text* into the smallest meaningful units (sentences, bullets, paragraphs)."""
    raw_units = _SENTENCE_SPLIT_RE.split(text)
    return [u.strip() for u in raw_units if u.strip()]


def chunk_text(
    text: str,
    *,
    job_description_id: str | int,
    filename: str,
    role_title: str,
    chunk_target_chars: int = CHUNK_TARGET_CHARS,
    overlap_chars: int = OVERLAP_CHARS,
) -> list[dict[str, Any]]:
    """Split *text* into overlapping chunks and attach per-chunk metadata.

    Parameters
    ----------
    text:
        Full parsed text of the job description.
    job_description_id:
        Database id of the parent JobDescription record.
    filename:
        Original upload filename.
    role_title:
        Best-effort role title extracted during upload.
    chunk_target_chars:
        Soft upper limit (characters) before a new chunk starts.
    overlap_chars:
        Minimum characters of the previous chunk to carry into the next.

    Returns
    -------
    list of dicts, each with:
        text      – chunk body string
        metadata  – {job_description_id, filename, role_title,
                     chunk_index, source_type}
    """
    units = _split_into_units(text)
    if not units:
        return []

    chunks: list[dict[str, Any]] = []
    current_units: list[str] = []
    current_chars: int = 0

    for unit in units:
        unit_len = len(unit)

        if current_chars + unit_len > chunk_target_chars and current_units:
            # Flush current chunk.
            chunks.append(_make_chunk(current_units, len(chunks), job_description_id, filename, role_title))

            # Build overlap: keep the tail of the previous chunk until we
            # have at least overlap_chars worth of text.
            overlap_units: list[str] = []
            overlap_accumulated = 0
            for prev_unit in reversed(current_units):
                overlap_accumulated += len(prev_unit)
                overlap_units.insert(0, prev_unit)
                if overlap_accumulated >= overlap_chars:
                    break

            current_units = overlap_units + [unit]
            current_chars = sum(len(u) for u in current_units)
        else:
            current_units.append(unit)
            current_chars += unit_len

    # Flush the last (possibly partial) chunk.
    if current_units:
        chunks.append(_make_chunk(current_units, len(chunks), job_description_id, filename, role_title))

    return chunks


def _make_chunk(
    units: list[str],
    index: int,
    job_description_id: str | int,
    filename: str,
    role_title: str,
) -> dict[str, Any]:
    return {
        "text": " ".join(units),
        "metadata": {
            "job_description_id": str(job_description_id),
            "filename": filename,
            "role_title": role_title,
            "chunk_index": index,
            "source_type": "job_description",
        },
    }


# ---------------------------------------------------------------------------
# Embedding generation (synchronous)
# ---------------------------------------------------------------------------


def generate_embedding(text: str) -> list[float]:
    """Return a single embedding vector for *text* using text-embedding-3-small.

    Raises openai.OpenAIError on API failure.
    """
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(input=text, model=EMBEDDING_MODEL)
    return response.data[0].embedding


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Return one embedding vector per item in *texts* (single batched API call).

    Returns an empty list when *texts* is empty.
    Raises openai.OpenAIError on API failure.
    """
    if not texts:
        return []
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(input=texts, model=EMBEDDING_MODEL)
    # The API preserves input order but sort defensively.
    ordered = sorted(response.data, key=lambda item: item.index)
    return [item.embedding for item in ordered]


# ---------------------------------------------------------------------------
# Embedding generation (asynchronous — use inside FastAPI async endpoints)
# ---------------------------------------------------------------------------


async def generate_embedding_async(text: str) -> list[float]:
    """Async variant of generate_embedding."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.embeddings.create(input=text, model=EMBEDDING_MODEL)
    return response.data[0].embedding


async def generate_embeddings_async(texts: list[str]) -> list[list[float]]:
    """Async variant of generate_embeddings (single batched API call)."""
    if not texts:
        return []
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.embeddings.create(input=texts, model=EMBEDDING_MODEL)
    ordered = sorted(response.data, key=lambda item: item.index)
    return [item.embedding for item in ordered]
