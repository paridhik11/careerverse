"""Pydantic schemas and the SQLAlchemy `JobDescription` model.

Upload stores the original PDF/TXT on disk and persists extracted text so the
RAG pipeline (later milestone) can load JDs by id without re-parsing files.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class JobDescription(Base):
    """A persisted job description: original file metadata + extracted text."""

    __tablename__ = "job_descriptions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(16), nullable=False)  # "pdf" | "txt"
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    role_title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    parsed_text: Mapped[str] = mapped_column(Text, nullable=False)
    # SHA-256 of raw file bytes — used only for duplicate detection, not exposed in API.
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class JobDescriptionUploadItem(BaseModel):
    """One successfully uploaded job description in the batch response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Database id of the saved JobDescription, as a string.")
    filename: str = Field(description="Original filename as provided by the client.")
    role_title: str = Field(description="Best-effort role title from filename or content.")
    status: str = Field(description="Upload status, e.g. 'success'.")


class JobDescriptionUploadResponse(BaseModel):
    """Returned after one or more job description files are uploaded."""

    uploaded: list[JobDescriptionUploadItem]


class SampleJobDescriptionItem(BaseModel):
    """One pre-seeded sample JD available for the dashboard picker."""

    id: str = Field(description="Stable fixture id, e.g. 'software-engineer'.")
    role_title: str
    category: str
    summary: str


class SampleJobDescriptionListResponse(BaseModel):
    samples: list[SampleJobDescriptionItem]


class SeedSampleJobDescriptionsRequest(BaseModel):
    sample_ids: list[str] = Field(
        min_length=1,
        description="Fixture ids to persist + index into ChromaDB.",
    )
