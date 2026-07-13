"""Context assembly for the Career Mentor Chatbot.

Given a `resume_id`, fetches all available project data from Postgres and
formats it into a compact, structured context block that the mentor prompt
can consume directly.

Design decisions
----------------
1. **Direct structured retrieval, not RAG** — every data source (resume
   review, skill gap, roadmap, chosen career) is already structured JSON in
   Postgres, bounded in size. Embedding and ChromaDB retrieval would add
   latency and cost with no quality benefit when the data is already
   structured and small. This is the right call for this architecture.

2. **No LLM calls** — the assembly is pure DB reads + string formatting.
   The mentor agent (``app.agents.career_mentor``) is the only module that
   calls Gemini. This keeps the context service fast and independently
   testable without mocking Gemini.

3. **Explicit missing-data annotations** — every optional data source
   (chosen career, skill gap, roadmap) has a clearly labelled "not yet
   available" placeholder when absent. The prompt instructs the mentor to
   surface these messages to the user rather than guessing or hallucinating.

4. **Resume text truncation** — raw resume text can be many kilobytes. We
   cap it at ``RESUME_TEXT_LIMIT`` characters to keep the prompt compact
   without losing meaningful signal. The structured fields (skills,
   experience summary) are always included in full.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.job_description import JobDescription
from app.models.job_match import JobMatch
from app.models.learning_roadmap import LearningRoadmap, RoadmapContent
from app.models.report import RESUME_REVIEW_REPORT_TYPE, Report
from app.models.resume import Resume
from app.models.skill_gap import SkillGap
from app.services.resume_store_service import get_parsed_resume

logger = logging.getLogger(__name__)

# Maximum characters of raw resume text to include in the context block.
# Structured fields (skills, experience) are always included verbatim.
RESUME_TEXT_LIMIT = 2500


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _truncate(text: str, limit: int = RESUME_TEXT_LIMIT) -> str:
    """Truncate text to `limit` characters, appending an ellipsis if cut."""
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n[... truncated for context length ...]"


def _load_resume_section(resume: Resume) -> str:
    """Format the candidate's parsed resume into a context block."""
    parsed = get_parsed_resume(resume)
    lines = [
        "=== CANDIDATE RESUME ===",
        f"File: {resume.file_name}",
    ]
    if parsed.name:
        lines.append(f"Name: {parsed.name}")
    if parsed.email:
        lines.append(f"Email: {parsed.email}")
    if parsed.skills:
        lines.append(f"\nSkills:\n{parsed.skills.strip()}")
    if parsed.education:
        lines.append(f"\nEducation:\n{parsed.education.strip()}")
    if parsed.experience:
        lines.append(f"\nExperience:\n{parsed.experience.strip()}")
    if parsed.projects:
        lines.append(f"\nProjects:\n{parsed.projects.strip()}")
    # Include truncated full text as a fallback for details not caught by
    # the structured extractor (the heuristic parser can miss sections).
    if parsed.full_text:
        lines.append(
            f"\nFull resume text (truncated):\n{_truncate(parsed.full_text)}"
        )
    return "\n".join(lines)


def _load_resume_review_section(db: Session, resume_id: int) -> str:
    """Format the Resume Reviewer Agent's output, or note it is missing."""
    report: Report | None = (
        db.query(Report)
        .filter(
            Report.resume_id == resume_id,
            Report.report_type == RESUME_REVIEW_REPORT_TYPE,
        )
        .order_by(Report.created_at.desc())
        .first()
    )
    if report is None:
        return (
            "=== RESUME REVIEW ===\n"
            "Not yet available. The Resume Review Agent has not run for this resume."
        )

    c = report.content
    lines = [
        "=== RESUME REVIEW ===",
        f"Overall Score: {c.get('overall_score', 'N/A')}/100",
        f"ATS Score:     {c.get('ats_score', 'N/A')}/100",
        f"Summary:       {c.get('summary', '')}",
    ]
    strengths = c.get("strengths", [])
    if strengths:
        lines.append("Strengths: " + "; ".join(strengths))
    weaknesses = c.get("weaknesses", [])
    if weaknesses:
        lines.append("Weaknesses: " + "; ".join(weaknesses))
    suggestions = c.get("suggestions", [])
    if suggestions:
        lines.append("Key suggestions: " + "; ".join(suggestions[:4]))
    return "\n".join(lines)


def _load_chosen_career_section(db: Session, resume_id: int) -> tuple[str, int | None]:
    """Format the chosen career + its JD, or note it is missing.

    Returns
    -------
    tuple[str, int | None]
        A 2-tuple of (context_block, job_match_id). `job_match_id` is None
        when no career has been chosen — downstream sections that depend on
        the chosen career will also be marked as unavailable.
    """
    chosen: JobMatch | None = (
        db.query(JobMatch)
        .filter(JobMatch.resume_id == resume_id, JobMatch.is_chosen.is_(True))
        .first()
    )
    if chosen is None:
        return (
            "=== CHOSEN CAREER ===\n"
            "Not yet selected. The user has not chosen a target career from their "
            "Top 3 recommendations. Skill gap and roadmap data are also unavailable "
            "until a career is selected.",
            None,
        )

    jd: JobDescription | None = (
        db.query(JobDescription)
        .filter(JobDescription.id == chosen.job_description_id)
        .first()
    )

    lines = [
        "=== CHOSEN CAREER ===",
        f"Role Title:     {chosen.role_title}",
        f"Match %:        {chosen.match_percent}%",
        f"Confidence:     {chosen.confidence_score}",
        f"Career Overview: {chosen.career_overview}",
        f"Why it matched: {chosen.reasoning}",
    ]
    if chosen.missing_skills:
        lines.append("Missing skills (at recommendation time): " + ", ".join(chosen.missing_skills))

    if jd is None:
        lines.append(
            "\nJob Description: Not found (JD may have been deleted after recommendation)."
        )
    elif jd.parsed_text and jd.parsed_text.strip():
        lines.append(
            f"\nJob Description (full text, truncated):\n{_truncate(jd.parsed_text, 3000)}"
        )
    else:
        lines.append("\nJob Description: Exists but has no parsed text.")

    return "\n".join(lines), chosen.id


