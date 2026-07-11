"""Pydantic schemas and the SQLAlchemy `JobMatch` model.

A `JobMatch` is one of the exactly-three Career Recommendation Agent outputs
persisted for a resume: it links a `Resume` to a `JobDescription` retrieved
via RAG, together with the agent's match percentage, reasoning, missing
skills, confidence, and career overview for that specific pairing.

`JobDescription.parsed_text` is intentionally left untouched by this
milestone (see `app.models.job_description`) so the Job Simulation Agent can
load the full JD text by `job_description_id` without re-parsing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

ConfidenceScore = Literal["High", "Medium", "Low"]
MatchPercent = Annotated[int, Field(ge=0, le=100)]
Rank = Annotated[int, Field(ge=1, le=3)]


class CareerMatchRecommendation(BaseModel):
    """One recommendation as returned by the Career Recommendation Agent (raw AI output).

    `job_description_id` stays a string here because that's how RAG metadata
    (`app.rag.retriever`) represents ids — the service layer casts it to an
    `int` when persisting a `JobMatch` row.
    """

    job_description_id: str = Field(
        description="Id of the retrieved JobDescription this recommendation is grounded in."
    )
    role_title: str = Field(min_length=1, description="Job title for this recommendation.")
    match_percent: MatchPercent = Field(description="Resume-to-JD match, 0-100.")
    confidence_score: ConfidenceScore = Field(description="'High', 'Medium', or 'Low'.")
    reasoning: str = Field(min_length=1, description="2-4 sentences explaining the match.")
    career_overview: str = Field(min_length=1, description="2-3 sentences describing the role.")
    missing_skills: list[str] = Field(
        default_factory=list,
        description="Technical/professional skills missing for this specific JD.",
    )
    rank: Rank = Field(description="1, 2, or 3 — best match first.")


class CareerAdvisorAgentResponse(BaseModel):
    """Top-level JSON contract the Career Recommendation Agent must return."""

    matches: list[CareerMatchRecommendation] = Field(min_length=3, max_length=3)

    @field_validator("matches")
    @classmethod
    def _ranks_and_jds_are_unique(
        cls, matches: list[CareerMatchRecommendation]
    ) -> list[CareerMatchRecommendation]:
        ranks = sorted(match.rank for match in matches)
        if ranks != [1, 2, 3]:
            raise ValueError(f"matches must have ranks exactly [1, 2, 3], got {ranks}.")

        jd_ids = [match.job_description_id for match in matches]
        if len(set(jd_ids)) != len(jd_ids):
            raise ValueError(f"matches must reference distinct job descriptions, got {jd_ids}.")

        return matches


class JobMatch(Base):
    """A persisted Career Recommendation Agent output tied to one resume + one JD."""

    __tablename__ = "job_matches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id"), nullable=False, index=True
    )
    job_description_id: Mapped[int] = mapped_column(
        ForeignKey("job_descriptions.id"), nullable=False, index=True
    )
    role_title: Mapped[str] = mapped_column(String(255), nullable=False)
    match_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_score: Mapped[str] = mapped_column(String(16), nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    career_overview: Mapped[str] = mapped_column(Text, nullable=False)
    missing_skills: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    is_chosen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class JobMatchRecord(BaseModel):
    """Read-model for a persisted `JobMatch` row — returned by the job-matches API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    resume_id: int
    job_description_id: int
    role_title: str
    match_percent: MatchPercent
    confidence_score: ConfidenceScore
    reasoning: str
    career_overview: str
    missing_skills: list[str]
    rank: Rank
    is_chosen: bool
    created_at: datetime


class JobMatchListResponse(BaseModel):
    """Returned by `POST /job-matches/{resume_id}` — always exactly three matches."""

    matches: list[JobMatchRecord] = Field(min_length=3, max_length=3)
