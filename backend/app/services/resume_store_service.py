"""Persistence for `Resume` records.

This module does not duplicate upload or parsing logic — it calls
`app.services.resume_service.save_resume_upload` and
`app.services.resume_parser.parse_resume` exactly as they already exist and
simply persists their combined output as a `Resume` row. This is the piece
that was missing for a resume to have a stable id that
`POST /resumes/{id}/review` can load.
"""

from __future__ import annotations

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.resume import ParsedResume, Resume
from app.services import resume_service
from app.services.resume_parser import parse_resume


async def ingest_resume(db: Session, file: UploadFile, user_id: int | None = None) -> Resume:
    """Validate, store, and parse a resume PDF, then persist it with an id.

    Raises
    ------
    resume_service.InvalidResumeError
        The upload failed PDF validation (see `resume_service.save_resume_upload`).
    app.services.resume_parser.ResumeParseError
        The stored PDF could not be opened or contained no extractable text.
    """
    upload = await resume_service.save_resume_upload(file)
    parsed = parse_resume(upload.file_path)

    resume = Resume(
        user_id=user_id,
        file_name=upload.file_name,
        file_path=upload.file_path,
        parsed_resume=parsed.model_dump(),
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def get_resume_by_id(db: Session, resume_id: int) -> Resume | None:
    """Fetch a persisted resume by its primary key, or `None` if it doesn't exist."""
    return db.query(Resume).filter(Resume.id == resume_id).first()


def get_parsed_resume(resume: Resume) -> ParsedResume:
    """Rehydrate the stored `parsed_resume` JSON column back into a `ParsedResume`."""
    return ParsedResume.model_validate(resume.parsed_resume)
