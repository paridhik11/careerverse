"""Routes for the Skill Gap Analysis Agent.

Thin HTTP layer only: request/response shaping and translating
service/agent exceptions into appropriate HTTP status codes. All
orchestration (loading the chosen career, JD text, optional enrichments,
running the AI call, persisting results) lives in
`app.services.skill_gap_service`. All Gemini logic lives in
`app.agents.skill_gap`.

Endpoint
--------
POST /skill-gap/{resume_id}

    Generates a personalised Skill Gap Analysis for the career the user
    has chosen after completing the Virtual Work Experience.

    Prerequisites:
    1. A resume must exist with `resume_id` (created by `POST /resumes`).
    2. The Career Recommendation Agent must have run (`POST /job-matches/{id}`).
    3. The user must have chosen one career (`PATCH /job-matches/{id}/choose`).

    The analysis is grounded exclusively in the selected career's uploaded
    Job Description — never in the other two recommendations, never
    hallucinated.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents import skill_gap as skill_gap_agent
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.resume import Resume
from app.models.skill_gap import SkillGapResponse
from app.models.user import User
from app.services import resume_store_service, skill_gap_service

router = APIRouter(prefix="/skill-gap", tags=["skill-gap"])


@router.post(
    "/{resume_id}",
    response_model=SkillGapResponse,
    summary="Generate a personalised Skill Gap Analysis for the user's chosen career.",
    status_code=status.HTTP_200_OK,
)
async def create_skill_gap(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SkillGapResponse:
    """Run the Skill Gap Agent for the user's chosen career.

    Flow:
    1. Verify the resume exists and belongs to the authenticated user.
    2. Delegate to `skill_gap_service.generate_skill_gap`, which:
       a. Loads the chosen `JobMatch` for this resume.
       b. Loads the full `JobDescription.parsed_text` (primary source of truth).
       c. Loads the resume text.
       d. Optionally loads the Resume Reviewer Agent's summary as enrichment.
       e. Optionally loads VWE performance metadata for the chosen career.
       f. Calls the Skill Gap Agent.
       g. Persists the result as a `SkillGap` row.
    3. Return the `SkillGapRecord` wrapped in a `SkillGapResponse`.

    Prerequisites
    -------------
    - `POST /resumes` — resume must exist.
    - `POST /job-matches/{resume_id}` — career recommendations must have run.
    - `PATCH /job-matches/{job_match_id}/choose` — user must have selected a career.

    HTTP status codes
    -----------------
    - 200: skill gap successfully generated and persisted.
    - 400: no career has been selected yet, or the JD has no text.
    - 404: resume not found or does not belong to the current user.
    - 502: the Gemini API call failed or returned an invalid response.
    - 504: the Gemini API call timed out.
    """
    resume: Resume | None = resume_store_service.get_resume_by_id(db, resume_id)
    if resume is None or resume.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    try:
        skill_gap_record = await skill_gap_service.generate_skill_gap(db, resume)
    except skill_gap_service.NoChosenCareerError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except skill_gap_service.JobDescriptionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except skill_gap_agent.SkillGapAgentTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    except (
        skill_gap_agent.LLMRequestError,
        skill_gap_agent.InvalidSkillGapResponseError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return SkillGapResponse(skill_gap=skill_gap_record)
