"""Tests for POST /job-descriptions/upload."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

VALID_PASSWORD = "supersecret1"

SAMPLE_JD_TEXT = """\
Software Engineer

Job Title: Software Engineer

About the role
We are looking for a Software Engineer to build APIs with FastAPI and React.

Requirements
- Python
- FastAPI
- PostgreSQL
"""


def _pdf_bytes_from_text(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 550, 780)
    overflow = page.insert_textbox(rect, text, fontsize=11, fontname="helv")
    assert overflow >= 0, "Sample JD text did not fit on one page"
    data = doc.tobytes()
    doc.close()
    return data


def _auth_headers(client, email: str = "jd.uploader@example.com") -> dict[str, str]:
    response = client.post(
        "/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def sample_pdf_bytes() -> bytes:
    return _pdf_bytes_from_text(SAMPLE_JD_TEXT)


def test_upload_pdf_job_description(
    client,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sample_pdf_bytes: bytes,
) -> None:
    monkeypatch.setattr(
        "app.services.job_description_service.settings.upload_dir",
        str(tmp_path),
    )
    headers = _auth_headers(client)

    response = client.post(
        "/job-descriptions/upload",
        headers=headers,
        files=[
            ("files", ("software_engineer_jd.pdf", sample_pdf_bytes, "application/pdf")),
        ],
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["uploaded"]) == 1
    item = body["uploaded"][0]
    assert item["filename"] == "software_engineer_jd.pdf"
    assert item["status"] == "success"
    assert item["id"]
    assert "Software Engineer" in item["role_title"]

    stored = list((tmp_path / "job_descriptions").glob("*_software_engineer_jd.pdf"))
    assert len(stored) == 1
    assert stored[0].read_bytes().startswith(b"%PDF")


def test_upload_txt_job_description(
    client,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.services.job_description_service.settings.upload_dir",
        str(tmp_path),
    )
    headers = _auth_headers(client, email="jd.txt@example.com")
    payload = SAMPLE_JD_TEXT.encode("utf-8")

    response = client.post(
        "/job-descriptions/upload",
        headers=headers,
        files=[
            ("files", ("product_manager.txt", payload, "text/plain")),
        ],
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["uploaded"]) == 1
    item = body["uploaded"][0]
    assert item["filename"] == "product_manager.txt"
    assert item["status"] == "success"
    assert "Software Engineer" in item["role_title"]

    stored = list((tmp_path / "job_descriptions").glob("*_product_manager.txt"))
    assert len(stored) == 1
    assert "FastAPI" in stored[0].read_text(encoding="utf-8")


def test_upload_multiple_job_descriptions(
    client,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sample_pdf_bytes: bytes,
) -> None:
    monkeypatch.setattr(
        "app.services.job_description_service.settings.upload_dir",
        str(tmp_path),
    )
    headers = _auth_headers(client, email="jd.multi@example.com")

    txt_payload = (
        "Job Title: Data Scientist\n\nAnalyze datasets and build models.\n"
    ).encode("utf-8")

    response = client.post(
        "/job-descriptions/upload",
        headers=headers,
        files=[
            ("files", ("software_engineer.pdf", sample_pdf_bytes, "application/pdf")),
            ("files", ("data_scientist.txt", txt_payload, "text/plain")),
        ],
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["uploaded"]) == 2
    filenames = {item["filename"] for item in body["uploaded"]}
    assert filenames == {"software_engineer.pdf", "data_scientist.txt"}
    assert all(item["status"] == "success" for item in body["uploaded"])
    assert all(item["id"] for item in body["uploaded"])

    jd_dir = tmp_path / "job_descriptions"
    assert len(list(jd_dir.glob("*.pdf"))) == 1
    assert len(list(jd_dir.glob("*.txt"))) == 1


def test_upload_rejects_unsupported_format(
    client,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.services.job_description_service.settings.upload_dir",
        str(tmp_path),
    )
    headers = _auth_headers(client, email="jd.bad@example.com")

    response = client.post(
        "/job-descriptions/upload",
        headers=headers,
        files=[
            ("files", ("notes.docx", b"PK fake docx", "application/octet-stream")),
        ],
    )

    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "unsupported" in detail or "pdf" in detail


def test_upload_rejects_empty_file(
    client,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.services.job_description_service.settings.upload_dir",
        str(tmp_path),
    )
    headers = _auth_headers(client, email="jd.empty@example.com")

    response = client.post(
        "/job-descriptions/upload",
        headers=headers,
        files=[
            ("files", ("empty.txt", b"", "text/plain")),
        ],
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_rejects_corrupt_pdf(
    client,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.services.job_description_service.settings.upload_dir",
        str(tmp_path),
    )
    headers = _auth_headers(client, email="jd.corrupt@example.com")

    response = client.post(
        "/job-descriptions/upload",
        headers=headers,
        files=[
            ("files", ("broken.pdf", b"%PDF-not-really", "application/pdf")),
        ],
    )

    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "parse" in detail or "pdf" in detail or "unable" in detail or "text" in detail


def test_upload_requires_auth(
    client,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.services.job_description_service.settings.upload_dir",
        str(tmp_path),
    )

    response = client.post(
        "/job-descriptions/upload",
        files=[
            ("files", ("role.txt", b"Job Title: Analyst\nDo analysis.\n", "text/plain")),
        ],
    )

    assert response.status_code == 401


def test_upload_persists_and_rejects_duplicate(
    client,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.services.job_description_service.settings.upload_dir",
        str(tmp_path),
    )
    headers = _auth_headers(client, email="jd.persist@example.com")
    payload = b"Job Title: Backend Engineer\n\nBuild reliable APIs with FastAPI.\n"

    response = client.post(
        "/job-descriptions/upload",
        headers=headers,
        files=[
            ("files", ("backend_engineer.txt", payload, "text/plain")),
        ],
    )

    assert response.status_code == 201
    item = response.json()["uploaded"][0]
    jd_id = item["id"]
    assert jd_id

    dup = client.post(
        "/job-descriptions/upload",
        headers=headers,
        files=[
            ("files", ("backend_engineer.txt", payload, "text/plain")),
        ],
    )
    assert dup.status_code == 400
    assert "duplicate" in dup.json()["detail"].lower()
