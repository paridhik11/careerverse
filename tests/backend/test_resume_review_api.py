"""End-to-end tests for POST /resumes and POST /resumes/{id}/review.

The Resume Reviewer Agent (`app.agents.resume_reviewer.review_resume`) is
monkeypatched everywhere here so these tests never call Gemini for real —
agent behavior itself is covered by `test_resume_reviewer_agent.py`.
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from app.agents import resume_reviewer
from app.models.report import ResumeReviewReport

VALID_PASSWORD = "supersecret1"

VALID_REVIEW = ResumeReviewReport(
    overall_score=78,
    ats_score=65,
    summary="A solid early-career resume with strong projects but light on quantified impact.",
    strengths=["Strong technical projects", "Good programming skills", "Relevant coursework"],
    weaknesses=["Missing quantified achievements", "Weak project descriptions", "No internship experience"],
    ats_issues=["Missing keywords", "No dedicated technical skills section"],
    suggestions=["Quantify project impact.", "Add a technical skills section."],
    recommended_roles=["Software Engineer", "Backend Developer", "Data Analyst"],
)


def _pdf_bytes_from_text(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 550, 780)
    page.insert_textbox(rect, text, fontsize=11, fontname="helv")
    data = doc.tobytes()
    doc.close()
    return data


SAMPLE_RESUME_PDF = _pdf_bytes_from_text(
    "Jane Doe\njane.doe@example.com\n\n"
    "Skills\nPython, FastAPI, React\n\n"
    "Education\nB.S. Computer Science\n\n"
    "Projects\nCareerVerse AI - resume analysis platform\n"
)


def _auth_headers(client, email: str = "reviewer@example.com") -> dict[str, str]:
    response = client.post("/signup", json={"email": email, "password": VALID_PASSWORD})
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_resume(client, headers: dict[str, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> int:
    monkeypatch.setattr("app.services.resume_service.settings.upload_dir", str(tmp_path))
    response = client.post(
        "/resumes",
        headers=headers,
        files={"file": ("jane_doe_resume.pdf", SAMPLE_RESUME_PDF, "application/pdf")},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_resume_returns_parsed_content(client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    headers = _auth_headers(client)
    monkeypatch.setattr("app.services.resume_service.settings.upload_dir", str(tmp_path))

    response = client.post(
        "/resumes",
        headers=headers,
        files={"file": ("jane_doe_resume.pdf", SAMPLE_RESUME_PDF, "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["status"] == "parsed"
    assert "Python" in body["parsed_resume"]["skills"]


def test_create_resume_requires_auth(client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.resume_service.settings.upload_dir", str(tmp_path))
    response = client.post(
        "/resumes", files={"file": ("resume.pdf", SAMPLE_RESUME_PDF, "application/pdf")}
    )
    assert response.status_code == 401


def test_create_resume_rejects_non_pdf(client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    headers = _auth_headers(client)
    monkeypatch.setattr("app.services.resume_service.settings.upload_dir", str(tmp_path))

    response = client.post(
        "/resumes", headers=headers, files={"file": ("notes.txt", b"not a pdf", "text/plain")}
    )

    assert response.status_code == 400


def test_review_resume_returns_report_matching_schema_exactly(
    client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = _auth_headers(client)
    resume_id = _create_resume(client, headers, tmp_path, monkeypatch)

    async def fake_review(_parsed_resume):
        return VALID_REVIEW

    monkeypatch.setattr(resume_reviewer, "review_resume", fake_review)

    response = client.post(f"/resumes/{resume_id}/review", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {
        "overall_score",
        "ats_score",
        "summary",
        "strengths",
        "weaknesses",
        "ats_issues",
        "suggestions",
        "recommended_roles",
    }
    assert body["overall_score"] == 78
    assert body["ats_score"] == 65
    assert 3 <= len(body["strengths"]) <= 6
    assert 3 <= len(body["weaknesses"]) <= 6
    assert 3 <= len(body["recommended_roles"]) <= 5


def test_review_resume_requires_auth(client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    headers = _auth_headers(client)
    resume_id = _create_resume(client, headers, tmp_path, monkeypatch)

    response = client.post(f"/resumes/{resume_id}/review")

    assert response.status_code == 401


def test_review_resume_not_found_returns_404(client) -> None:
    headers = _auth_headers(client)

    response = client.post("/resumes/999999/review", headers=headers)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_review_resume_owned_by_another_user_returns_404(
    client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner_headers = _auth_headers(client, email="owner@example.com")
    resume_id = _create_resume(client, owner_headers, tmp_path, monkeypatch)

    other_headers = _auth_headers(client, email="intruder@example.com")
    response = client.post(f"/resumes/{resume_id}/review", headers=other_headers)

    assert response.status_code == 404


def test_review_resume_timeout_returns_504(client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    headers = _auth_headers(client)
    resume_id = _create_resume(client, headers, tmp_path, monkeypatch)

    async def fake_review(_parsed_resume):
        raise resume_reviewer.ResumeReviewTimeoutError("timed out")

    monkeypatch.setattr(resume_reviewer, "review_resume", fake_review)

    response = client.post(f"/resumes/{resume_id}/review", headers=headers)

    assert response.status_code == 504


def test_review_resume_gemini_error_returns_502(client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    headers = _auth_headers(client)
    resume_id = _create_resume(client, headers, tmp_path, monkeypatch)

    async def fake_review(_parsed_resume):
        raise resume_reviewer.GeminiRequestError("boom")

    monkeypatch.setattr(resume_reviewer, "review_resume", fake_review)

    response = client.post(f"/resumes/{resume_id}/review", headers=headers)

    assert response.status_code == 502


def test_review_resume_invalid_json_returns_502(client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    headers = _auth_headers(client)
    resume_id = _create_resume(client, headers, tmp_path, monkeypatch)

    async def fake_review(_parsed_resume):
        raise resume_reviewer.InvalidReviewResponseError("bad json")

    monkeypatch.setattr(resume_reviewer, "review_resume", fake_review)

    response = client.post(f"/resumes/{resume_id}/review", headers=headers)

    assert response.status_code == 502


def test_endpoints_are_visible_in_openapi_schema(client) -> None:
    schema = client.get("/openapi.json").json()

    assert "/resumes" in schema["paths"]
    assert "post" in schema["paths"]["/resumes"]
    assert "/resumes/{resume_id}/review" in schema["paths"]
    assert "post" in schema["paths"]["/resumes/{resume_id}/review"]
