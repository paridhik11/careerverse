"""Business logic for job description file uploads.

Validates PDF/TXT payloads, extracts text via `job_description_parser`, stores
the original file under uploads/, persists a `JobDescription` row, and indexes
the parsed text into ChromaDB via the RAG pipeline.
"""

from __future__ import annotations

import hashlib
import logging
import re
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.job_description import (
    JobDescription,
    JobDescriptionUploadItem,
    JobDescriptionUploadResponse,
)
from app.services.job_description_parser import (
    JobDescriptionParseError,
    extract_role_title,
    extract_text,
)

logger = logging.getLogger(__name__)

PDF_MAGIC = b"%PDF"
SUPPORTED_EXTENSIONS = {".pdf", ".txt"}
MAX_JD_BYTES = 10 * 1024 * 1024  # 10 MB — same ceiling as resume uploads


class InvalidJobDescriptionError(Exception):
    """Raised when an uploaded JD fails validation or cannot be stored."""


def _resolve_upload_dir() -> Path:
    """Return the job-descriptions uploads directory, creating it if needed."""
    upload_dir = Path(settings.upload_dir)
    if not upload_dir.is_absolute():
        upload_dir = Path.cwd() / upload_dir
    jd_dir = upload_dir / "job_descriptions"
    jd_dir.mkdir(parents=True, exist_ok=True)
    return jd_dir.resolve()


def _sanitize_filename(filename: str) -> str:
    """Strip path components and keep a safe basename for disk storage."""
    name = Path(filename).name.strip()
    safe = re.sub(r"[^\w.\-]+", "_", name, flags=re.UNICODE)
    return safe or "job_description"


def _detect_file_type(filename: str | None, header: bytes) -> str:
    """Detect `pdf` or `txt` from extension (+ PDF magic). Raises if unsupported."""
    if not filename or not filename.strip():
        raise InvalidJobDescriptionError("A file name is required.")

    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise InvalidJobDescriptionError(
            f"Unsupported file type for '{Path(filename).name}'. "
            "Only PDF (.pdf) and plain text (.txt) job descriptions are accepted."
        )

    if suffix == ".pdf":
        if not header.startswith(PDF_MAGIC):
            raise InvalidJobDescriptionError(
                f"'{Path(filename).name}' is not a valid PDF (missing PDF header)."
            )
        return "pdf"

    return "txt"


def _content_hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


async def _read_and_validate(file: UploadFile) -> tuple[str, str, bytes]:
    """Read one upload, validate type/size/emptiness, return (filename, file_type, bytes)."""
    original_name = Path(file.filename or "").name
    header = await file.read(8)
    file_type = _detect_file_type(file.filename, header)

    rest = await file.read()
    payload = header + rest

    if len(payload) == 0:
        raise InvalidJobDescriptionError(f"'{original_name}' is empty.")
    if len(payload) > MAX_JD_BYTES:
        raise InvalidJobDescriptionError(
            f"'{original_name}' must be {MAX_JD_BYTES // (1024 * 1024)} MB or smaller."
        )

    # TXT: reject if the body is only whitespace once decoded (parser also checks).
    if file_type == "txt" and not payload.strip():
        raise InvalidJobDescriptionError(f"'{original_name}' is empty.")

    return original_name, file_type, payload


def _store_file(original_name: str, file_type: str, payload: bytes) -> Path:
    """Write the original bytes under uploads/job_descriptions/ with a unique name."""
    safe = _sanitize_filename(original_name)
    stored_name = f"{uuid.uuid4().hex}_{safe}"
    expected_ext = f".{file_type}"
    if not stored_name.lower().endswith(expected_ext):
        stored_name = f"{stored_name}{expected_ext}"

    destination = _resolve_upload_dir() / stored_name
    try:
        destination.write_bytes(payload)
    except OSError as exc:
        raise InvalidJobDescriptionError(
            f"Could not store '{original_name}' on disk: {exc}"
        ) from exc
    return destination


def _ensure_not_duplicate(db: Session, digest: str, filename: str) -> None:
    existing = (
        db.query(JobDescription).filter(JobDescription.content_hash == digest).first()
    )
    if existing is not None:
        raise InvalidJobDescriptionError(
            f"Duplicate upload: '{filename}' matches an already stored job description "
            f"(id={existing.id})."
        )


