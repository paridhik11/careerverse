"""Pydantic schemas and the SQLAlchemy `Resume` model.



Upload stores the PDF on disk. Parsing extracts structured fields with

heuristics only — no AI analysis in this milestone.

The `Resume` ORM model below was added in the Resume Reviewer Agent milestone.

It does not change how upload or parsing work (`app.services.resume_service`

and `app.services.resume_parser` are untouched) — it only gives a parsed

resume a stable database id, which downstream agents (starting with the

Resume Reviewer Agent) need in order to load a resume by id instead of

re-parsing a file path on every call.

"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base





class ResumeUploadResponse(BaseModel):

    """Returned after a resume PDF is successfully written to uploads/."""



    file_name: str = Field(description="Original filename as provided by the client.")

    file_path: str = Field(description="Absolute path where the file was stored.")

    status: str = Field(description="Upload status, e.g. 'uploaded'.")





class ParsedResume(BaseModel):

    """Structured fields extracted from a resume PDF (no scoring or analysis)."""



    full_text: str = Field(description="All text extracted from the PDF via PyMuPDF.")

    name: str | None = Field(

        default=None,

        description="Best-effort candidate name from the header lines.",

    )

    email: str | None = Field(default=None, description="First email address found.")

    phone: str | None = Field(default=None, description="First phone number found.")

    skills: str = Field(

        default="",

        description="Raw text under the Skills (or equivalent) section heading.",

    )

    education: str = Field(

        default="",

        description="Raw text under the Education section heading.",

    )

    experience: str = Field(

        default="",

        description="Raw text under the Experience / Work History section heading.",

    )

    projects: str = Field(

        default="",

        description="Raw text under the Projects section heading.",

    )


class Resume(Base):
    """A persisted resume: upload metadata + parsed content.

    Populated by `app.services.resume_store_service.ingest_resume`, which
    calls the existing upload and parsing services and stores their output
    here so it can be looked up by id (e.g. for `POST /resumes/{id}/review`).

    `file_hash` is the SHA-256 hex digest of the raw PDF bytes.  It enables
    hash-based deduplication: if the same PDF is uploaded again, the existing
    resume row (and its cached AI review) can be reused instead of re-running
    Gemini.
    """

    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    # SHA-256 hex digest of the raw PDF — enables cache lookups.
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # Stores a `ParsedResume.model_dump()` dict — see `get_parsed_resume`.
    parsed_resume: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ResumeRecordResponse(BaseModel):
    """Returned after a resume is uploaded, parsed, and persisted with an id."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    parsed_resume: ParsedResume
    status: str = "parsed"
