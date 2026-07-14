"""Routes for the Learning Roadmap Agent.

Thin HTTP layer only: request/response shaping and translating
service/agent exceptions into appropriate HTTP status codes. All
orchestration (loading the chosen career, JD text, skill gap, running the
AI call, persisting results) lives in
`app.services.learning_roadmap_service`. All Gemini logic lives in
`app.agents.learning_plan`.

Endpoint
--------
POST /learning-roadmap/{resume_id}

    Generates a personalised 3-Month Learning Roadmap for the career the
    user has chosen.

    Prerequisites:
    1. A resume must exist with `resume_id` (created by `POST /resumes`).
    2. The Career Recommendation Agent must have run (`POST /job-matches/{id}`).
    3. The user must have chosen one career (`PATCH /job-matches/{id}/choose`).
    4. The Skill Gap Analysis must have run (`POST /skill-gap/{resume_id}`).

    The roadmap is grounded in the selected career's JD and Skill Gap Analysis
    — never in generic role templates, never hallucinated.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents import learning_plan as learning_plan_agent
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.learning_roadmap import LearningRoadmapResponse
from app.models.resume import Resume
from app.models.user import User
from app.services import learning_roadmap_service, resume_store_service

router = APIRouter(prefix="/learning-roadmap", tags=["learning-roadmap"])


@router.post(
    "/{resume_id}",
    response_model=LearningRoadmapResponse,
    summary="Generate a personalised 3-Month Learning Roadmap for the user's chosen career.",
    status_code=status.HTTP_200_OK,
)
async def create_learning_roadmap(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LearningRoadmapResponse:
    """Run the Learning Roadmap Agent for the user's chosen career.

    Flow:
    1. Verify the resume exists and belongs to the authenticated user.
    2. Delegate to `learning_roadmap_service.generate_roadmap`, which:
       a. Loads the chosen `JobMatch` for this resume.
       b. Loads the full `JobDescription.parsed_text` (primary source of truth).
       c. Loads the resume text.
       d. Loads the latest `SkillGap` for the chosen match (required).
       e. Serialises the skill gap for the prompt.
       f. Calls the Learning Roadmap Agent.
       g. Persists the result as a `LearningRoadmap` row.
    3. Return the `LearningRoadmapRecord` wrapped in a `LearningRoadmapResponse`.

    Prerequisites
    -------------
    - `POST /resumes` — resume must exist.
    - `POST /job-matches/{resume_id}` — career recommendations must have run.
    - `PATCH /job-matches/{job_match_id}/choose` — user must have selected a career.
    - `POST /skill-gap/{resume_id}` — skill gap analysis must have run.

    HTTP status codes
    -----------------
    - 200: roadmap successfully generated and persisted.
    - 400: no career selected, JD has no text, or no skill gap analysis found.
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
        roadmap_record = await learning_roadmap_service.generate_roadmap(db, resume)
    except learning_roadmap_service.NoChosenCareerError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except learning_roadmap_service.JobDescriptionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except learning_roadmap_service.SkillGapNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except learning_plan_agent.LearningPlanAgentTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    except (
        learning_plan_agent.LLMRequestError,
        learning_plan_agent.InvalidLearningPlanResponseError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return LearningRoadmapResponse(roadmap=roadmap_record)
