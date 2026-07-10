"""Business logic for resume file uploads.

Validates that the payload is a PDF and writes it under the configured
uploads directory. Does not parse the PDF, call AI, or touch the database.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.models.resume import ResumeUploadResponse

PDF_MAGIC = b"%PDF"
MAX_RESUME_BYTES = 10 * 1024 * 1024  # 10 MB — keeps accidental huge uploads out


class InvalidResumeError(Exception):
    """Raised when the uploaded file fails PDF validation."""


def _resolve_upload_dir() -> Path:
    """Return the uploads directory as an absolute path, creating it if needed."""
    upload_dir = Path(settings.upload_dir)
    if not upload_dir.is_absolute():
        # settings.upload_dir is relative to the process cwd (typically backend/).
        upload_dir = Path.cwd() / upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir.resolve()


def _sanitize_filename(filename: str) -> str:
    """Strip path components and keep a safe basename for disk storage."""
    name = Path(filename).name.strip()
    # Collapse anything that isn't alphanumeric, dot, dash, or underscore.
    safe = re.sub(r"[^\w.\-]+", "_", name, flags=re.UNICODE)
    return safe or "resume.pdf"


def _is_pdf(filename: str | None, content_type: str | None, header: bytes) -> bool:
    """Require a .pdf extension and PDF magic bytes; content-type is advisory."""
    if not filename or not filename.lower().endswith(".pdf"):
        return False
    if not header.startswith(PDF_MAGIC):
        return False
    # Some browsers send application/octet-stream; accept that if magic matches.
    if content_type and content_type not in (
        "application/pdf",
        "application/octet-stream",
        "binary/octet-stream",
    ):
        return False
    return True


async def save_resume_upload(file: UploadFile) -> ResumeUploadResponse:
    """Validate and persist a resume PDF. Returns metadata for the client."""
    if file.filename is None or not file.filename.strip():
        raise InvalidResumeError("A file name is required.")

    # Read a small prefix first so we can reject non-PDFs without buffering
    # the entire body when the magic check fails early.
    header = await file.read(8)
    if not _is_pdf(file.filename, file.content_type, header):
        raise InvalidResumeError("Only PDF resumes are accepted.")

    rest = await file.read()
    payload = header + rest
    if len(payload) > MAX_RESUME_BYTES:
        raise InvalidResumeError(
            f"Resume must be {MAX_RESUME_BYTES // (1024 * 1024)} MB or smaller."
        )
    if len(payload) == 0:
        raise InvalidResumeError("The uploaded file is empty.")

    original_name = Path(file.filename).name
    stored_name = f"{uuid.uuid4().hex}_{_sanitize_filename(original_name)}"
    if not stored_name.lower().endswith(".pdf"):
        stored_name = f"{stored_name}.pdf"

    destination = _resolve_upload_dir() / stored_name
    destination.write_bytes(payload)

    return ResumeUploadResponse(
        file_name=original_name,
        file_path=str(destination),
        status="uploaded",
    )
