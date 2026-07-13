"""End-to-end tests for POST /job-matches/{resume_id}.

The RAG retriever (`app.rag.retriever.retrieve_relevant_job_descriptions`)
and the Career Recommendation Agent
(`app.agents.career_advisor.generate_career_matches`) are monkeypatched
everywhere here so these tests never call Gemini or ChromaDB for real —
agent behavior itself is covered by `test_career_advisor_agent.py`.
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from app.agents import career_advisor
from app.models.job_match import CareerMatchRecommendation
from app.services import job_match_service

VALID_PASSWORD = "supersecret1"

RETRIEVED_JDS = [
    {"job_description_id": "1", "role_title": "Software Engineer", "chunks": ["Build APIs."]},
    {"job_description_id": "2", "role_title": "Data Scientist", "chunks": ["Analyze data."]},
    {"job_description_id": "3", "role_title": "Product Manager", "chunks": ["Run sprints."]},
]

THREE_MATCHES = [
    CareerMatchRecommendation(
        job_description_id="1",
        role_title="Software Engineer",
        match_percent=91,
        confidence_score="High",
        reasoning="Strong Python and FastAPI background matches the JD's core stack directly.",
        career_overview="Builds and maintains backend services and APIs for the product.",
        missing_skills=["Kubernetes", "GraphQL"],
        rank=1,
    ),
    CareerMatchRecommendation(
        job_description_id="2",
        role_title="Data Scientist",
        match_percent=68,
        confidence_score="Medium",
        reasoning="Some data analysis exposure but limited modeling experience overall.",
        career_overview="Analyzes datasets and builds predictive models for the business.",
        missing_skills=["scikit-learn", "Statistics"],
        rank=2,
    ),
    CareerMatchRecommendation(
        job_description_id="3",
        role_title="Product Manager",
        match_percent=45,
        confidence_score="Low",
        reasoning="Resume shows little product or stakeholder management experience yet.",
        career_overview="Owns the roadmap and coordinates sprint planning across teams.",
        missing_skills=["Stakeholder management", "Roadmapping"],
        rank=3,
    ),
]


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


def _auth_headers(client, email: str = "matcher@example.com") -> dict[str, str]:
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


def _fake_retrieve(*_args, **_kwargs):
    return RETRIEVED_JDS


async def _fake_generate_career_matches(*_args, **_kwargs):
    return THREE_MATCHES


@pytest.fixture()
def mocked_pipeline(monkeypatch: pytest.MonkeyPatch):
    """Patch retrieval + agent so the endpoint runs end-to-end without external calls."""
    monkeypatch.setattr(job_match_service, "retrieve_relevant_job_descriptions", _fake_retrieve)
    monkeypatch.setattr(career_advisor, "generate_career_matches", _fake_generate_career_matches)


def _seed_job_descriptions(client) -> None:
    """Use the TestClient's own overridden DB session to seed JobDescription rows."""
    from app.core.database import get_db
    from app.main import app

    override = app.dependency_overrides[get_db]
    gen = override()
    db = next(gen)
    try:
        from app.models.job_description import JobDescription

        for jd_id, role_title in [
            (1, "Software Engineer"),
            (2, "Data Scientist"),
            (3, "Product Manager"),
        ]:
            db.add(
                JobDescription(
                    id=jd_id,
                    filename=f"{role_title}.pdf",
                    file_type="pdf",
                    file_path=f"/tmp/{role_title}.pdf",
                    role_title=role_title,
                    parsed_text=f"{role_title} job description text.",
                    content_hash=f"hash-{jd_id}",
                )
            )
        db.commit()
    finally:
        gen.close()


