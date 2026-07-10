"""Resume route handlers.

Routes only accept the multipart upload and translate service-layer errors
into HTTP responses. Validation and disk I/O live in `app.services.resume_service`.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.deps import get_current_user
from app.models.resume import ResumeUploadResponse
from app.models.user import User
from app.services import resume_service

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume(
    file: UploadFile = File(..., description="Resume PDF"),
    _current_user: User = Depends(get_current_user),
) -> ResumeUploadResponse:
    """Accept a multipart PDF upload and store it under uploads/.

    Auth is required because resume upload sits after login in the user journey.
    Ownership wiring (associating the file with a DB row) comes in a later milestone.
    """
    try:
        return await resume_service.save_resume_upload(file)
    except resume_service.InvalidResumeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
