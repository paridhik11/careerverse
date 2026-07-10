"""Tests for POST /resume/upload."""

from pathlib import Path

import pytest

VALID_PASSWORD = "supersecret1"
MINIMAL_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def _auth_headers(client) -> dict[str, str]:
    response = client.post(
        "/signup",
        json={"email": "resume.uploader@example.com", "password": VALID_PASSWORD},
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_upload_resume_success(client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.resume_service.settings.upload_dir", str(tmp_path))
    headers = _auth_headers(client)

    response = client.post(
        "/resume/upload",
        headers=headers,
        files={"file": ("jane_doe_resume.pdf", MINIMAL_PDF, "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["file_name"] == "jane_doe_resume.pdf"
    assert body["status"] == "uploaded"
    assert Path(body["file_path"]).exists()
    assert Path(body["file_path"]).read_bytes().startswith(b"%PDF")


def test_upload_rejects_non_pdf(client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.resume_service.settings.upload_dir", str(tmp_path))
    headers = _auth_headers(client)

    response = client.post(
        "/resume/upload",
        headers=headers,
        files={"file": ("notes.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert "pdf" in response.json()["detail"].lower()


def test_upload_requires_auth(client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.resume_service.settings.upload_dir", str(tmp_path))

    response = client.post(
        "/resume/upload",
        files={"file": ("resume.pdf", MINIMAL_PDF, "application/pdf")},
    )

    assert response.status_code == 401
