"""Rule-based ATS scoring for deterministic resume evaluation.

Computes `overall_score` and `ats_score` from the parsed resume text using
reproducible heuristics — no LLM calls. Gemini then *explains* these scores
rather than inventing them, which eliminates non-determinism in scoring.

Scoring dimensions (each 0-100):
    - structure_score:   presence of expected resume sections
    - skills_score:      richness of the skills section
    - experience_score:  quality signals in experience (action verbs, metrics)
    - projects_score:    presence and depth of projects
    - education_score:   presence of education section
    - formatting_score:  length, density, and formatting hygiene signals

`overall_score` = weighted average across all dimensions.
`ats_score`     = weighted average of ATS-relevant sub-scores.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.resume import ParsedResume

# ─── Action verbs that signal strong bullet points ───────────────────────────

ACTION_VERBS: frozenset[str] = frozenset({
    "architected", "automated", "built", "coached", "collaborated", "coordinated",
    "created", "defined", "delivered", "deployed", "designed", "developed",
    "drove", "engineered", "enhanced", "established", "evaluated", "executed",
    "facilitated", "implemented", "improved", "increased", "integrated", "launched",
    "led", "managed", "mentored", "migrated", "modelled", "modernised", "modernized",
    "monitored", "optimised", "optimized", "owned", "partnered", "planned", "presented",
    "produced", "reduced", "refactored", "resolved", "reviewed", "scaled", "shipped",
    "simplified", "spearheaded", "streamlined", "transformed", "validated", "wrote",
})

# ─── Expected resume section headings ────────────────────────────────────────

REQUIRED_SECTIONS: list[tuple[str, list[str]]] = [
    ("experience", ["experience", "work experience", "work history", "employment", "professional experience"]),
    ("education", ["education", "academic background", "qualifications"]),
    ("skills", ["skills", "technical skills", "technologies", "competencies", "tools"]),
    ("contact", ["email", "phone", "linkedin", "github", "portfolio"]),
]

OPTIONAL_SECTIONS: list[tuple[str, list[str]]] = [
    ("projects", ["projects", "personal projects", "side projects", "open source"]),
    ("summary", ["summary", "objective", "profile", "about me"]),
    ("certifications", ["certifications", "certificates", "licenses"]),
    ("awards", ["awards", "achievements", "honors", "honours"]),
]

# ─── Quantification patterns (numbers / % in bullet points) ──────────────────

METRIC_PATTERN = re.compile(
    r"\b(\d+[\.,]?\d*\s*(%|x|×|percent|users|requests|ms|seconds|hours|days|"
    r"k|m|b|million|billion|thousand|TB|GB|MB|engineers|customers|clients|"
    r"countries|languages|features|deployments|products|teams?))\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ATSScoreBreakdown:
    overall_score: int          # 0-100
    ats_score: int              # 0-100
    structure_score: int        # 0-100
    skills_score: int           # 0-100
    experience_score: int       # 0-100
    projects_score: int         # 0-100
    education_score: int        # 0-100
    formatting_score: int       # 0-100
    sections_present: list[str]
    sections_missing: list[str]
    action_verb_count: int
    metric_count: int
    word_count: int


def _normalise(text: str) -> str:
    return text.lower().strip()


def _count_words(text: str) -> int:
    return len(text.split())


def _section_present(text: str, aliases: list[str]) -> bool:
    lower = _normalise(text)
    return any(alias in lower for alias in aliases)


def _score_structure(parsed: ParsedResume) -> tuple[int, list[str], list[str]]:
    """Check required and optional section presence. Returns (score, present, missing)."""
    full = parsed.full_text + " " + parsed.skills + " " + parsed.experience + " " + parsed.education

    present: list[str] = []
    missing: list[str] = []

    for label, aliases in REQUIRED_SECTIONS:
        if _section_present(full, aliases):
            present.append(label)
        else:
            missing.append(label)

    for label, aliases in OPTIONAL_SECTIONS:
        if _section_present(full, aliases):
            present.append(label)

    required_count = len(REQUIRED_SECTIONS)
    found_required = sum(
        1 for label, _ in REQUIRED_SECTIONS if label in present
    )
    optional_bonus = min(len([l for l, _ in OPTIONAL_SECTIONS if l in present]) * 5, 20)

    base = int((found_required / required_count) * 80) + optional_bonus
    return min(base, 100), present, missing


def _score_skills(parsed: ParsedResume) -> int:
    skills_text = parsed.skills.strip()
    if not skills_text or skills_text == "(no Skills section detected)":
        return 10
    word_count = _count_words(skills_text)
    if word_count < 5:
        return 20
    if word_count < 15:
        return 50
    if word_count < 30:
        return 70
    if word_count < 60:
        return 85
    return 95


def _score_experience(parsed: ParsedResume) -> tuple[int, int, int]:
    """Returns (score, action_verb_count, metric_count)."""
    exp_text = parsed.experience.strip()
    if not exp_text or exp_text == "(no Experience section detected)":
        return 15, 0, 0

    words = exp_text.lower().split()
    action_count = sum(1 for w in words if w.rstrip(".,;:") in ACTION_VERBS)
    metric_matches = METRIC_PATTERN.findall(exp_text)
    metric_count = len(metric_matches)

    word_count = _count_words(exp_text)

    score = 30
    # Penalise very short experience sections
    if word_count < 20:
        score = 20
    elif word_count > 50:
        score += 10

    # Action verb bonus (up to +30)
    score += min(action_count * 6, 30)
    # Metric bonus (up to +25)
    score += min(metric_count * 5, 25)

    return min(score, 100), action_count, metric_count


def _score_projects(parsed: ParsedResume) -> int:
    proj_text = parsed.projects.strip()
    if not proj_text or proj_text == "(no Projects section detected)":
        return 30  # Missing projects is a weakness but not fatal
    word_count = _count_words(proj_text)
    if word_count < 10:
        return 40
    if word_count < 40:
        return 60
    if word_count < 100:
        return 80
    return 92


def _score_education(parsed: ParsedResume) -> int:
    edu_text = parsed.education.strip()
    if not edu_text or edu_text == "(no Education section detected)":
        return 20
    word_count = _count_words(edu_text)
    if word_count < 5:
        return 35
    return 90


def _score_formatting(parsed: ParsedResume) -> int:
    full = parsed.full_text
    word_count = _count_words(full)
    score = 70

    # Resume too short
    if word_count < 150:
        score -= 25
    elif word_count < 300:
        score -= 10

    # Resume too long (wall of text)
    if word_count > 1200:
        score -= 15

    # Check for email presence (ATS-important)
    if parsed.email:
        score += 5

    # Check for phone
    if parsed.phone:
        score += 5

    # Check for URLs / LinkedIn / GitHub
    if re.search(r"(linkedin|github|portfolio|http)", full, re.IGNORECASE):
        score += 10

    return max(10, min(score, 100))


def compute_ats_scores(parsed: ParsedResume) -> ATSScoreBreakdown:
    """Compute a fully deterministic ATS score breakdown for a parsed resume.

    Same input → same scores every time.  No randomness, no LLM.
    """
    structure_score, sections_present, sections_missing = _score_structure(parsed)
    skills_score = _score_skills(parsed)
    experience_score, action_verb_count, metric_count = _score_experience(parsed)
    projects_score = _score_projects(parsed)
    education_score = _score_education(parsed)
    formatting_score = _score_formatting(parsed)
    word_count = _count_words(parsed.full_text)

    # Weighted overall score
    overall_score = int(
        structure_score * 0.20
        + skills_score * 0.20
        + experience_score * 0.25
        + projects_score * 0.15
        + education_score * 0.10
        + formatting_score * 0.10
    )

    # ATS score weights towards parseable structure and keyword density
    ats_score = int(
        structure_score * 0.30
        + skills_score * 0.30
        + formatting_score * 0.20
        + education_score * 0.10
        + experience_score * 0.10
    )

    return ATSScoreBreakdown(
        overall_score=min(max(overall_score, 0), 100),
        ats_score=min(max(ats_score, 0), 100),
        structure_score=structure_score,
        skills_score=skills_score,
        experience_score=experience_score,
        projects_score=projects_score,
        education_score=education_score,
        formatting_score=formatting_score,
        sections_present=sections_present,
        sections_missing=sections_missing,
        action_verb_count=action_verb_count,
        metric_count=metric_count,
        word_count=word_count,
    )
