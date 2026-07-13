"""High-level RAG retrieval: resume text → relevant JD chunks, grouped by JD.

No LLM calls are made here.  This module only retrieves context; downstream
agents are responsible for reasoning over it.

Public API
----------
retrieve_relevant_job_descriptions(resume_text, top_k=8)
    → list[{job_description_id, role_title, chunks}]

Return format
-------------
[
    {
        "job_description_id": "42",
        "role_title": "Software Engineer",
        "chunks": [
            "We are looking for a Software Engineer ...",
            "Requirements: Python, FastAPI, PostgreSQL ..."
        ]
    },
    ...
]

Exceptions
----------
EmbeddingError  – raised when the Gemini embedding call for the resume fails.
ChromaDBError   – propagated from store.query() on database failure.
"""

from __future__ import annotations

import logging
from typing import Any

from app.rag.embeddings import generate_embedding
from app.rag.store import ChromaDBError, EmptyCollectionError, query

logger = logging.getLogger(__name__)


def retrieve_relevant_job_descriptions(
    resume_text: str,
    top_k: int = 8,
) -> list[dict[str, Any]]:
    """Retrieve the most relevant JD chunks for the given resume text.

    Steps
    -----
    1. Generate an embedding for the full resume text.
    2. Query ChromaDB for the top-*top_k* most similar chunks.
    3. Group returned chunks by ``job_description_id``.
    4. Return one result entry per unique JD, ordered by first appearance
       (i.e. the JD whose first chunk ranked highest appears first).

    Parameters
    ----------
    resume_text:
        Full parsed text of the user's resume.
    top_k:
        Maximum number of chunks to retrieve before grouping.
        Defaults to 8 so that up to ~3–4 distinct JDs are represented.

    Returns
    -------
    list of dicts — empty list when the collection has no documents.

    Raises
    ------
    EmbeddingError  – when the Gemini call fails.
    ChromaDBError   – when the ChromaDB query fails (not including empty collection).
    """
    if not resume_text or not resume_text.strip():
        logger.warning("retrieve_relevant_job_descriptions called with empty resume text.")
        return []

    # Step 1 — embed the resume.
    try:
        resume_embedding = generate_embedding(resume_text)
    except Exception as exc:
        logger.exception("Failed to generate embedding for resume: %s", exc)
        raise EmbeddingError(f"Could not generate resume embedding: {exc}") from exc

    # Step 2 — query ChromaDB.
    try:
        results = query(resume_embedding, n_results=top_k)
    except EmptyCollectionError:
        logger.info("ChromaDB collection is empty — returning no results.")
        return []
    except ChromaDBError:
        raise

    # Step 3 & 4 — group chunks by JD, preserving relevance order.
    grouped: dict[str, dict[str, Any]] = {}

    documents: list[str] = results.get("documents", [[]])[0]
    metadatas: list[dict[str, Any]] = results.get("metadatas", [[]])[0]

    for doc, meta in zip(documents, metadatas):
        jd_id = str(meta.get("job_description_id", "unknown"))
        if jd_id not in grouped:
            grouped[jd_id] = {
                "job_description_id": jd_id,
                "role_title": meta.get("role_title", ""),
                "chunks": [],
            }
        grouped[jd_id]["chunks"].append(doc)

    logger.info(
        "RAG retrieval complete: %d chunks → %d unique JDs.",
        len(documents),
        len(grouped),
    )
    return list(grouped.values())


class EmbeddingError(Exception):
    """Raised when the Gemini embedding call fails during retrieval."""
