"""Pydantic schemas and the SQLAlchemy `LearningRoadmap` model.

A `LearningRoadmap` stores the 3-Month Learning Roadmap Agent's output for
the single career the user has chosen after completing the Skill Gap Analysis.

The roadmap is always grounded in:
  - The user's resume text.
  - The full parsed text of the selected Job Description (primary source of truth).
  - The Skill Gap Analysis for the chosen career (existing skills, missing
    skills, and readiness score drive the month-by-month progression).

Only one career is ever processed per call — the chosen `JobMatch`. The roadmap
is NEVER generated for the other two recommendations.

Month 1 covers foundations, Month 2 builds intermediate competency, Month 3
focuses on job readiness and portfolio preparation.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import JSON, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ---------------------------------------------------------------------------
# SQLAlchemy ORM model
# ---------------------------------------------------------------------------


class LearningRoadmap(Base):
    """Persisted 3-Month Learning Roadmap for one resume + one chosen JobMatch.

    `roadmap_json` stores the full validated `RoadmapContent` dict so the
    frontend can receive all three months in a single round-trip.
    """

    __tablename__ = "learning_roadmaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    resume_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("resumes.id"), nullable=False, index=True
    )
    job_match_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job_matches.id"), nullable=False, index=True
    )
    roadmap_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Agent output sub-schemas
# ---------------------------------------------------------------------------


class MonthPlan(BaseModel):
    """One month's learning plan — validated before the DB is touched.

    Every field is grounded in the uploaded Job Description and the Skill Gap
    Analysis. The agent is instructed never to hallucinate resources or topics
    that are not relevant to the identified skill gaps.

    Fields
    ------
    focus:
        A single sentence describing the overarching theme for this month
        (e.g. "Build Python and SQL foundations required by the JD").
    topics:
        Ordered list of 3–6 concrete topics or skills to study, each a
        concise string drawn from the JD or skill gap.
    projects:
        1–3 practical projects the learner should build to demonstrate
        the month's topics. Each item describes a concrete deliverable.
    resources:
        Curated list of 3–5 free or widely available learning resources
        (courses, documentation, books, YouTube channels). Each entry is a
        concise "Resource Name — URL or platform" string.
    milestones:
        2–4 verifiable checkpoints that confirm the month's goals have been
        met (e.g. "Can write SQL JOINs without reference material").
    """

    focus: str = Field(min_length=1)
    topics: list[str] = Field(min_length=1)
    projects: list[str] = Field(min_length=1)
    resources: list[str] = Field(min_length=1)
    milestones: list[str] = Field(min_length=1)


class RoadmapContent(BaseModel):
    """Structured output contract the Learning Roadmap Agent must satisfy.

    Three months of progressive learning: foundations → intermediate → job ready.
    Validated at the agent boundary; any schema deviation is rejected before
    persistence.
    """

    month_1: MonthPlan
    month_2: MonthPlan
    month_3: MonthPlan


# ---------------------------------------------------------------------------
# API read model — returned to the frontend
# ---------------------------------------------------------------------------


class LearningRoadmapRecord(BaseModel):
    """Read model for a persisted `LearningRoadmap` row — returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    resume_id: int
    job_match_id: int
    roadmap: RoadmapContent
    created_at: datetime

    @classmethod
    def from_orm_row(cls, row: "LearningRoadmap") -> "LearningRoadmapRecord":
        """Construct a `LearningRoadmapRecord` from a `LearningRoadmap` ORM instance."""
        return cls(
            id=row.id,
            resume_id=row.resume_id,
            job_match_id=row.job_match_id,
            roadmap=RoadmapContent.model_validate(row.roadmap_json),
            created_at=row.created_at,
        )


class LearningRoadmapResponse(BaseModel):
    """Top-level response returned by `POST /learning-roadmap/{resume_id}`."""

    roadmap: LearningRoadmapRecord
