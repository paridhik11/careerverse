"""Business logic for the Learning Roadmap generation flow.

Per `.cursorrules`, all orchestration belongs here:
- `api/learning_roadmap.py` stays a thin HTTP layer.
- `agents/learning_plan.py` only knows how to call OpenAI.
- This service owns loading, skill gap serialisation, persistence, and error
  mapping.

Flow (see `generate_roadmap`):
1. Load the chosen `JobMatch` for the resume — fail fast if no career has
   been selected.
2. Load the full `JobDescription.parsed_text` — primary source of truth for
   role requirements.
3. Load the resume text.
4. Load the latest `SkillGap` row for the chosen match — required to drive the
   month-by-month progression. If no skill gap analysis has been run, raise
   a clear error so the frontend can direct the user to run it first.
5. Serialise the Skill Gap Analysis into a compact JSON string for the prompt.
6. Call the Learning Roadmap Agent.
7. Persist the validated `RoadmapContent` as a `LearningRoadmap` row.
8. Return the `LearningRoadmapRecord` read model.

Idempotency
-----------
Each call re-generates and re-persists the roadmap. For MVP this is acceptable
— the user is unlikely to call this endpoint multiple times, and the cost is a
single AI call. The latest row is always the most relevant.
"""

from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from app.agents import learning_plan as learning_plan_agent
from app.models.job_description import JobDescription
from app.models.job_match import JobMatch
from app.models.learning_roadmap import LearningRoadmap, LearningRoadmapRecord, RoadmapContent
from app.models.resume import Resume
from app.models.skill_gap import SkillGap
from app.services.resume_store_service import get_parsed_resume

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Typed exception hierarchy
# ---------------------------------------------------------------------------


class LearningRoadmapServiceError(Exception):
    """Base class for every error in the learning roadmap service layer."""


class NoChosenCareerError(LearningRoadmapServiceError):
    """The user has not yet chosen a career for this resume.

    `PATCH /job-matches/{job_match_id}/choose` must be called first.
    """


class JobDescriptionNotFoundError(LearningRoadmapServiceError):
    """The `JobDescription` linked to the chosen `JobMatch` is missing or has no text.

    Cannot produce a JD-grounded roadmap without the JD content.
    """


class SkillGapNotFoundError(LearningRoadmapServiceError):
    """No Skill Gap Analysis exists for the chosen career.

    `POST /skill-gap/{resume_id}` must be called before generating the roadmap.
    """


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_chosen_job_match(db: Session, resume_id: int) -> JobMatch:
    """Return the chosen `JobMatch` for a resume.

    Raises
    ------
    NoChosenCareerError
        No `JobMatch` with `is_chosen=True` exists for this resume.
    """
    chosen: JobMatch | None = (
        db.query(JobMatch)
        .filter(JobMatch.resume_id == resume_id, JobMatch.is_chosen.is_(True))
        .first()
    )
    if chosen is None:
        raise NoChosenCareerError(
            f"No career has been selected for resume_id={resume_id}. "
            f"Call PATCH /job-matches/{{job_match_id}}/choose first."
        )
    return chosen


def _load_jd_text(db: Session, job_description_id: int) -> str:
    """Return the full parsed text of a `JobDescription`.

    Raises
    ------
    JobDescriptionNotFoundError
        The JD does not exist or its `parsed_text` is empty.
    """
    jd: JobDescription | None = (
        db.query(JobDescription)
        .filter(JobDescription.id == job_description_id)
        .first()
    )
    if jd is None:
        raise JobDescriptionNotFoundError(
            f"JobDescription id={job_description_id} not found. "
            f"It may have been deleted after the career recommendation was generated."
        )
    if not jd.parsed_text or not jd.parsed_text.strip():
        raise JobDescriptionNotFoundError(
            f"JobDescription id={job_description_id} exists but has no parsed text. "
            f"Cannot produce a JD-grounded learning roadmap without JD content."
        )
    return jd.parsed_text


def _load_skill_gap(db: Session, resume_id: int, job_match_id: int) -> SkillGap:
    """Return the latest `SkillGap` for the chosen career.

    Raises
    ------
    SkillGapNotFoundError
        No `SkillGap` row exists for this resume + job_match combination.
    """
    skill_gap: SkillGap | None = (
        db.query(SkillGap)
        .filter(
            SkillGap.resume_id == resume_id,
            SkillGap.job_match_id == job_match_id,
        )
        .order_by(SkillGap.created_at.desc())
        .first()
    )
    if skill_gap is None:
        raise SkillGapNotFoundError(
            f"No Skill Gap Analysis found for resume_id={resume_id}, "
            f"job_match_id={job_match_id}. "
            f"Call POST /skill-gap/{resume_id} first."
        )
    return skill_gap


