"""Business logic for the Skill Gap Analysis flow.

Per `.cursorrules`, all orchestration belongs here:
- `api/skill_gap.py` stays a thin HTTP layer.
- `agents/skill_gap.py` only knows how to call Gemini.
- This service owns loading, enrichment, persistence, and error mapping.

Flow (see `generate_skill_gap`):
1. Load the chosen `JobMatch` for the resume — fail fast if no career has
   been selected or if the match belongs to a different resume.
2. Load the full `JobDescription.parsed_text` for the chosen match — this is
   the PRIMARY source of truth for the skill gap analysis.
3. Reload the resume text from the stored `Resume.parsed_resume`.
4. Optionally load the Resume Reviewer Agent's summary as enrichment context.
5. Optionally load any VWE performance metadata from the `JobSimulation` row
   linked to the chosen `JobMatch` (only if a simulation was completed).
6. Call the Skill Gap Agent with all available inputs.
7. Persist the validated `SkillGapContent` as a `SkillGap` row.
8. Return the `SkillGapRecord` read model.

Idempotency
-----------
Each call re-generates and re-persists the skill gap. For MVP this is
acceptable — the user is unlikely to call this endpoint multiple times, and
the cost is a single AI call. The latest row is always the most relevant.
"""

from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from app.agents import skill_gap as skill_gap_agent
from app.models.job_description import JobDescription
from app.models.job_match import JobMatch
from app.models.job_simulation import JobSimulation
from app.models.report import RESUME_REVIEW_REPORT_TYPE
from app.models.resume import Resume
from app.models.skill_gap import SkillGap, SkillGapContent, SkillGapRecord
from app.services import report_service
from app.services.resume_store_service import get_parsed_resume

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Typed exception hierarchy
# ---------------------------------------------------------------------------


class SkillGapServiceError(Exception):
    """Base class for every error in the skill gap service layer."""


class NoChosenCareerError(SkillGapServiceError):
    """The user has not yet chosen a career for this resume.

    `PATCH /job-matches/{job_match_id}/choose` must be called first.
    """


