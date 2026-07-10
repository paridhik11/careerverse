"""Routes for persisted resumes and the Resume Reviewer Agent.

Thin HTTP layer only: request/response shaping and translating service/agent
exceptions into HTTP status codes. Business logic (validation, DB access)
lives in `app.services`; AI logic lives in `app.agents.resume_reviewer`.

`POST /resumes/{id}/review` is the endpoint required by this milestone.
`POST /resumes` exists alongside it purely so a resume can get a database id
to review — it delegates to the existing, unmodified upload
(`resume_service.save_resume_upload`) and parsing (`resume_parser.parse_resume`)
logic and does not change either of them.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.agents import resume_reviewer
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.report import RESUME_REVIEW_REPORT_TYPE, ResumeReviewReport
from app.models.resume import ResumeRecordResponse
from app.models.user import User
from app.services import report_service, resume_service, resume_store_service
from app.services.resume_parser import ResumeParseError

router = APIRouter(prefix="/resumes", tags=["resume-review"])


@router.post(
    "",
    response_model=ResumeRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload, parse, and persist a resume so it can be reviewed by id.",
)
async def create_resume(
    file: UploadFile = File(..., description="Resume PDF"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeRecordResponse:
    """Store a resume with a database id.

    Reuses the existing upload validation and PyMuPDF parsing unchanged; this
    endpoint only adds the database row that `POST /resumes/{id}/review`
    needs in order to load a parsed resume by id.
    """
    try:
        resume = await resume_store_service.ingest_resume(db, file, user_id=current_user.id)
    except resume_service.InvalidResumeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ResumeParseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ResumeRecordResponse.model_validate(resume)


@router.post(
    "/{resume_id}/review",
    response_model=ResumeReviewReport,
    summary="Run the Resume Reviewer Agent on a stored resume.",
)
async def review_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeReviewReport:
    """Review a previously stored resume with GPT-4o and persist the report.

    Flow: load the parsed resume by id -> call the Resume Reviewer Agent ->
    persist the result as a `resume_review` Report -> return the structured
    report (matching the schema exactly, with no extra envelope fields).
    """
    resume = resume_store_service.get_resume_by_id(db, resume_id)
    if resume is None or resume.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")

    parsed_resume = resume_store_service.get_parsed_resume(resume)
    if not parsed_resume.full_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This resume has no parsed content to review.",
        )

    try:
        report = await resume_reviewer.review_resume(parsed_resume)
    except resume_reviewer.ResumeReviewTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc)
        ) from exc
    except resume_reviewer.OpenAIRequestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except resume_reviewer.InvalidReviewResponseError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    report_service.save_report(
        db,
        resume_id=resume.id,
        report_type=RESUME_REVIEW_REPORT_TYPE,
        content=report.model_dump(),
    )

    return report
