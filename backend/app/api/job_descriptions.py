"""Job description route handlers.

Routes only accept multipart uploads and translate service-layer errors into
HTTP responses. Validation, parsing, and persistence live in
`app.services.job_description_service` / `job_description_parser`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.job_description import (
    JobDescriptionUploadResponse,
    SampleJobDescriptionListResponse,
    SeedSampleJobDescriptionsRequest,
)
from app.models.user import User
from app.services import job_description_service

router = APIRouter(prefix="/job-descriptions", tags=["job-descriptions"])


@router.get(
    "/samples",
    response_model=SampleJobDescriptionListResponse,
    summary="List pre-seeded sample job descriptions for the dashboard picker.",
)
async def list_sample_job_descriptions(
    _current_user: User = Depends(get_current_user),
) -> SampleJobDescriptionListResponse:
    samples = job_description_service.list_sample_job_descriptions()
    return SampleJobDescriptionListResponse(samples=samples)


@router.post(
    "/samples/seed",
    response_model=JobDescriptionUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Persist selected sample JDs into the DB and index them for RAG.",
)
async def seed_sample_job_descriptions(
    body: SeedSampleJobDescriptionsRequest,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobDescriptionUploadResponse:
    try:
        return job_description_service.seed_sample_job_descriptions(db, body.sample_ids)
    except job_description_service.InvalidJobDescriptionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/upload",
    response_model=JobDescriptionUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload one or more job description PDF/TXT files.",
)
async def upload_job_descriptions(
    files: list[UploadFile] = File(..., description="One or more JD PDF or TXT files"),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobDescriptionUploadResponse:
    """Accept multipart PDF/TXT uploads, extract text, and persist JobDescription rows.

    Auth is required because JD upload sits after login in the user journey.
    Embeddings / ChromaDB indexing are intentionally out of scope for this milestone.
    """
    try:
        return await job_description_service.save_job_description_uploads(db, files)
    except job_description_service.InvalidJobDescriptionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