def test_create_job_matches_returns_exactly_three_ranked_matches(
    client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mocked_pipeline
) -> None:
    headers = _auth_headers(client)
    resume_id = _create_resume(client, headers, tmp_path, monkeypatch)
    _seed_job_descriptions(client)

    response = client.post(f"/job-matches/{resume_id}", headers=headers)

    assert response.status_code == 200
    body = response.json()
    matches = body["matches"]
    assert len(matches) == 3

    ranks = sorted(m["rank"] for m in matches)
    assert ranks == [1, 2, 3]

    jd_ids = {m["job_description_id"] for m in matches}
    assert len(jd_ids) == 3

    for match in matches:
        assert 0 <= match["match_percent"] <= 100
        assert match["resume_id"] == resume_id
        assert match["is_chosen"] is False
        assert match["confidence_score"] in {"High", "Medium", "Low"}

    missing_skills_sets = [tuple(sorted(m["missing_skills"])) for m in matches]
    assert len(set(missing_skills_sets)) == 3


def test_create_job_matches_requires_auth(
    client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mocked_pipeline
) -> None:
    headers = _auth_headers(client)
    resume_id = _create_resume(client, headers, tmp_path, monkeypatch)
    _seed_job_descriptions(client)

    response = client.post(f"/job-matches/{resume_id}")

    assert response.status_code == 401


def test_create_job_matches_resume_not_found_returns_404(client, mocked_pipeline) -> None:
    headers = _auth_headers(client)

    response = client.post("/job-matches/999999", headers=headers)

    assert response.status_code == 404


def test_create_job_matches_owned_by_another_user_returns_404(
    client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mocked_pipeline
) -> None:
    owner_headers = _auth_headers(client, email="owner2@example.com")
    resume_id = _create_resume(client, owner_headers, tmp_path, monkeypatch)
    _seed_job_descriptions(client)

    other_headers = _auth_headers(client, email="intruder2@example.com")
    response = client.post(f"/job-matches/{resume_id}", headers=other_headers)

    assert response.status_code == 404


def test_create_job_matches_returns_400_when_no_jds_retrieved(
    client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = _auth_headers(client, email="nojd@example.com")
    resume_id = _create_resume(client, headers, tmp_path, monkeypatch)

    monkeypatch.setattr(job_match_service, "retrieve_relevant_job_descriptions", lambda *a, **k: [])

    response = client.post(f"/job-matches/{resume_id}", headers=headers)

    assert response.status_code == 400


def test_create_job_matches_agent_error_returns_502(
    client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = _auth_headers(client, email="aierror@example.com")
    resume_id = _create_resume(client, headers, tmp_path, monkeypatch)
    _seed_job_descriptions(client)

    monkeypatch.setattr(job_match_service, "retrieve_relevant_job_descriptions", _fake_retrieve)

    async def failing_generate(*_args, **_kwargs):
        raise career_advisor.InvalidCareerAdvisorResponseError("bad json")

    monkeypatch.setattr(career_advisor, "generate_career_matches", failing_generate)

    response = client.post(f"/job-matches/{resume_id}", headers=headers)

    assert response.status_code == 502


def test_create_job_matches_persists_rows_linked_to_job_descriptions(
    client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mocked_pipeline
) -> None:
    headers = _auth_headers(client, email="persist@example.com")
    resume_id = _create_resume(client, headers, tmp_path, monkeypatch)
    _seed_job_descriptions(client)

    response = client.post(f"/job-matches/{resume_id}", headers=headers)
    assert response.status_code == 200

    from app.core.database import get_db
    from app.main import app

    override = app.dependency_overrides[get_db]
    gen = override()
    db = next(gen)
    try:
        from app.models.job_match import JobMatch

        rows = db.query(JobMatch).filter(JobMatch.resume_id == resume_id).all()
        assert len(rows) == 3
        for row in rows:
            assert row.job_description_id in {1, 2, 3}
            assert row.is_chosen is False
    finally:
        gen.close()


def test_endpoint_is_visible_in_openapi_schema(client) -> None:
    schema = client.get("/openapi.json").json()

    assert "/job-matches/{resume_id}" in schema["paths"]
    assert "post" in schema["paths"]["/job-matches/{resume_id}"]
