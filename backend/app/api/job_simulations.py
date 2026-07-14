"""Routes for the AI Job Simulation Agent.

Thin HTTP layer only: request/response shaping and translating
service/agent exceptions into appropriate HTTP status codes. All
orchestration (loading job matches, loading JD texts, running concurrent AI
calls, persisting results) lives in `app.services.simulation_service`. All
Gemini logic lives in `app.agents.simulation_agent`.

Endpoints
---------
POST /job-matches/{resume_id}/simulate/{job_match_id}
    Generate (or return a cached) simulation for ONE career match.
    This is the preferred "Start Experience" flow: ~15-20 s instead of ~60 s.

POST /job-matches/{resume_id}/simulate-all
    Legacy endpoint: generates all three simulations concurrently.
    Kept for backward compatibility.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents import simulation_agent
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.job_simulation import JobSimulationRecord, SimulateAllResponse
from app.models.resume import Resume
from app.models.user import User
from app.services import resume_store_service, simulation_service

router = APIRouter(prefix="/job-matches", tags=["job-simulations"])


@router.post(
    "/{resume_id}/simulate/{job_match_id}",
    response_model=JobSimulationRecord,
    summary="Generate (or return cached) simulation for a single career match.",
    status_code=status.HTTP_200_OK,
)
async def simulate_single_career(
    resume_id: int,
    job_match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobSimulationRecord:
    """Generate a simulation for one specific career match.

    This is the preferred endpoint for the "Start Experience" flow.
    Generates only the simulation for the career the user clicked on,
    reducing wait time from ~60 s to ~15-20 s.  Results are cached —
    clicking "Start Experience" again returns the cached result instantly.

    HTTP status codes
    -----------------
    - 200: simulation generated or returned from cache.
    - 400: job match not found or JD has no parsed text.
    - 404: resume not found or does not belong to the current user.
    - 502: the Gemini API call failed.
    - 504: the Gemini API call timed out.
    """
    resume: Resume | None = resume_store_service.get_resume_by_id(db, resume_id)
    if resume is None or resume.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    try:
        record = await simulation_service.simulate_for_match(db, resume_id, job_match_id)
    except simulation_service.JobMatchesNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Career match not found. Run the Career Recommendation Agent first.",
        ) from exc
    except simulation_service.JobDescriptionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description not found. The JD may have been deleted.",
        ) from exc
    except simulation_agent.SimulationAgentTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Simulation generation timed out. Please try again.",
        ) from exc
    except (
        simulation_agent.LLMRequestError,
        simulation_agent.InvalidSimulationResponseError,
    ) as exc:
        # Never mask the real agent/OpenRouter failure — the frontend surfaces
        # `detail` via ApiError.message. A generic string made 502s undebuggable.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return record


@router.post(
    "/{resume_id}/simulate-all",
    response_model=SimulateAllResponse,
    summary="Generate all three AI job simulations for a resume's Top 3 career matches.",
    status_code=status.HTTP_200_OK,
)
async def simulate_all_careers(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SimulateAllResponse:
    """Run the Simulation Agent concurrently for all three career matches.

    Flow:
    1. Verify the resume exists and belongs to the authenticated user.
    2. Delegate to `simulation_service.simulate_all_for_resume`, which:
       a. Loads the three `JobMatch` rows for this resume.
       b. Loads the `JobDescription.parsed_text` for each match.
       c. Runs three concurrent `generate_simulation()` calls via
          `asyncio.gather()`.
       d. Persists all three results in a single DB transaction.
    3. Return the three `JobSimulationRecord`s wrapped in a
       `SimulateAllResponse`.

    Prerequisites
    -------------
    `POST /job-matches/{resume_id}` (the Career Recommendation Agent endpoint)
    must have been called first — this endpoint requires exactly three
    `JobMatch` rows to exist for the given resume.

    HTTP status codes
    -----------------
    - 200: three simulations successfully generated and persisted.
    - 400: the resume has fewer than three career matches (run the Career
      Recommendation Agent first), or a matched JD has no parsed text.
    - 404: resume not found or does not belong to the current user.
    - 502: the Gemini API call failed.
    - 504: the Gemini API call timed out.
    """
    # Verify the resume exists and belongs to the authenticated user.
    resume: Resume | None = resume_store_service.get_resume_by_id(db, resume_id)
    if resume is None or resume.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    try:
        records = await simulation_service.simulate_all_for_resume(db, resume_id)
    except simulation_service.JobMatchesNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except simulation_service.JobDescriptionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except simulation_agent.SimulationAgentTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    except (
        simulation_agent.LLMRequestError,
        simulation_agent.InvalidSimulationResponseError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return SimulateAllResponse(simulations=records)
