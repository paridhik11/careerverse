"""Business logic for the AI Job Simulation flow.

Per `.cursorrules`, all orchestration belongs here:
- `api/job_simulations.py` stays a thin HTTP layer.
- `agents/simulation_agent.py` only knows how to call OpenAI.
- This service owns loading, concurrency, persistence, and error mapping.

Flow (see `simulate_all_for_resume`):
1. Load exactly three `JobMatch` records for the given resume, ordered by
   rank.
2. Load the full `JobDescription.parsed_text` for each match — this is the
   ONLY source of truth the Simulation Agent uses.
3. Launch three concurrent Simulation Agent calls via `asyncio.gather()` so
   all three simulations are generated in parallel, not sequentially.
4. Persist each result as a `JobSimulation` row linked to its `JobMatch`.
5. Return the three records ordered by rank (rank 1 = best match first).

Concurrency design
------------------
`asyncio.gather()` fires three `generate_simulation()` coroutines at once
and awaits all three. Wall-clock time is determined by the slowest call
(whichever JD produces the most complex simulation), not by the sum of
all three — a significant latency win for the end user compared to serial
execution. The DB session is used synchronously before and after `gather()`;
it is never shared between coroutines.

Idempotency
-----------
Simulations are re-generated each time the endpoint is called. This matches
the pattern of the Career Recommendation Agent (which also always re-runs).
For an MVP the user is unlikely to call simulate-all multiple times; the
cost of a duplicate call is one set of AI tokens, which is acceptable.
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

    # Step 3: fire all three simulation calls concurrently.
    # asyncio.gather raises the first exception encountered and cancels the
    # remaining coroutines, so a single failure surfaces immediately.
    simulation_contents: tuple[SimulationContent, ...] = await asyncio.gather(
        *[
            simulation_agent.generate_simulation(match.role_title, jd_text)
            for match, jd_text in zip(matches, jd_texts)
        ]
    )

    logger.info(
        "Simulation Service: all 3 simulations generated for resume_id=%s. Persisting.",
        resume_id,
    )

    # Step 4: persist all three in one DB transaction.
    orm_rows = _persist_simulations(db, matches, list(simulation_contents))

    # Step 5: build and return read models, preserving rank order.
    return [JobSimulationRecord.from_orm_row(row) for row in orm_rows]
