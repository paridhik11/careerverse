"""Pydantic schemas and the SQLAlchemy `SkillGap` model.

A `SkillGap` stores the Skill Gap Analysis Agent's output for the single
career the user has chosen after completing the Virtual Work Experience.

The analysis is always grounded in:
  - The user's resume text.
  - The full parsed text of the selected Job Description (the JD is the
    primary source of truth — skills are only reported when they appear in
    the uploaded JD, never hallucinated).
  - Optionally, simulation metadata from the completed VWE (passed when
    available to enrich the readiness score and recommendations).

Only one career is ever analysed per call — the chosen `JobMatch`. The
analysis is NEVER run against the other two recommendations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

ReadinessScore = Annotated[int, Field(ge=0, le=100)]


# ---------------------------------------------------------------------------
# SQLAlchemy ORM model
# ---------------------------------------------------------------------------


class SkillGap(Base):
    """Persisted Skill Gap Analysis for one resume + one chosen JobMatch.

    `existing_skills`, `missing_technical_skills`, `missing_soft_skills`,
    and `recommended_next_steps` are JSON arrays of strings validated by
    the Pydantic `SkillGapContent` model before persistence.

    `readiness_score` is an integer 0–100. `summary` is a short narrative
    paragraph contextualising the score.
    """

    __tablename__ = "skill_gaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    resume_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("resumes.id"), nullable=False, index=True
    )
    job_match_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job_matches.id"), nullable=False, index=True
    )
    existing_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    missing_technical_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    missing_soft_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    recommended_next_steps: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    readiness_score: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Agent output schema — validated before the DB is touched
# ---------------------------------------------------------------------------


class SkillGapContent(BaseModel):
    """Structured output contract the Skill Gap Agent must satisfy.

    Every field is grounded in the uploaded Job Description — the agent is
    instructed never to report skills that are not explicitly mentioned in
    the JD text. Pydantic validates this schema at the agent boundary; any
    deviation is rejected before persistence.

    Fields
    ------
    readiness_score:
        0–100 integer. Reflects how closely the resume's skills and
        experience match the requirements of the selected JD. Simulation
        performance nudges this score up or down when provided.
    summary:
        1–3 sentence narrative contextualising the score: what the user
        already demonstrates, what the main gaps are, and overall career
        readiness outlook.
    existing_skills:
        Skills, tools, or competencies explicitly present in both the
        resume and the selected JD. Each item is a concise string.
    missing_technical_skills:
        Technical skills, tools, or technologies required by the JD that
        are absent or insufficiently demonstrated in the resume.
    missing_soft_skills:
        Soft skills or professional behaviours required by the JD that are
        absent or insufficiently demonstrated in the resume.
    recommended_next_steps:
        Prioritised, actionable steps the user should take to close the
        most important gaps. Ordered from highest to lowest impact.
    """

    readiness_score: ReadinessScore
    summary: str = Field(min_length=1)
    existing_skills: list[str] = Field(min_length=1)
    missing_technical_skills: list[str] = Field(min_length=0, default_factory=list)
    missing_soft_skills: list[str] = Field(min_length=0, default_factory=list)
    recommended_next_steps: list[str] = Field(min_length=1)


# ---------------------------------------------------------------------------
# API read model — returned to the frontend
# ---------------------------------------------------------------------------


class SkillGapRecord(BaseModel):
    """Read model for a persisted `SkillGap` row — returned by the API.

    Constructed from an ORM instance via `from_orm_row()`.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    resume_id: int
    job_match_id: int
    readiness_score: ReadinessScore
    summary: str
    existing_skills: list[str]
    missing_technical_skills: list[str]
    missing_soft_skills: list[str]
    recommended_next_steps: list[str]
    created_at: datetime

    @classmethod
    def from_orm_row(cls, row: "SkillGap") -> "SkillGapRecord":
        """Construct a `SkillGapRecord` from a `SkillGap` ORM instance."""
        return cls(
            id=row.id,
            resume_id=row.resume_id,
            job_match_id=row.job_match_id,
            readiness_score=row.readiness_score,
            summary=row.summary,
            existing_skills=row.existing_skills,
            missing_technical_skills=row.missing_technical_skills,
            missing_soft_skills=row.missing_soft_skills,
            recommended_next_steps=row.recommended_next_steps,
            created_at=row.created_at,
        )


class SkillGapResponse(BaseModel):
    """Top-level response returned by `POST /skill-gap/{resume_id}`."""

    skill_gap: SkillGapRecord
