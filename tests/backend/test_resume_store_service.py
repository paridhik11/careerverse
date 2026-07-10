"""Tests for resume persistence (`resume_store_service`) and `report_service`.

Uses a real in-memory SQLite database (not the `client` fixture) so we can
assert directly on the persisted `Resume` / `Report` rows.
"""

from __future__ import annotations

import io

import fitz
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.datastructures import Headers

from app.core.database import Base
from app.models.report import RESUME_REVIEW_REPORT_TYPE, Report
from app.models.resume import Resume
from app.services import report_service, resume_store_service


def _pdf_bytes_from_text(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 550, 780)
    page.insert_textbox(rect, text, fontsize=11, fontname="helv")
    data = doc.tobytes()
    doc.close()
    return data


def _upload_file(pdf_bytes: bytes, filename: str = "jane_doe_resume.pdf"):
    from fastapi import UploadFile

    return UploadFile(
        file=io.BytesIO(pdf_bytes),
        filename=filename,
        headers=Headers({"content-type": "application/pdf"}),
    )


@pytest.fixture()
def db_session(tmp_path) -> Session:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.mark.asyncio
async def test_ingest_resume_persists_parsed_content(
    db_session: Session, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.services.resume_service.settings.upload_dir", str(tmp_path))
    pdf_bytes = _pdf_bytes_from_text("Jane Doe\njane@example.com\n\nSkills\nPython, FastAPI\n")

    resume = await resume_store_service.ingest_resume(
        db_session, _upload_file(pdf_bytes), user_id=1
    )

    assert resume.id is not None
    assert resume.user_id == 1
    assert resume.file_name == "jane_doe_resume.pdf"
    assert "Python" in resume.parsed_resume["skills"]

    fetched = resume_store_service.get_resume_by_id(db_session, resume.id)
    assert fetched is not None
    assert fetched.id == resume.id

    parsed = resume_store_service.get_parsed_resume(fetched)
    assert parsed.email == "jane@example.com"


def test_get_resume_by_id_returns_none_when_missing(db_session: Session) -> None:
    assert resume_store_service.get_resume_by_id(db_session, 9999) is None


def test_save_report_persists_a_row(db_session: Session, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.resume_service.settings.upload_dir", str(tmp_path))
    resume = Resume(
        user_id=1,
        file_name="resume.pdf",
        file_path=str(tmp_path / "resume.pdf"),
        parsed_resume={"full_text": "some text", "skills": "", "education": "", "experience": "", "projects": ""},
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    content = {
        "overall_score": 80,
        "ats_score": 70,
        "summary": "Solid resume.",
        "strengths": ["a", "b", "c"],
        "weaknesses": ["a", "b", "c"],
        "ats_issues": [],
        "suggestions": [],
        "recommended_roles": ["Software Engineer", "Backend Developer", "Data Analyst"],
    }

    report = report_service.save_report(
        db_session, resume_id=resume.id, report_type=RESUME_REVIEW_REPORT_TYPE, content=content
    )

    assert report.id is not None
    assert report.report_type == RESUME_REVIEW_REPORT_TYPE

    stored = db_session.query(Report).filter(Report.resume_id == resume.id).all()
    assert len(stored) == 1
    assert stored[0].content["overall_score"] == 80
