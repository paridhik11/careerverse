"""RAG integration smoke test.

This script exercises the full RAG pipeline end-to-end:
  1. Creates a temporary ChromaDB directory.
  2. Indexes two sample job descriptions.
  3. Loads a sample resume.
  4. Calls retrieve_relevant_job_descriptions().
  5. Prints the retrieved JD titles and chunk counts.

Usage (from the careerverse/ root with venv activated):
    python tests/backend/rag_smoke_test.py

A real OPENAI_API_KEY must be set in the environment (or backend/.env).
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap — add backend/ to sys.path so `app.*` imports resolve.
# ---------------------------------------------------------------------------

BACKEND_ROOT = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Load .env so OPENAI_API_KEY is available when running the script directly.
try:
    from dotenv import load_dotenv

    env_file = BACKEND_ROOT / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass  # python-dotenv not installed in this env; rely on shell environment.

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_RESUME = """\
Jane Doe
jane@example.com | linkedin.com/in/janedoe | github.com/janedoe

SUMMARY
Software Engineer with 3 years of experience building scalable Python APIs.
Proficient in FastAPI, PostgreSQL, Docker, and React.

EXPERIENCE
Software Engineer — Acme Corp (2021–present)
- Built REST APIs with FastAPI serving 1M+ requests/day.
- Reduced PostgreSQL query latency by 40% through indexing.
- Implemented CI/CD pipelines with GitHub Actions and Docker.

EDUCATION
B.Sc. Computer Science — State University (2021)

SKILLS
Python, FastAPI, PostgreSQL, Docker, React, TypeScript, Git, Linux
"""

SAMPLE_JDS = [
    {
        "id": "smoke-1",
        "filename": "software_engineer.txt",
        "role_title": "Software Engineer",
        "text": """\
Software Engineer

Job Title: Software Engineer
Location: Remote

About the Role
We are hiring a Software Engineer to build and maintain scalable Python APIs.

Requirements
- 2+ years of Python development experience
- Strong FastAPI or Django REST framework knowledge
- PostgreSQL and SQLAlchemy experience
- Familiarity with Docker and Kubernetes
- Experience with CI/CD pipelines (GitHub Actions, Jenkins)

Responsibilities
- Build, test, and ship backend services using Python and FastAPI
- Own database schema design and query optimisation
- Collaborate with the frontend team on API contracts
""",
    },
    {
        "id": "smoke-2",
        "filename": "data_scientist.txt",
        "role_title": "Data Scientist",
        "text": """\
Data Scientist

Job Title: Data Scientist
Location: Hybrid

About the Role
We are looking for a Data Scientist to build predictive models and data pipelines.

Requirements
- 2+ years working with pandas, scikit-learn, and matplotlib
- Strong SQL and data wrangling skills
- Experience deploying ML models to production (Flask/FastAPI)
- Familiarity with cloud platforms (AWS SageMaker or GCP Vertex AI)

Responsibilities
- Analyse large datasets and derive actionable insights
- Build and evaluate machine learning models
- Maintain data pipelines and dashboards
""",
    },
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 60)
    print("CareerVerse RAG Smoke Test")
    print("=" * 60)

    # Use a temporary directory so this script never writes to the real vector_db.
    with tempfile.TemporaryDirectory(prefix="cv_rag_smoke_") as tmp_dir:
        print(f"\n[+] Using temp ChromaDB directory: {tmp_dir}\n")

        # Patch the persist dir at runtime before importing store.
        os.environ["CHROMA_PERSIST_DIR"] = tmp_dir

        from app.rag.store import index_job_description
        from app.rag.retriever import retrieve_relevant_job_descriptions

        # Step 1 — index sample JDs.
        print("[+] Indexing sample job descriptions …")
        for jd in SAMPLE_JDS:
            n = index_job_description(
                job_description_id=jd["id"],
                filename=jd["filename"],
                role_title=jd["role_title"],
                parsed_text=jd["text"],
            )
            print(f"    ✓ '{jd['role_title']}' — {n} chunks indexed")

        # Step 2 — query with the sample resume.
        print("\n[+] Querying with sample resume …")
        results = retrieve_relevant_job_descriptions(SAMPLE_RESUME, top_k=8)

        if not results:
            print("\n[!] No results returned — check your OPENAI_API_KEY.\n")
            sys.exit(1)

        print(f"\n[+] Retrieved {len(results)} matching job description(s):\n")
        for rank, item in enumerate(results, start=1):
            print(f"  {rank}. {item['role_title']} (id={item['job_description_id']})")
            print(f"     {len(item['chunks'])} chunk(s) retrieved")
            print(f"     First chunk preview: {item['chunks'][0][:120].strip()!r}")
            print()

        print("=" * 60)
        print("Smoke test PASSED.")
        print("=" * 60)


if __name__ == "__main__":
    main()
