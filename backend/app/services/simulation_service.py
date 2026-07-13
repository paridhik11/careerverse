"""Business logic for the AI Job Simulation flow.

Per `.cursorrules`, all orchestration belongs here:
- `api/job_simulations.py` stays a thin HTTP layer.
- `agents/simulation_agent.py` only knows how to call Gemini.
- This service owns loading, concurrency, persistence, and error mapping.

Two entry points
----------------
`simulate_for_match(db, resume_id, job_match_id)`
    Generates a simulation for ONE career match — called when the user
    clicks "Start Experience" on a specific card.  Much faster than
    generating all three: typically ~15-20 s instead of ~60 s.  Caches the
    result so repeated clicks return instantly.

`simulate_all_for_resume(db, resume_id)`
    Legacy entry point kept for backward compatibility. Generates all three
    concurrently — now also checks the cache and skips already-generated
    simulations.

Caching design
--------------
`JobSimulation` rows are keyed on `job_match_id` (UNIQUE constraint).  Before
calling Gemini, both helpers check whether a simulation already exists for the
requested match.  Cache hits are returned immediately with zero AI cost.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy.orm import Session

from app.agents import simulation_agent
from app.models.job_description import JobDescription
from app.models.job_match import JobMatch
from app.models.job_simulation import JobSimulation, JobSimulationRecord, SimulationContent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Typed exception hierarchy
# ---------------------------------------------------------------------------


class SimulationServiceError(Exception):
    """Base class for every error in the simulation service layer."""


class JobMatchesNotFoundError(SimulationServiceError):
    """Fewer than three `JobMatch` rows exist for this resume.

    The Career Recommendation Agent must run successfully before simulations
    can be generated.
    """


class JobDescriptionNotFoundError(SimulationServiceError):
    """A `JobMatch` references a `JobDescription` that no longer exists or has
    no parsed text — cannot generate a grounded simulation without it.
    """


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_cached_simulation(db: Session, job_match_id: int) -> JobSimulationRecord | None:
    """Return the cached simulation for a match, or None if none exists."""
    row: JobSimulation | None = (
        db.query(JobSimulation)
        .filter(JobSimulation.job_match_id == job_match_id)
        .order_by(JobSimulation.created_at.desc())
        .first()
    )
    if row is None:
        return None
    return JobSimulationRecord.from_orm_row(row)


def _load_job_matches(db: Session, resume_id: int) -> list[JobMatch]:
    """Return the three `JobMatch` rows for a resume, ordered by rank.

    Raises
    ------
    JobMatchesNotFoundError
        Fewer than three matches exist for this resume.
    """
    matches: list[JobMatch] = (
        db.query(JobMatch)
        .filter(JobMatch.resume_id == resume_id)
        .order_by(JobMatch.rank)
        .all()
    )
    if len(matches) < 3:
        raise JobMatchesNotFoundError(
            f"Found {len(matches)} job match(es) for resume_id={resume_id}, "
            f"but 3 are required. Run the Career Recommendation Agent first."
        )
    # Take at most 3 in case extra matches exist.
    return matches[:3]


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
            f"Cannot generate a grounded simulation without JD content."
        )
    return jd.parsed_text


def _persist_simulations(
    db: Session,
    matches: list[JobMatch],
    contents: list[SimulationContent],
) -> list[JobSimulation]:
    """Persist three `SimulationContent` results as `JobSimulation` rows.

    Commits in a single transaction and refreshes every row so callers
    receive fully populated ORM instances (with auto-generated `id` and
    `created_at`).
    """
    records: list[JobSimulation] = []
    for match, content in zip(matches, contents):
        record = JobSimulation(
            job_match_id=match.id,
            simulation_json=content.model_dump(),
        )
        db.add(record)
        records.append(record)

    db.commit()
    for record in records:
        db.refresh(record)

    return records


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


async def simulate_for_match(
    db: Session,
    resume_id: int,
    job_match_id: int,
) -> JobSimulationRecord:
    """Generate (or return a cached) simulation for a single career match.

    This is the preferred entry point for the "Start Experience" flow: the
    user picks one career card and we generate ONLY that simulation instead
    of all three.  Typical wall-clock time drops from ~60 s to ~15-20 s.

    Parameters
    ----------
    db:            Synchronous SQLAlchemy session.
    resume_id:     Used to scope the `JobMatch` lookup.
    job_match_id:  The specific career match to simulate.

    Returns
    -------
    JobSimulationRecord
        Either a freshly generated simulation or a cached result from a
        previous call for the same `job_match_id`.

    Raises
    ------
    JobMatchesNotFoundError
        The `job_match_id` doesn't exist or doesn't belong to `resume_id`.
    JobDescriptionNotFoundError
        The matched JD is missing or has no parsed text.
    simulation_agent.SimulationAgentError (and subclasses)
        The Simulation Agent call failed.
    """
    # Cache check — return immediately if this match was already simulated.
    cached = _get_cached_simulation(db, job_match_id)
    if cached is not None:
        logger.info(
            "Simulation Service: cache hit for job_match_id=%s resume_id=%s.",
            job_match_id,
            resume_id,
        )
        return cached

    # Load the specific JobMatch (scoped to resume_id for security).
    match: JobMatch | None = (
        db.query(JobMatch)
        .filter(JobMatch.id == job_match_id, JobMatch.resume_id == resume_id)
        .first()
    )
    if match is None:
        raise JobMatchesNotFoundError(
            f"Job match id={job_match_id} not found for resume_id={resume_id}. "
            f"Run the Career Recommendation Agent first."
        )

    jd_text = _load_jd_text(db, match.job_description_id)

    logger.info(
        "Simulation Service: generating single simulation for job_match_id=%s role='%s'.",
        job_match_id,
        match.role_title,
    )

    content: SimulationContent = await simulation_agent.generate_simulation(
        match.role_title, jd_text
    )

    # Persist and return.
    orm_row = JobSimulation(
        job_match_id=match.id,
        simulation_json=content.model_dump(),
    )
    db.add(orm_row)
    db.commit()
    db.refresh(orm_row)

    return JobSimulationRecord.from_orm_row(orm_row)


async def simulate_all_for_resume(
    db: Session,
    resume_id: int,
) -> list[JobSimulationRecord]:
    """Generate and persist three concurrent job simulations for a resume.

    Parameters
    ----------
    db:
        Synchronous SQLAlchemy session provided by the FastAPI dependency.
    resume_id:
        The id of the `Resume` whose Top 3 career matches should be
        simulated.

    Returns
    -------
    list[JobSimulationRecord]
        Exactly three `JobSimulationRecord`s, ordered by `JobMatch.rank`
        (rank 1 = best career match first).

    Raises
    ------
    JobMatchesNotFoundError
        Fewer than three `JobMatch` rows exist for this resume.
    JobDescriptionNotFoundError
        A matched JD is missing or has no parsed text.
    simulation_agent.SimulationAgentError (and subclasses)
        One or more Simulation Agent calls failed — propagated so the API
        layer can map them to the correct HTTP status codes.
    """
    # Step 1: load three JobMatch records ordered by rank.
    matches = _load_job_matches(db, resume_id)

    # Step 2: load JD text for each match upfront (synchronous DB reads).
    # Do this before entering the concurrent async phase so we fail fast
    # on a missing JD before spending any AI credits.
    jd_texts: list[str] = [
        _load_jd_text(db, match.job_description_id) for match in matches
    ]

    logger.info(
        "Simulation Service: launching 3 concurrent simulation calls for resume_id=%s "
        "(roles: %s).",
        resume_id,
        ", ".join(f"'{m.role_title}'" for m in matches),
    )

    # Step 3: check cache for each match — only call Gemini for uncached ones.
    cached_results: dict[int, JobSimulationRecord] = {}
    uncached_matches: list[JobMatch] = []
    uncached_jd_texts: list[str] = []

    for match, jd_text in zip(matches, jd_texts):
        cached = _get_cached_simulation(db, match.id)
        if cached is not None:
            cached_results[match.id] = cached
            logger.info(
                "Simulation Service: cache hit for job_match_id=%s role='%s'.",
                match.id,
                match.role_title,
            )
        else:
            uncached_matches.append(match)
            uncached_jd_texts.append(jd_text)

    # Step 4: fire concurrent simulation calls only for uncached matches.
    if uncached_matches:
        logger.info(
            "Simulation Service: generating %d new simulation(s) for resume_id=%s "
            "(roles: %s).",
            len(uncached_matches),
            resume_id,
            ", ".join(f"'{m.role_title}'" for m in uncached_matches),
        )

        new_contents: tuple[SimulationContent, ...] = await asyncio.gather(
            *[
                simulation_agent.generate_simulation(match.role_title, jd_text)
                for match, jd_text in zip(uncached_matches, uncached_jd_texts)
            ]
        )

        # Step 5: persist new results.
        new_orm_rows = _persist_simulations(db, uncached_matches, list(new_contents))
        for row in new_orm_rows:
            cached_results[row.job_match_id] = JobSimulationRecord.from_orm_row(row)

    # Step 6: return all three in rank order.
    return [cached_results[match.id] for match in matches]
