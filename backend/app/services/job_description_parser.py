"""Extract plain text from job description PDF or TXT files.

Uses PyMuPDF for PDFs and UTF-8 (with latin-1 fallback) for plain text.
Does not chunk, embed, or call Gemini — that belongs to later RAG milestones.
"""

from __future__ import annotations

import re
from pathlib import Path

import fitz  # PyMuPDF

# Common prefixes that often precede a role title on the first content lines.
_TITLE_PREFIX_RE = re.compile(
    r"^(?:job\s*title|position(?:\s*title)?|role(?:\s*title)?|title)\s*[:\-–—]\s*(.+)$",
    re.IGNORECASE,
)

# Filename noise to strip when deriving a role title from the basename.
_FILENAME_NOISE_RE = re.compile(
    r"(?i)(?:[\s_\-]*(?:jd|job[\s_\-]*desc(?:ription)?|posting|opening))+",
)


class JobDescriptionParseError(Exception):
    """Raised when a JD file cannot be opened or yields no usable text."""


def _open_pdf(source: str | Path | bytes) -> fitz.Document:
    """Open a PDF from a filesystem path or in-memory bytes."""
    try:
        if isinstance(source, (str, Path)):
            return fitz.open(str(source))
        return fitz.open(stream=source, filetype="pdf")
    except Exception as exc:  # PyMuPDF raises FileDataError / RuntimeError variants
        raise JobDescriptionParseError(f"Unable to open job description PDF: {exc}") from exc


def extract_text_from_pdf(source: str | Path | bytes) -> str:
    """Pull plain text from every page with PyMuPDF."""
    doc = _open_pdf(source)
    try:
        if doc.page_count == 0:
            raise JobDescriptionParseError("PDF has no pages.")
        parts: list[str] = []
        for page in doc:
            page_text = page.get_text("text")
            if page_text:
                parts.append(page_text)
        full = "\n".join(parts).strip()
        if not full:
            raise JobDescriptionParseError("PDF contains no extractable text.")
        return full
    finally:
        doc.close()


def extract_text_from_txt(source: str | Path | bytes) -> str:
    """Read a plain-text job description as UTF-8 (latin-1 fallback)."""
    if isinstance(source, (str, Path)):
        raw = Path(source).read_bytes()
    else:
        raw = source

    if not raw:
        raise JobDescriptionParseError("Text file is empty.")

    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            text = raw.decode(encoding).strip()
            break
        except UnicodeDecodeError:
            continue
    else:
        raise JobDescriptionParseError("Text file could not be decoded.")

    if not text:
        raise JobDescriptionParseError("Text file contains no extractable text.")
    return text


def extract_text(source: str | Path | bytes, file_type: str) -> str:
    """Extract text for a detected file type (`pdf` or `txt`)."""
    normalized = file_type.lower().lstrip(".")
    if normalized == "pdf":
        return extract_text_from_pdf(source)
    if normalized == "txt":
        return extract_text_from_txt(source)
    raise JobDescriptionParseError(f"Unsupported file type for parsing: {file_type}")


def role_title_from_filename(filename: str) -> str | None:
    """Best-effort role title from a basename like `software_engineer_jd.pdf`."""
    stem = Path(filename).stem.strip()
    if not stem:
        return None
    cleaned = _FILENAME_NOISE_RE.sub(" ", stem)
    cleaned = re.sub(r"[_\-]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .-_")
    if not cleaned or cleaned.lower() in {"jd", "job", "description"}:
        return None
    return cleaned.title()


def role_title_from_content(parsed_text: str) -> str | None:
    """Best-effort role title from early lines of the JD body."""
    lines = [line.strip() for line in parsed_text.splitlines() if line.strip()]
    for line in lines[:15]:
        match = _TITLE_PREFIX_RE.match(line)
        if match:
            title = match.group(1).strip(" .-_|")
            if title:
                return title
    # Fallback: first short line that looks like a heading, not a sentence.
    for line in lines[:8]:
        if len(line) > 80 or line.endswith("."):
            continue
        if _TITLE_PREFIX_RE.match(line):
            continue
        word_count = len(line.split())
        if 1 <= word_count <= 8:
            return line.strip(" .-_|")
    return None


def extract_role_title(filename: str, parsed_text: str) -> str:
    """Prefer content-derived title; fall back to filename; else empty string."""
    from_content = role_title_from_content(parsed_text)
    if from_content:
        return from_content
    from_filename = role_title_from_filename(filename)
    return from_filename or ""
