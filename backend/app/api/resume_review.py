"""Routes for persisted resumes and the Resume Reviewer Agent.

Thin HTTP layer only: request/response shaping and translating service/agent
exceptions into HTTP status codes. Business logic (validation, DB access)
lives in `app.services`; AI logic lives in `app.agents.resume_reviewer`.

`POST /resumes/{id}/review` is the endpoint required by this milestone.
`POST /resumes` exists alongside it purely so a resume can get a database id
to review — it delegates to the existing, unmodified upload
(`resume_service.save_resume_upload`) and parsing (`resume_parser.parse_resume`)
logic and does not change either of them.

Hash-based caching
------------------
If the same PDF was already reviewed (matched by `file_hash`), the cached
`ResumeReviewReport` is returned immediately without calling the AI service.
This eliminates the latency cost for repeat uploads and makes scores fully
deterministic.
"""

from __future__ import annotations

import logging
import traceback

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

logger = logging.getLogger(__name__)

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume file. Please upload a valid PDF.",
        ) from exc
    except ResumeParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read text from your resume. Make sure the PDF contains selectable text (not a scanned image).",
        ) from exc

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
    """Review a previously stored resume with the AI service and persist the report.

    Flow:
    1. Load the parsed resume by id.
    2. Check if a cached review already exists for this file hash (same PDF
       → instant return, no AI call).
    3. If not cached, call the Resume Reviewer Agent → persist the result.

    The response always matches `ResumeReviewReport` exactly (no envelope).
    """
    resume = resume_store_service.get_resume_by_id(db, resume_id)
    if resume is None or resume.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    parsed_resume = resume_store_service.get_parsed_resume(resume)
    if not parsed_resume.full_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This resume has no parsed content to review. Make sure the PDF contains selectable text.",
        )

    # ── Hash-based cache check ──────────────────────────────────────────────
    # If this exact file was reviewed before (same hash), reuse the cached
    # report — no AI call, no latency, deterministic scores.
    if resume.file_hash:
        cached_report = _get_cached_review_for_hash(db, resume.file_hash, current_user.id)
        if cached_report is not None:
            logger.info(
                "Resume review cache hit for hash=%s resume_id=%s",
                resume.file_hash[:12],
                resume_id,
            )
            return cached_report

    # ── Run the agent ───────────────────────────────────────────────────────
    try:
        report = await resume_reviewer.review_resume(parsed_resume)
    except resume_reviewer.ResumeReviewTimeoutError as exc:
        _log_review_failure(resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    except resume_reviewer.LLMRequestError as exc:
        _log_review_failure(resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except resume_reviewer.InvalidReviewResponseError as exc:
        _log_review_failure(resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        _log_review_failure(resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{type(exc).__name__}: {exc}",
        ) from exc

    # Persist after a successful agent run. Keep this outside the AI try/except
    # so DB failures are not mislabelled as OpenRouter/AI 502s — but still
    # return a structured error instead of a bare FastAPI 500.
    try:
        report_service.save_report(
            db,
            resume_id=resume.id,
            report_type=RESUME_REVIEW_REPORT_TYPE,
            content=report.model_dump(),
        )
    except Exception as exc:
        _log_review_failure(resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Review succeeded but could not be saved: {type(exc).__name__}: {exc}",
        ) from exc

    return report


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _log_review_failure(resume_id: int, exc: BaseException) -> None:
    """Log the exact exception behind a 502/504 without ever masking it.

    Logging itself must not raise (Windows console encoding can break on
    some characters); the HTTP handler must still return the real detail.
    """
    cause = exc.__cause__
    tb = traceback.extract_tb(exc.__traceback__)
    frame = tb[-1] if tb else None
    filename = frame.filename if frame else "?"
    lineno = frame.lineno if frame else "?"
    message = (
        f"RESUME_REVIEW_FAILURE resume_id={resume_id} "
        f"type={type(exc).__name__} msg={exc!s} "
        f"cause_type={type(cause).__name__ if cause else None} "
        f"cause={cause!s} file={filename} line={lineno}"
    )
    try:
        print(message, flush=True)
        traceback.print_exc()
        logger.exception(message)
    except Exception:
        # Never let logging prevent the real HTTPException from being raised.
        print(message, flush=True)
        traceback.print_exc()


def _get_cached_review_for_hash(
    db: Session,
    file_hash: str,
    user_id: int,
) -> ResumeReviewReport | None:
    """Return a previously persisted review for the given file hash, or None.

    Looks for any resume owned by `user_id` with `file_hash`, then checks
    whether a `resume_review` Report exists for it.
    """
    from app.models.report import Report

    cached_resume = resume_store_service.get_resume_by_hash(db, file_hash, user_id)
    if cached_resume is None:
        return None

    cached_report_row = report_service.get_latest_report(
        db, resume_id=cached_resume.id, report_type=RESUME_REVIEW_REPORT_TYPE
    )
    if cached_report_row is None:
        return None

    try:
        return ResumeReviewReport.model_validate(cached_report_row.content)
    except Exception:
        return None
