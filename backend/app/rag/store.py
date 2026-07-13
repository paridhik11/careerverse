"""ChromaDB service — persistent vector storage for job description chunks.

All JD chunks are stored in a single ChromaDB collection named
``job_descriptions``.  The collection lives on disk under the path configured
by ``settings.chroma_persist_dir`` (default: ``../vector_db``).

Public API
----------
get_collection()                          – get or create the collection
add_documents(chunks, embeddings)         – store pre-embedded chunks
delete_documents(job_description_id)      – remove all chunks for a JD
query(query_embedding, n_results)         – similarity search
index_job_description(...)                – convenience: chunk → embed → store

Exceptions
----------
ChromaDBError       – base error for any ChromaDB operation failure
EmptyCollectionError – raised by query() when the collection has no documents
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "job_descriptions"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_persist_dir() -> str:
    """Return the absolute path to the ChromaDB persistence directory."""
    persist_path = Path(settings.chroma_persist_dir)
    if not persist_path.is_absolute():
        persist_path = Path.cwd() / persist_path
    persist_path.mkdir(parents=True, exist_ok=True)
    return str(persist_path.resolve())


def _get_client() -> chromadb.PersistentClient:
    """Instantiate a ChromaDB persistent client pointing at the configured directory."""
    return chromadb.PersistentClient(
        path=_resolve_persist_dir(),
        settings=ChromaSettings(anonymized_telemetry=False),
    )


# ---------------------------------------------------------------------------
# Public CRUD functions
# ---------------------------------------------------------------------------


def get_collection() -> chromadb.Collection:
    """Return (or create) the ``job_descriptions`` ChromaDB collection.

    The collection uses cosine similarity so distance scores are in [0, 2];
    lower = more similar.

    Raises ChromaDBError on any failure.
    """
    try:
        client = _get_client()
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        return collection
    except ChromaDBError:
        raise
    except Exception as exc:
        logger.exception("Failed to get or create ChromaDB collection: %s", exc)
        raise ChromaDBError(f"Could not access ChromaDB collection: {exc}") from exc


def add_documents(
    chunks: list[dict[str, Any]],
    embeddings: list[list[float]],
) -> None:
    """Store pre-embedded *chunks* in ChromaDB.

    Parameters
    ----------
    chunks:
        Output of ``embeddings.chunk_text()``.  Each dict must have keys
        ``text`` (the chunk body) and ``metadata`` (job_description_id,
        filename, role_title, chunk_index, source_type).
    embeddings:
        One embedding vector per chunk, in the same order.

    Uses ``upsert`` so re-indexing the same JD does not raise a duplicate-id
    error — it simply overwrites the existing vectors.

    Raises ChromaDBError on failure.
    """
    if not chunks:
        return
    if len(chunks) != len(embeddings):
        raise ChromaDBError(
            f"Chunk / embedding count mismatch: {len(chunks)} chunks, "
            f"{len(embeddings)} embeddings."
        )

    try:
        collection = get_collection()

        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        # Deterministic ids: "<jd_id>_chunk_<index>"
        ids = [
            f"{c['metadata']['job_description_id']}_chunk_{c['metadata']['chunk_index']}"
            for c in chunks
        ]

        # upsert handles duplicate uploads gracefully.
        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info("Upserted %d chunks into ChromaDB (collection=%s).", len(chunks), COLLECTION_NAME)
    except ChromaDBError:
        raise
    except Exception as exc:
        logger.exception("Failed to add documents to ChromaDB: %s", exc)
        raise ChromaDBError(f"Could not store documents in ChromaDB: {exc}") from exc


def delete_documents(job_description_id: str | int) -> None:
    """Remove all chunks that belong to *job_description_id* from ChromaDB.

    Safe to call even when no chunks exist for that id (no-op).

    Raises ChromaDBError on failure.
    """
    jd_id = str(job_description_id)
    try:
        collection = get_collection()
        collection.delete(where={"job_description_id": jd_id})
        logger.info("Deleted ChromaDB chunks for job_description_id=%s.", jd_id)
    except ChromaDBError:
        raise
    except Exception as exc:
        logger.exception("Failed to delete ChromaDB documents: %s", exc)
        raise ChromaDBError(
            f"Could not delete documents for jd_id={jd_id}: {exc}"
        ) from exc


def query(
    query_embedding: list[float],
    n_results: int = 8,
) -> dict[str, Any]:
    """Cosine-similarity search against the job_descriptions collection.

    Parameters
    ----------
    query_embedding:
        Embedding vector for the query (e.g. resume text).
    n_results:
        Maximum number of chunks to return.

    Returns
    -------
    Raw ChromaDB result dict with keys: ``ids``, ``documents``,
    ``metadatas``, ``distances``.

    Raises EmptyCollectionError when the collection has no documents.
    Raises ChromaDBError on any other failure.
    """
    try:
        collection = get_collection()
        count = collection.count()
        if count == 0:
            raise EmptyCollectionError(
                "ChromaDB collection is empty — upload job descriptions first."
            )
        safe_n = min(n_results, count)
        return collection.query(
            query_embeddings=[query_embedding],
            n_results=safe_n,
            include=["documents", "metadatas", "distances"],
        )
    except (ChromaDBError, EmptyCollectionError):
        raise
    except Exception as exc:
        logger.exception("ChromaDB query failed: %s", exc)
        raise ChromaDBError(f"ChromaDB query failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Convenience: full indexing pipeline (chunk → embed → store)
# ---------------------------------------------------------------------------


def index_job_description(
    job_description_id: str | int,
    filename: str,
    role_title: str,
    parsed_text: str,
) -> int:
    """Chunk, embed, and store a job description in ChromaDB.

    This is the single call the upload service should make after persisting a
    JobDescription DB record.

    Returns the number of chunks indexed.
    Raises ChromaDBError on storage failure.
    Raises google.genai.errors.APIError on embedding failure.
    """
    # Import here to avoid a circular dependency at module load time.
    from app.rag.embeddings import chunk_text, generate_embeddings

    chunks = chunk_text(
        parsed_text,
        job_description_id=job_description_id,
        filename=filename,
        role_title=role_title,
    )
    if not chunks:
        logger.warning(
            "No chunks produced for job_description_id=%s — skipping indexing.",
            job_description_id,
        )
        return 0

    texts = [c["text"] for c in chunks]
    embeddings = generate_embeddings(texts)
    add_documents(chunks, embeddings)
    return len(chunks)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ChromaDBError(Exception):
    """Raised when a ChromaDB operation fails."""


class EmptyCollectionError(ChromaDBError):
    """Raised when the collection contains no documents to query."""