def _serialise_skill_gap(skill_gap: SkillGap, role_title: str) -> str:
    """Serialise the Skill Gap row into a compact JSON string for the prompt.

    The summary string gives the model everything it needs to build a
    month-by-month plan grounded in the actual gap analysis.
    """
    summary = {
        "role_title": role_title,
        "readiness_score": skill_gap.readiness_score,
        "skill_gap_summary": skill_gap.summary,
        "existing_skills": skill_gap.existing_skills,
        "missing_technical_skills": skill_gap.missing_technical_skills,
        "missing_soft_skills": skill_gap.missing_soft_skills,
        "recommended_next_steps": skill_gap.recommended_next_steps,
    }
    return json.dumps(summary, indent=2)


def _persist_roadmap(
    db: Session,
    resume_id: int,
    job_match_id: int,
    content: RoadmapContent,
) -> LearningRoadmap:
    """Save a validated `RoadmapContent` as a `LearningRoadmap` row.

    Commits in a single transaction and refreshes the row so the caller
    receives a fully populated ORM instance (with auto-generated `id` and
    `created_at`).
    """
    record = LearningRoadmap(
        resume_id=resume_id,
        job_match_id=job_match_id,
        roadmap_json=content.model_dump(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


async def generate_roadmap(
    db: Session,
    resume: Resume,
) -> LearningRoadmapRecord:
    """Run the full Learning Roadmap generation flow for the user's chosen career.

    Parameters
    ----------
    db:
        Synchronous SQLAlchemy session provided by the FastAPI dependency.
    resume:
        The `Resume` ORM instance whose chosen career is being processed.

    Returns
    -------
    LearningRoadmapRecord
        A fully populated read model containing the 3-month roadmap with
        focus, topics, projects, resources, and milestones for each month.

    Raises
    ------
    NoChosenCareerError
        The user has not yet selected a career for this resume.
    JobDescriptionNotFoundError
        The chosen career's Job Description is missing or has no parsed text.
    SkillGapNotFoundError
        No Skill Gap Analysis has been run for the chosen career.
    learning_plan_agent.InvalidLearningPlanResponseError
        GPT-4o returned a response that could not be parsed or validated.
    learning_plan_agent.OpenAIRequestError
        The OpenAI API call failed.
    learning_plan_agent.LearningPlanAgentTimeoutError
        The OpenAI API call timed out.
    """
    # Step 1: load the chosen career — fail fast if none is selected.
    chosen_match = _load_chosen_job_match(db, resume.id)

    logger.info(
        "Learning Roadmap Service: generating roadmap for resume_id=%s, "
        "job_match_id=%s (role='%s').",
        resume.id,
        chosen_match.id,
        chosen_match.role_title,
    )

    # Step 2: load the full JD text — the primary source of truth.
    jd_text = _load_jd_text(db, chosen_match.job_description_id)

    # Step 3: get the resume text.
    parsed = get_parsed_resume(resume)
    resume_text = parsed.full_text

    # Step 4: load the latest Skill Gap Analysis — required to drive the plan.
    skill_gap = _load_skill_gap(db, resume.id, chosen_match.id)
    logger.debug(
        "Learning Roadmap Service: skill gap loaded for resume_id=%s "
        "(readiness_score=%d).",
        resume.id,
        skill_gap.readiness_score,
    )

    # Step 5: serialise the skill gap for the prompt.
    skill_gap_summary = _serialise_skill_gap(skill_gap, chosen_match.role_title)

    # Step 6: run the Learning Roadmap Agent.
    content: RoadmapContent = await learning_plan_agent.generate_learning_plan(
        resume_text=resume_text,
        jd_text=jd_text,
        role_title=chosen_match.role_title,
        skill_gap_summary=skill_gap_summary,
    )

    logger.info(
        "Learning Roadmap Service: agent completed for resume_id=%s.",
        resume.id,
    )

    # Step 7: persist the result.
    orm_row = _persist_roadmap(
        db,
        resume_id=resume.id,
        job_match_id=chosen_match.id,
        content=content,
    )

    # Step 8: return the read model.
    return LearningRoadmapRecord.from_orm_row(orm_row)
