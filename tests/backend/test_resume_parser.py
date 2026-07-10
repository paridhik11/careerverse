"""Unit tests for the PyMuPDF resume parser (no OpenAI, no analysis)."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from app.services.resume_parser import (
    ResumeParseError,
    extract_email,
    extract_name,
    extract_phone,
    extract_sections,
    parse_resume,
)


SAMPLE_RESUME = """\
Jane Doe
jane.doe@example.com | (555) 123-4567 | linkedin.com/in/janedoe

Summary
Motivated software engineering student seeking an internship.

Skills
Python, FastAPI, React, TypeScript, PostgreSQL, Git

Education
B.S. Computer Science, State University, 2022 – 2026
GPA: 3.8

Experience
Software Engineering Intern — Acme Corp
June 2025 – August 2025
- Built REST APIs with FastAPI
- Wrote unit tests with pytest

Projects
CareerVerse AI
- Resume parsing and career recommendation platform
Campus Navigator
- Mobile app for campus wayfinding
"""


def _pdf_bytes_from_text(text: str) -> bytes:
    """Build a minimal one-page PDF containing `text` via PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 550, 780)
    # insert_textbox keeps newlines so section heuristics see real line breaks.
    overflow = page.insert_textbox(rect, text, fontsize=11, fontname="helv")
    assert overflow >= 0, "Sample resume text did not fit on one page"
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture()
def sample_pdf_bytes() -> bytes:
    return _pdf_bytes_from_text(SAMPLE_RESUME)


@pytest.fixture()
def sample_pdf_path(tmp_path: Path, sample_pdf_bytes: bytes) -> Path:
    path = tmp_path / "jane_doe_resume.pdf"
    path.write_bytes(sample_pdf_bytes)
    return path


def test_parse_resume_from_bytes(sample_pdf_bytes: bytes) -> None:
    parsed = parse_resume(sample_pdf_bytes)

    assert "Jane Doe" in parsed.full_text
    assert parsed.name == "Jane Doe"
    assert parsed.email == "jane.doe@example.com"
    assert parsed.phone is not None
    assert "555" in parsed.phone
    assert "Python" in parsed.skills
    assert "FastAPI" in parsed.skills
    assert "Computer Science" in parsed.education
    assert "Acme Corp" in parsed.experience
    assert "CareerVerse AI" in parsed.projects


def test_parse_resume_from_path(sample_pdf_path: Path) -> None:
    parsed = parse_resume(sample_pdf_path)
    assert parsed.email == "jane.doe@example.com"
    assert parsed.model_dump()  # structured JSON-ready dict


def test_parse_resume_returns_structured_dict(sample_pdf_bytes: bytes) -> None:
    payload = parse_resume(sample_pdf_bytes).model_dump()
    assert set(payload.keys()) == {
        "full_text",
        "name",
        "email",
        "phone",
        "skills",
        "education",
        "experience",
        "projects",
    }
    assert isinstance(payload["full_text"], str)
    assert payload["full_text"]


def test_extract_email_and_phone_helpers() -> None:
    text = "Reach me at alex@school.edu or call +1-415-555-0199 tonight."
    assert extract_email(text) == "alex@school.edu"
    phone = extract_phone(text)
    assert phone is not None
    assert "415" in phone


def test_extract_name_skips_contact_lines() -> None:
    lines = [
        "alex@school.edu",
        "(415) 555-0199",
        "https://github.com/alex",
        "Alex Rivera",
        "Skills",
    ]
    assert extract_name(lines) == "Alex Rivera"


def test_extract_sections_by_headings() -> None:
    lines = [
        "Alex Rivera",
        "Skills",
        "Python, SQL",
        "Education",
        "B.S. CS",
        "Experience",
        "Intern at Beta",
        "Projects",
        "Portfolio site",
        "Certifications",
        "AWS Cloud Practitioner",
    ]
    sections = extract_sections(lines)
    assert sections["skills"] == "Python, SQL"
    assert sections["education"] == "B.S. CS"
    assert sections["experience"] == "Intern at Beta"
    assert sections["projects"] == "Portfolio site"
    # Certifications is a boundary heading — must not leak into projects.
    assert "AWS" not in sections["projects"]


def test_missing_sections_are_empty_strings() -> None:
    pdf = _pdf_bytes_from_text(
        "Sam Lee\nsam@example.com\n\nSummary\nLooking for roles.\n"
    )
    parsed = parse_resume(pdf)
    assert parsed.name == "Sam Lee"
    assert parsed.email == "sam@example.com"
    assert parsed.skills == ""
    assert parsed.education == ""
    assert parsed.experience == ""
    assert parsed.projects == ""


def test_section_aliases_are_recognized() -> None:
    pdf = _pdf_bytes_from_text(
        "Pat Kim\npat@example.com\n\n"
        "Technical Skills\nJava, Spring\n\n"
        "Work Experience\nEngineer at Gamma\n\n"
        "Academic Background\nM.S. Data Science\n\n"
        "Personal Projects\nML classifier\n"
    )
    parsed = parse_resume(pdf)
    assert "Java" in parsed.skills
    assert "Gamma" in parsed.experience
    assert "Data Science" in parsed.education
    assert "ML classifier" in parsed.projects


def test_invalid_pdf_raises() -> None:
    with pytest.raises(ResumeParseError):
        parse_resume(b"this is not a pdf")


def test_empty_pdf_raises() -> None:
    doc = fitz.open()
    doc.new_page()  # blank page, no text
    blank = doc.tobytes()
    doc.close()
    with pytest.raises(ResumeParseError, match="no extractable text"):
        parse_resume(blank)