def _load_skill_gap_section(db: Session, resume_id: int, job_match_id: int | None) -> str:
    """Format the Skill Gap Analysis output, or note it is missing."""
    if job_match_id is None:
        return (
            "=== SKILL GAP ANALYSIS ===\n"
            "Not yet available. No career has been selected, so skill gap analysis "
            "has not run."
        )

    gap: SkillGap | None = (
        db.query(SkillGap)
        .filter(
            SkillGap.resume_id == resume_id,
            SkillGap.job_match_id == job_match_id,
        )
        .order_by(SkillGap.created_at.desc())
        .first()
    )
    if gap is None:
        return (
            "=== SKILL GAP ANALYSIS ===\n"
            "Not yet generated. The Skill Gap Agent has not run for the selected career."
        )

    lines = [
        "=== SKILL GAP ANALYSIS ===",
        f"Readiness Score: {gap.readiness_score}/100",
        f"Summary: {gap.summary}",
    ]
    if gap.existing_skills:
        lines.append("Existing skills: " + ", ".join(gap.existing_skills))
    if gap.missing_technical_skills:
        lines.append("Missing technical skills: " + ", ".join(gap.missing_technical_skills))
    if gap.missing_soft_skills:
        lines.append("Missing soft skills: " + ", ".join(gap.missing_soft_skills))
    if gap.recommended_next_steps:
        lines.append(
            "Recommended next steps:\n"
            + "\n".join(f"  {i+1}. {s}" for i, s in enumerate(gap.recommended_next_steps))
        )
    return "\n".join(lines)


def _load_roadmap_section(db: Session, resume_id: int, job_match_id: int | None) -> str:
    """Format the 3-Month Learning Roadmap, or note it is missing."""
    if job_match_id is None:
        return (
            "=== 3-MONTH LEARNING ROADMAP ===\n"
            "Not yet available. No career has been selected, so the roadmap has not "
            "been generated."
        )

    roadmap: LearningRoadmap | None = (
        db.query(LearningRoadmap)
        .filter(
            LearningRoadmap.resume_id == resume_id,
            LearningRoadmap.job_match_id == job_match_id,
        )
        .order_by(LearningRoadmap.created_at.desc())
        .first()
    )
    if roadmap is None:
        return (
            "=== 3-MONTH LEARNING ROADMAP ===\n"
            "Not yet generated. The Learning Roadmap Agent has not run for the selected career."
        )

    try:
        content = RoadmapContent.model_validate(roadmap.roadmap_json)
    except Exception:
        return (
            "=== 3-MONTH LEARNING ROADMAP ===\n"
            "Roadmap data exists but could not be read. Please regenerate the roadmap."
        )

    def _fmt_month(label: str, plan) -> str:  # type: ignore[return]
        return (
            f"{label}: {plan.focus}\n"
            f"  Topics: {', '.join(plan.topics)}\n"
            f"  Projects: {', '.join(plan.projects)}\n"
            f"  Resources: {', '.join(plan.resources)}\n"
            f"  Milestones: {', '.join(plan.milestones)}"
        )

    lines = [
        "=== 3-MONTH LEARNING ROADMAP ===",
        _fmt_month("Month 1", content.month_1),
        _fmt_month("Month 2", content.month_2),
        _fmt_month("Month 3", content.month_3),
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


def assemble_context(db: Session, resume: Resume) -> str:
    """Build the full context block for the Career Mentor Chatbot.

    Fetches all available project data for the given resume and formats it
    into a single structured string. The string is passed verbatim into the
    mentor prompt so the model always knows exactly what data is available.

    When a data source is missing (e.g. skill gap not yet generated), an
    explicit "not yet available" note is included so the mentor can report
    the gap to the user instead of guessing.

    No LLM calls are made here — this is pure DB reads + string formatting.

    Parameters
    ----------
    db:
        Synchronous SQLAlchemy session provided by the FastAPI dependency.
    resume:
        The ``Resume`` ORM instance whose context is being assembled.

    Returns
    -------
    str
        A multi-section context block ready for insertion into the mentor
        system prompt.
    """
    logger.debug("Assembling mentor context for resume_id=%s.", resume.id)

    resume_section = _load_resume_section(resume)
    review_section = _load_resume_review_section(db, resume.id)
    career_section, chosen_job_match_id = _load_chosen_career_section(db, resume.id)
    skill_gap_section = _load_skill_gap_section(db, resume.id, chosen_job_match_id)
    roadmap_section = _load_roadmap_section(db, resume.id, chosen_job_match_id)

    context = "\n\n".join([
        resume_section,
        review_section,
        career_section,
        skill_gap_section,
        roadmap_section,
    ])

    logger.debug(
        "Mentor context assembled for resume_id=%s (chosen_job_match_id=%s, "
        "context_length=%d chars).",
        resume.id,
        chosen_job_match_id,
        len(context),
    )
    return context
