"""Persistence for `Resume` records.

This module does not duplicate upload or parsing logic — it calls
`app.services.resume_service.save_resume_upload` and
`app.services.resume_parser.parse_resume` exactly as they already exist and
simply persists their combined output as a `Resume` row.

Hash-based deduplication
------------------------
Every ingested resume now stores a SHA-256 hex digest of the raw PDF bytes in
the `file_hash` column.  `get_resume_by_hash` lets callers check whether an
identical PDF was already uploaded (and therefore whether a cached AI review
already exists) before calling Gemini again.
"""

from __future__ import annotations

import hashlib

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.resume import ParsedResume, Resume
from app.services import resume_service
from app.services.resume_parser import parse_resume


def _sha256_hex(data: bytes) -> str:
    """Return the SHA-256 hex digest of `data`."""
    return hashlib.sha256(data).hexdigest()


async def ingest_resume(db: Session, file: UploadFile, user_id: int | None = None) -> Resume:
    """Validate, store, and parse a resume PDF, then persist it with an id.

    Computes a SHA-256 hash of the raw PDF bytes and stores it in the
    `file_hash` column so identical uploads can be detected by callers.

    Raises
    ------
    resume_service.InvalidResumeError
        The upload failed PDF validation (see `resume_service.save_resume_upload`).
    app.services.resume_parser.ResumeParseError
        The stored PDF could not be opened or contained no extractable text.
    """
    # Read raw bytes for hashing BEFORE saving (UploadFile is a stream).
    raw_bytes = await file.read()
    file_hash = _sha256_hex(raw_bytes)

    # Reset the stream so save_resume_upload can read it again.
    await file.seek(0)

    upload = await resume_service.save_resume_upload(file)
    parsed = parse_resume(upload.file_path)

    resume = Resume(
        user_id=user_id,
        file_name=upload.file_name,
        file_path=upload.file_path,
        file_hash=file_hash,
        parsed_resume=parsed.model_dump(),
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def get_resume_by_id(db: Session, resume_id: int) -> Resume | None:
    """Fetch a persisted resume by its primary key, or `None` if it doesn't exist."""
    return db.query(Resume).filter(Resume.id == resume_id).first()


def get_resume_by_hash(db: Session, file_hash: str, user_id: int | None = None) -> Resume | None:
    """Find the most-recently-uploaded resume with the given SHA-256 hash.

    If `user_id` is provided, the lookup is scoped to that user.  Returns
    `None` when no matching resume exists.
    """
    query = db.query(Resume).filter(Resume.file_hash == file_hash)
    if user_id is not None:
        query = query.filter(Resume.user_id == user_id)
    return query.order_by(Resume.created_at.desc()).first()


def get_parsed_resume(resume: Resume) -> ParsedResume:
    """Rehydrate the stored `parsed_resume` JSON column back into a `ParsedResume`."""
    return ParsedResume.model_validate(resume.parsed_resume)
