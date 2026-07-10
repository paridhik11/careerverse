"""Heuristic resume PDF parser using PyMuPDF.

Extracts full text plus contact fields and common section bodies. Does not call
OpenAI or score/analyze the resume — that belongs to the Resume Reviewer Agent.
"""

from __future__ import annotations

import re
from pathlib import Path

import fitz  # PyMuPDF

from app.models.resume import ParsedResume

# Contact patterns — intentionally simple; resumes vary widely in formatting.
EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
)
# Covers (555) 123-4567, 555-123-4567, +1 555 123 4567, and similar.
PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s.\-]?)?"
    r"(?:\(?\d{2,4}\)?[\s.\-]?)?"
    r"\d{3,4}[\s.\-]?\d{3,4}"
    r"(?:\s*(?:x|ext\.?)\s*\d{1,5})?",
    re.IGNORECASE,
)

# Map canonical section keys → heading aliases (matched case-insensitively).
SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "skills": (
        "skills",
        "technical skills",
        "core competencies",
        "technologies",
        "tech stack",
        "key skills",
    ),
    "education": (
        "education",
        "academic background",
        "academics",
        "academic history",
    ),
    "experience": (
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "work history",
        "employment history",
    ),
    "projects": (
        "projects",
        "personal projects",
        "academic projects",
        "key projects",
        "selected projects",
    ),
}

# Other common headings — used only to bound section slices, not returned.
_BOUNDARY_ALIASES: tuple[str, ...] = (
    "summary",
    "professional summary",
    "profile",
    "objective",
    "certifications",
    "certificates",
    "awards",
    "achievements",
    "publications",
    "languages",
    "interests",
    "hobbies",
    "references",
    "volunteer",
    "volunteering",
    "activities",
    "leadership",
)

_URL_RE = re.compile(r"https?://|www\.|linkedin\.com|github\.com", re.IGNORECASE)
_NAME_LINE_RE = re.compile(r"^[A-Z][A-Za-z'’\-]+(?:\s+[A-Z][A-Za-z'’\-]+){0,3}$")


class ResumeParseError(Exception):
    """Raised when a PDF cannot be opened or yields no usable text."""


def _open_document(source: str | Path | bytes) -> fitz.Document:
    """Open a PDF from a filesystem path or in-memory bytes."""
    try:
        if isinstance(source, (str, Path)):
            return fitz.open(str(source))
        return fitz.open(stream=source, filetype="pdf")
    except Exception as exc:  # PyMuPDF raises FileDataError / RuntimeError variants
        raise ResumeParseError(f"Unable to open resume PDF: {exc}") from exc


def extract_full_text(source: str | Path | bytes) -> str:
    """Pull plain text from every page with PyMuPDF, preserving line breaks."""
    doc = _open_document(source)
    try:
        if doc.page_count == 0:
            raise ResumeParseError("PDF has no pages.")
        parts: list[str] = []
        for page in doc:
            # "text" mode is the default layout-aware extractor — good enough
            # for section heuristics without needing block/dict geometry.
            page_text = page.get_text("text")
            if page_text:
                parts.append(page_text)
        full = "\n".join(parts).strip()
        if not full:
            raise ResumeParseError("PDF contains no extractable text.")
        return full
    finally:
        doc.close()


def _normalize_lines(full_text: str) -> list[str]:
    """Split on newlines and drop blank lines while keeping order."""
    return [line.strip() for line in full_text.splitlines() if line.strip()]


def _looks_like_phone(candidate: str) -> bool:
    """Require enough digits so short numbers (years, GPAs) are not phones."""
    digits = re.sub(r"\D", "", candidate)
    return 10 <= len(digits) <= 15


def extract_email(full_text: str) -> str | None:
    match = EMAIL_RE.search(full_text)
    return match.group(0) if match else None


def extract_phone(full_text: str) -> str | None:
    for match in PHONE_RE.finditer(full_text):
        candidate = match.group(0).strip()
        if _looks_like_phone(candidate):
            return candidate
    return None


def extract_name(lines: list[str]) -> str | None:
    """Best-effort name: first header-ish line that is not contact/URL/section."""
    all_headers = _all_heading_labels()
    for line in lines[:12]:
        lowered = line.lower().rstrip(":")
        if lowered in all_headers:
            continue
        if EMAIL_RE.search(line) or _URL_RE.search(line):
            continue
        if PHONE_RE.fullmatch(line) and _looks_like_phone(line):
            continue
        # Prefer Title Case / ALL CAPS name patterns (2–4 tokens).
        if _NAME_LINE_RE.match(line):
            return line
        # Fallback: short line without digits, not a lone location fragment.
        word_count = len(line.split())
        if 1 <= word_count <= 4 and not re.search(r"\d", line) and "@" not in line:
            return line
    return None


def _all_heading_labels() -> set[str]:
    labels: set[str] = set(_BOUNDARY_ALIASES)
    for aliases in SECTION_ALIASES.values():
        labels.update(aliases)
    return labels


def _heading_key(line: str) -> str | None:
    """Return the canonical section key if `line` is a known heading, else None."""
    cleaned = line.strip().rstrip(":").strip().lower()
    # Allow headings like "SKILLS" or "Technical Skills |"
    cleaned = cleaned.split("|")[0].strip()
    for key, aliases in SECTION_ALIASES.items():
        if cleaned in aliases:
            return key
    if cleaned in _BOUNDARY_ALIASES:
        return "__boundary__"
    return None


def extract_sections(lines: list[str]) -> dict[str, str]:
    """Slice body text between known section headings.

    A line is treated as a heading when it matches a known alias (optionally
    ending with ':'). Content runs until the next recognized heading.
    """
    sections: dict[str, str] = {
        "skills": "",
        "education": "",
        "experience": "",
        "projects": "",
    }
    current: str | None = None
    buckets: dict[str, list[str]] = {key: [] for key in sections}

    for line in lines:
        key = _heading_key(line)
        if key is not None:
            current = key if key != "__boundary__" else None
            continue
        if current in buckets:
            buckets[current].append(line)

    for key, body_lines in buckets.items():
        sections[key] = "\n".join(body_lines).strip()
    return sections


def parse_resume(source: str | Path | bytes) -> ParsedResume:
    """Parse a resume PDF into structured JSON-ready fields.

    Parameters
    ----------
    source:
        Filesystem path or raw PDF bytes.

    Returns
    -------
    ParsedResume
        Pydantic model with full_text, contact fields, and section bodies.
    """
    full_text = extract_full_text(source)
    lines = _normalize_lines(full_text)
    sections = extract_sections(lines)

    return ParsedResume(
        full_text=full_text,
        name=extract_name(lines),
        email=extract_email(full_text),
        phone=extract_phone(full_text),
        skills=sections["skills"],
        education=sections["education"],
        experience=sections["experience"],
        projects=sections["projects"],
    )
