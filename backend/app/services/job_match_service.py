"""Business logic for the Career Recommendation flow.

Orchestrates (per `.cursorrules`, this is the only place this orchestration
should live — `api/job_matches.py` stays a thin route, and
`agents/career_advisor.py` only knows how to call OpenAI):

1. Load the resume by id.
2. Retrieve the Top-K relevant Job Descriptions from ChromaDB via the
   existing RAG retriever.
3. Pass the resume + retrieved JD context to the Career Recommendation Agent.
4. Persist the exactly-three recommendations as `JobMatch` rows, each with
   `is_chosen=False`.

`JobDescription.parsed_text` is never touched here — recommendations only
store a foreign key to it, so the full JD text stays retrievable by id for
the Job Simulation Agent (a later milestone).
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.agents import career_advisor
from app.models.job_match import CareerMatchRecommendation, JobMatch
from app.models.report import RESUME_REVIEW_REPORT_TYPE
from app.models.resume import Resume
from app.rag.retriever import EmbeddingError, retrieve_relevant_job_descriptions
from app.rag.store import ChromaDBError
from app.services import report_service
from app.services.resume_store_service import get_parsed_resume

logger = logging.getLogger(__name__)

RAG_TOP_K = 8


class JobMatchServiceError(Exception):
    """Base class for every Career Recommendation flow failure at the service layer."""


class NoJobDescriptionsAvailableError(JobMatchServiceError):
    """No job descriptions have been retrieved/indexed yet — nothing to match against."""


class RetrievalFailedError(JobMatchServiceError):
    """The RAG retrieval step (embeddings or ChromaDB) failed."""


class JobMatchNotFoundError(JobMatchServiceError):
    """No `JobMatch` row was found for the given id and resume combination."""


def _resume_review_summary(db: Session, resume_id: int) -> str | None:
    """Best-effort optional context: the Resume Reviewer Agent's summary, if it exists."""
    report = report_service.get_latest_report(
        db, resume_id=resume_id, report_type=RESUME_REVIEW_REPORT_TYPE
    )
    if report is None:
        return None
    return report.content.get("summary")


def _persist_matches(
    db: Session,
    *,
    resume_id: int,
    matches: list[CareerMatchRecommendation],
) -> list[JobMatch]:
    """Save exactly three `CareerMatchRecommendation`s as `JobMatch` rows."""
    records: list[JobMatch] = []
    for match in matches:
        record = JobMatch(
            resume_id=resume_id,
            job_description_id=int(match.job_description_id),
            role_title=match.role_title,
            match_percent=match.match_percent,
            confidence_score=match.confidence_score,
            reasoning=match.reasoning,
            career_overview=match.career_overview,
            missing_skills=match.missing_skills,
            rank=match.rank,
            is_chosen=False,
        )
        db.add(record)
        records.append(record)

    db.commit()
    for record in records:
        db.refresh(record)

    # Return in rank order (1, 2, 3) regardless of insertion order.
    return sorted(records, key=lambda record: record.rank)


async def generate_job_matches(db: Session, resume: Resume) -> list[JobMatch]:
    """Run the full Career Recommendation flow for a stored resume.

    Raises
    ------
    NoJobDescriptionsAvailableError
        No job descriptions have been uploaded/indexed yet.
    RetrievalFailedError
        The RAG retrieval step failed (embedding or ChromaDB error).
    app.agents.career_advisor.CareerAdvisorError (and subclasses)
        The Career Recommendation Agent failed to produce a valid response —
        propagated as-is so the API layer can map it to the right HTTP status.
    """
    parsed_resume = get_parsed_resume(resume)

    try:
        retrieved_job_descriptions = retrieve_relevant_job_descriptions(
            parsed_resume.full_text, top_k=RAG_TOP_K
        )
    except EmbeddingError as exc:
        raise RetrievalFailedError(f"Could not embed resume for retrieval: {exc}") from exc
    except ChromaDBError as exc:
        raise RetrievalFailedError(f"RAG retrieval failed: {exc}") from exc

    if not retrieved_job_descriptions:
        raise NoJobDescriptionsAvailableError(
            "No job descriptions are available yet — upload one or more job "
            "descriptions before requesting career recommendations."
        )

    review_summary = _resume_review_summary(db, resume.id)

    matches = await career_advisor.generate_career_matches(
        parsed_resume.full_text,
        retrieved_job_descriptions,
        resume_review_summary=review_summary,
    )

    logger.info(
        "Career Recommendation Agent produced %d matches for resume_id=%s.",
        len(matches),
        resume.id,
    )

    return _persist_matches(db, resume_id=resume.id, matches=matches)


def choose_job_match(db: Session, *, job_match_id: int, resume_id: int) -> JobMatch:
    """Atomically mark one `JobMatch` as chosen and deselect every sibling.

    Both writes (bulk deselect + single select) execute inside one transaction
    so the DB is never left in a partially-updated state.

    Raises
    ------
    JobMatchNotFoundError
        No `JobMatch` with `id == job_match_id` and `resume_id == resume_id` exists.
    """
    target = (
        db.query(JobMatch)
        .filter(JobMatch.id == job_match_id, JobMatch.resume_id == resume_id)
        .first()
    )
    if target is None:
        raise JobMatchNotFoundError(
            f"No job match found with id={job_match_id} for resume_id={resume_id}."
        )

    # Deselect all matches for this resume, then select the target — one transaction.
    (
        db.query(JobMatch)
        .filter(JobMatch.resume_id == resume_id)
        .update({"is_chosen": False}, synchronize_session="evaluate")
    )
    target.is_chosen = True
    db.commit()
    db.refresh(target)

    logger.info(
        "Career selected: job_match_id=%s (role=%r) for resume_id=%s.",
        target.id,
        target.role_title,
        target.resume_id,
    )
    return target


def get_chosen_job_match(db: Session, *, resume_id: int) -> JobMatch | None:
    """Return the chosen `JobMatch` for a resume, or `None` if none has been selected yet."""
    return (
        db.query(JobMatch)
        .filter(JobMatch.resume_id == resume_id, JobMatch.is_chosen.is_(True))
        .first()
    )
