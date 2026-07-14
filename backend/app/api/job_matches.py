"""Routes for the Career Recommendation Agent.

Thin HTTP layer only: request/response shaping and translating
service/agent exceptions into HTTP status codes. Orchestration (loading the
resume, retrieving JDs, calling the agent, persisting results) lives in
`app.services.job_match_service`; AI logic lives in
`app.agents.career_advisor`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents import career_advisor
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.job_match import (
    CareerChoiceResponse,
    ChosenJobMatchResponse,
    JobMatchListResponse,
    JobMatchRecord,
)
from app.models.job_match import JobMatch as JobMatchORM
from app.models.user import User
from app.services import job_match_service, resume_store_service

router = APIRouter(prefix="/job-matches", tags=["job-matches"])


@router.post(
    "/{resume_id}",
    response_model=JobMatchListResponse,
    summary="Run the Career Recommendation Agent and return the Top 3 career matches.",
)
async def create_job_matches(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobMatchListResponse:
    """Generate and persist the Top 3 career recommendations for a resume.

    Flow: load the resume by id -> retrieve Top-K job descriptions via RAG ->
    run the Career Recommendation Agent -> persist exactly three `JobMatch`
    rows (each `is_chosen=False`) -> return them ranked 1-3.
    """
    resume = resume_store_service.get_resume_by_id(db, resume_id)
    if resume is None or resume.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")

    parsed_resume = resume_store_service.get_parsed_resume(resume)
    if not parsed_resume.full_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This resume has no parsed content to match against job descriptions.",
        )

    try:
        job_matches = await job_match_service.generate_job_matches(db, resume)
    except job_match_service.NoJobDescriptionsAvailableError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except job_match_service.RetrievalFailedError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except career_advisor.NoRetrievedJobDescriptionsError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except career_advisor.CareerAdvisorTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc)
        ) from exc
    except (
        career_advisor.LLMRequestError,
        career_advisor.InvalidCareerAdvisorResponseError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return JobMatchListResponse(
        matches=[JobMatchRecord.model_validate(match) for match in job_matches]
    )


@router.patch(
    "/{job_match_id}/choose",
    response_model=CareerChoiceResponse,
    summary="Choose one career — deselects every other match for the same resume.",
)
async def choose_career(
    job_match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CareerChoiceResponse:
    """Mark a single `JobMatch` as the user's chosen career.

    Flow:
    1. Load the `JobMatch` by `job_match_id` — 404 if missing.
    2. Verify the linked resume belongs to the authenticated user — 404 if not.
    3. Delegate to `job_match_service.choose_job_match`, which atomically sets
       `is_chosen=True` on the target and `is_chosen=False` on every sibling.
    4. Return the selected role title and a confirmation message.

    HTTP status codes
    -----------------
    - 200: career chosen successfully.
    - 404: job match not found, or the linked resume does not belong to the user.
    """
    target: JobMatchORM | None = (
        db.query(JobMatchORM).filter(JobMatchORM.id == job_match_id).first()
    )
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job match not found.",
        )

    resume = resume_store_service.get_resume_by_id(db, target.resume_id)
    if resume is None or resume.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job match not found.",
        )

    try:
        chosen = job_match_service.choose_job_match(
            db, job_match_id=job_match_id, resume_id=resume.id
        )
    except job_match_service.JobMatchNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return CareerChoiceResponse(
        job_match_id=chosen.id,
        role_title=chosen.role_title,
        message=f"'{chosen.role_title}' has been selected as your career path.",
    )


@router.get(
    "/{resume_id}/chosen",
    response_model=ChosenJobMatchResponse,
    summary="Return the chosen career match for a resume.",
)
async def get_chosen_career(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChosenJobMatchResponse:
    """Retrieve the career the user has already chosen for a given resume.

    Returns the `ChosenJobMatchResponse` containing all fields downstream
    features (Skill Gap, Roadmap, Career Mentor) depend on.

    HTTP status codes
    -----------------
    - 200: chosen career returned.
    - 404: resume not found / not owned by user, or no career has been chosen yet.
    """
    resume = resume_store_service.get_resume_by_id(db, resume_id)
    if resume is None or resume.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    chosen = job_match_service.get_chosen_job_match(db, resume_id=resume_id)
    if chosen is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No career has been selected for this resume yet.",
        )

    return ChosenJobMatchResponse.model_validate(chosen)