class JobDescriptionNotFoundError(SkillGapServiceError):
    """The `JobDescription` linked to the chosen `JobMatch` is missing or has no text.

    Cannot produce a JD-grounded analysis without the JD content.
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
            f"Cannot produce a JD-grounded skill gap analysis without JD content."
        )
    return jd.parsed_text


def _resume_review_summary(db: Session, resume_id: int) -> str | None:
    """Best-effort optional context: the Resume Reviewer Agent's summary.

    Returns `None` if no review report exists — the skill gap analysis
    still runs, relying only on raw resume text.
    """
    report = report_service.get_latest_report(
        db, resume_id=resume_id, report_type=RESUME_REVIEW_REPORT_TYPE
    )
    if report is None:
        return None
    return report.content.get("summary")


def _simulation_metadata(db: Session, job_match_id: int) -> str | None:
    """Best-effort optional VWE performance data for the chosen career.

    Loads the `JobSimulation` linked to `job_match_id` (if one exists) and
    serialises a lightweight performance summary from its `simulation_json`.
    Returns `None` if no simulation has been completed for this match — the
    skill gap analysis still runs without the 10 % simulation adjustment.

    The summary extracts the per-task evaluation scores and produces a
    compact JSON string that the prompt can parse for signal without needing
    to read the full simulation content.
    """
    simulation: JobSimulation | None = (
        db.query(JobSimulation)
        .filter(JobSimulation.job_match_id == job_match_id)
        .order_by(JobSimulation.created_at.desc())
        .first()
    )
    if simulation is None:
        return None

    sim_json = simulation.simulation_json
    if not isinstance(sim_json, dict):
        return None

    tasks = sim_json.get("tasks", [])
    if not tasks:
        return None

    # Build a compact competency summary from per-task evaluation scores.
    competency_totals: dict[str, int] = {
        "communication": 0,
        "problem_solving": 0,
        "technical_judgment": 0,
        "collaboration": 0,
        "leadership": 0,
        "adaptability": 0,
    }
    task_count = 0
    for task in tasks:
        evaluation = task.get("evaluation", {})
        if not evaluation:
            continue
        for key in competency_totals:
            competency_totals[key] += evaluation.get(key, 0)
        task_count += 1

    if task_count == 0:
        return None

    averages = {k: round(v / task_count, 1) for k, v in competency_totals.items()}

    summary = {
        "job_title": sim_json.get("job_title", ""),
        "tasks_completed": task_count,
        "average_competency_scores_out_of_10": averages,
        "note": (
            "Scores reflect competency ceilings exercised across the completed "
            "Virtual Work Experience tasks — higher is stronger."
        ),
    }
    return json.dumps(summary, indent=2)


def _persist_skill_gap(
    db: Session,
    resume_id: int,
    job_match_id: int,
    content: SkillGapContent,
) -> SkillGap:
    """Save a validated `SkillGapContent` as a `SkillGap` row.

    Commits in a single transaction and refreshes the row so the caller
    receives a fully populated ORM instance (with auto-generated `id` and
    `created_at`).
    """
    record = SkillGap(
        resume_id=resume_id,
        job_match_id=job_match_id,
        existing_skills=content.existing_skills,
        missing_technical_skills=content.missing_technical_skills,
        missing_soft_skills=content.missing_soft_skills,
        recommended_next_steps=content.recommended_next_steps,
        readiness_score=content.readiness_score,
        summary=content.summary,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


async def generate_skill_gap(
    db: Session,
    resume: Resume,
) -> SkillGapRecord:
    """Run the full Skill Gap Analysis flow for the user's chosen career.

    Parameters
    ----------
    db:
        Synchronous SQLAlchemy session provided by the FastAPI dependency.
    resume:
        The `Resume` ORM instance whose chosen career is being analysed.

    Returns
    -------
    SkillGapRecord
        A fully populated read model containing the readiness score, skills
        lists, summary, and recommended next steps.

    Raises
    ------
    NoChosenCareerError
        The user has not yet selected a career for this resume.
    JobDescriptionNotFoundError
        The chosen career's Job Description is missing or has no parsed text.
    skill_gap_agent.InvalidSkillGapResponseError
        Gemini returned a response that could not be parsed or validated.
    skill_gap_agent.GeminiRequestError
        The Gemini API call failed.
    skill_gap_agent.SkillGapAgentTimeoutError
        The Gemini API call timed out.
    """
    # Step 1: load the chosen career — fail fast if none is selected.
    chosen_match = _load_chosen_job_match(db, resume.id)

    logger.info(
        "Skill Gap Service: analysing gap for resume_id=%s, "
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

    # Step 4: optional enrichment — Resume Reviewer summary.
    review_summary = _resume_review_summary(db, resume.id)
    if review_summary:
        logger.debug(
            "Skill Gap Service: resume review summary loaded for resume_id=%s.", resume.id
        )

    # Step 5: optional enrichment — VWE performance data.
    sim_meta = _simulation_metadata(db, chosen_match.id)
    if sim_meta:
        logger.debug(
            "Skill Gap Service: VWE simulation metadata loaded for job_match_id=%s.",
            chosen_match.id,
        )
    else:
        logger.debug(
            "Skill Gap Service: no simulation data found for job_match_id=%s; "
            "analysis will rely on resume ↔ JD comparison only.",
            chosen_match.id,
        )

    # Step 6: run the Skill Gap Agent.
    content: SkillGapContent = await skill_gap_agent.analyse_skill_gap(
        resume_text=resume_text,
        jd_text=jd_text,
        role_title=chosen_match.role_title,
        resume_review_summary=review_summary,
        simulation_metadata=sim_meta,
    )

    logger.info(
        "Skill Gap Service: agent completed for resume_id=%s. "
        "readiness_score=%d.",
        resume.id,
        content.readiness_score,
    )

    # Step 7: persist the result.
    orm_row = _persist_skill_gap(
        db,
        resume_id=resume.id,
        job_match_id=chosen_match.id,
        content=content,
    )

    # Step 8: return the read model.
    return SkillGapRecord.from_orm_row(orm_row)
