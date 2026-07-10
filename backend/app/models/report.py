"""Pydantic schema and SQLAlchemy model for AI-generated reports.

A `Report` is a persisted, structured AI output tied to a resume. The table
is intentionally generic (`report_type` + JSON `content`) rather than one
table per agent, so later milestones (career recommendation, skill gap,
roadmap) can reuse it instead of duplicating storage plumbing — the Resume
Reviewer Agent is simply the first writer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

RESUME_REVIEW_REPORT_TYPE = "resume_review"

Score = Annotated[int, Field(ge=0, le=100)]


class ResumeReviewReport(BaseModel):
    """Structured output of the Resume Reviewer Agent.

    Field names and shapes match the CareerVerse Resume Reviewer milestone
    spec exactly. The API returns this model as-is (no wrapper envelope) so
    the JSON contract stays stable for the frontend and for any future agent
    that reuses this report.
    """

    overall_score: Score = Field(description="Overall resume quality, 0-100.")
    ats_score: Score = Field(description="ATS compatibility score, 0-100.")
    summary: str = Field(min_length=1, description="2-4 sentence overview of the resume.")
    strengths: list[str] = Field(min_length=3, max_length=6, description="3-6 strengths.")
    weaknesses: list[str] = Field(min_length=3, max_length=6, description="3-6 weaknesses.")
    ats_issues: list[str] = Field(default_factory=list, description="ATS-related problems found.")
    suggestions: list[str] = Field(default_factory=list, description="Actionable improvements.")
    recommended_roles: list[str] = Field(
        min_length=3,
        max_length=5,
        description="3-5 preliminary career directions based only on the resume.",
    )


class Report(Base):
    """A persisted AI-generated report tied to a resume."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id"), nullable=False, index=True
    )
    report_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ReportRecord(BaseModel):
    """Read-model for a persisted Report row (internal use, e.g. future list endpoints)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    resume_id: int
    report_type: str
    created_at: datetime
