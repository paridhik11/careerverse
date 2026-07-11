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
from app.models.job_match import JobMatchListResponse, JobMatchRecord
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
        career_advisor.OpenAIRequestError,
        career_advisor.InvalidCareerAdvisorResponseError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return JobMatchListResponse(
        matches=[JobMatchRecord.model_validate(match) for match in job_matches]
    )