async def save_job_description_uploads(
    db: Session,
    files: list[UploadFile],
) -> JobDescriptionUploadResponse:
    """Validate, parse, store, and persist one or more job description files.

    All files are validated and parsed before any DB commit so a bad file in a
    batch does not leave partial rows. Original files already written to disk
    for a failed batch are left in place (unique names); the client can retry.
    """
    if not files:
        raise InvalidJobDescriptionError("At least one job description file is required.")

    # FastAPI can pass a single UploadFile when the client sends one part;
    # normalize to a list for uniform handling.
    uploads = files if isinstance(files, list) else [files]

    prepared: list[tuple[str, str, bytes, str, str, Path]] = []
    # (filename, file_type, payload, parsed_text, role_title, destination)

    for file in uploads:
        original_name, file_type, payload = await _read_and_validate(file)
        digest = _content_hash(payload)
        _ensure_not_duplicate(db, digest, original_name)

        # Also reject duplicates within the same batch.
        for prior_name, _, prior_payload, *_ in prepared:
            if _content_hash(prior_payload) == digest:
                raise InvalidJobDescriptionError(
                    f"Duplicate upload in this request: '{original_name}' "
                    f"matches '{prior_name}'."
                )

        try:
            parsed_text = extract_text(payload, file_type)
        except JobDescriptionParseError as exc:
            raise InvalidJobDescriptionError(
                f"Failed to parse '{original_name}': {exc}"
            ) from exc

        if not parsed_text.strip():
            raise InvalidJobDescriptionError(
                f"'{original_name}' produced no extractable text."
            )

        role_title = extract_role_title(original_name, parsed_text)
        destination = _store_file(original_name, file_type, payload)
        prepared.append(
            (original_name, file_type, payload, parsed_text, role_title, destination)
        )

    items: list[JobDescriptionUploadItem] = []
    persisted: list[tuple[int, str, str, str]] = []
    # (record.id, original_name, role_title, parsed_text)

    try:
        for original_name, file_type, payload, parsed_text, role_title, destination in prepared:
            record = JobDescription(
                filename=original_name,
                file_type=file_type,
                file_path=str(destination),
                role_title=role_title,
                parsed_text=parsed_text,
                content_hash=_content_hash(payload),
            )
            db.add(record)
            db.flush()  # assign id before commit
            items.append(
                JobDescriptionUploadItem(
                    id=str(record.id),
                    filename=original_name,
                    role_title=role_title,
                    status="success",
                )
            )
            persisted.append((record.id, original_name, role_title, parsed_text))
        db.commit()
    except InvalidJobDescriptionError:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise InvalidJobDescriptionError(
            f"Could not save job description records: {exc}"
        ) from exc

    # Index into ChromaDB after a successful DB commit.
    # Indexing failure is non-fatal — the DB record is already saved and the
    # user can still use the upload; the JD just won't be retrievable via RAG
    # until a future re-index.
    _index_uploaded_job_descriptions(persisted)

    return JobDescriptionUploadResponse(uploaded=items)


def _index_uploaded_job_descriptions(
    records: list[tuple[int, str, str, str]],
) -> None:
    """Chunk, embed, and store each JD in ChromaDB.

    Parameters
    ----------
    records:
        List of (id, filename, role_title, parsed_text) tuples for the newly
        persisted JobDescription rows.
    """
    try:
        from app.rag.store import index_job_description
    except Exception as exc:  # pragma: no cover
        logger.warning("RAG module unavailable — skipping ChromaDB indexing: %s", exc)
        return

    for jd_id, filename, role_title, parsed_text in records:
        try:
            chunk_count = index_job_description(
                job_description_id=jd_id,
                filename=filename,
                role_title=role_title,
                parsed_text=parsed_text,
            )
            logger.info(
                "Indexed job_description_id=%s into ChromaDB (%d chunks).",
                jd_id,
                chunk_count,
            )
        except Exception as exc:
            logger.error(
                "Failed to index job_description_id=%s into ChromaDB: %s",
                jd_id,
                exc,
            )
