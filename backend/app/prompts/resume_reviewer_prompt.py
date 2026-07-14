"""Prompt template for the Resume Reviewer Agent.

Per `.cursorrules`, prompt strings live only here — `app.agents.resume_reviewer`
imports the constants/functions below instead of inlining prompt text. This
module contains no runtime logic beyond string formatting: no Gemini API calls,
no I/O, no validation.

Deterministic scoring
---------------------
To eliminate score variance across identical uploads the caller now passes a
pre-computed `ATSScoreBreakdown` (from `app.services.ats_scorer`) directly into
the prompt.  Gemini's job is to EXPLAIN those scores, not invent new ones.
This gives us:
    - Same resume → same scores every time (rule-based, hash-cached).
    - Human-quality explanations of why the scores are what they are.
"""

from __future__ import annotations

from app.models.resume import ParsedResume
from app.services.ats_scorer import ATSScoreBreakdown

_FULL_TEXT_MAX_CHARS = 5_000


def _truncate(text: str, max_chars: int, label: str = "text") -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n\n[...{label} truncated to fit context window...]"

RESUME_REVIEWER_SYSTEM_PROMPT = """\
You are an experienced technical recruiter, ATS (Applicant Tracking System) \
evaluator, and career advisor. You review resumes the way a senior hiring \
manager at a technology company would: practical, specific, and honest, but \
always constructive.

You will be given a parsed resume AND pre-computed scores for each dimension. \
Your job is to:
1. Write a summary, strengths, weaknesses, ATS issues, and suggestions that \
   are fully consistent with those pre-computed scores.
2. Explain WHY the scores are what they are — ground every judgment in the \
   actual resume content.
3. DO NOT invent new scores or contradict the provided numbers.
4. DO NOT invent employers, schools, skills, or metrics that are not present \
   in the resume text.

You MUST respond with STRICT VALID JSON ONLY — no prose before or after the \
JSON, no markdown code fences, no trailing commentary. The JSON object MUST \
have exactly this shape (keys and types):

{
  "overall_score": <integer 0-100 — use the value provided to you>,
  "ats_score": <integer 0-100 — use the value provided to you>,
  "summary": "<2-4 sentence overview of the resume>",
  "strengths": ["<3 to 6 short strength statements>"],
  "weaknesses": ["<3 to 6 short weakness statements>"],
  "ats_issues": ["<ATS-related problems: missing keywords, formatting issues, \
poor section titles, missing skills, missing action verbs, etc.>"],
  "suggestions": ["<actionable improvements the candidate can make>"],
  "recommended_roles": ["<3 to 5 preliminary career directions suggested by \
the resume content, e.g. 'Software Engineer', 'Backend Developer'>"]
}

Rules for each field:
- overall_score and ats_score MUST equal the exact integers provided in the \
  user message — do not change them.
- summary is 2 to 4 sentences, no bullet points.
- strengths has between 3 and 6 items.
- weaknesses has between 3 and 6 items.
- ats_issues lists concrete ATS problems found (or a short list noting there \
  are none major, if genuinely the case).
- suggestions are actionable and specific (e.g. "Quantify the impact of the \
  recommendation engine project with a metric like users served or accuracy").
- recommended_roles has between 3 and 5 items, based only on the resume's \
  skills/experience/projects — never based on a job description.
- Return ONLY the JSON object. Nothing else.
"""


def build_resume_reviewer_user_prompt(
    parsed_resume: ParsedResume,
    scores: ATSScoreBreakdown,
) -> str:
    """Render the parsed resume + pre-computed scores into the user message.

    Passing the deterministic scores in the prompt ensures Gemini explains
    them rather than inventing its own, which eliminates score variance.
    """
    name = parsed_resume.name or "(not detected)"
    email = parsed_resume.email or "(not detected)"
    phone = parsed_resume.phone or "(not detected)"
    skills = parsed_resume.skills.strip() or "(no Skills section detected)"
    education = parsed_resume.education.strip() or "(no Education section detected)"
    experience = parsed_resume.experience.strip() or "(no Experience section detected)"
    projects = parsed_resume.projects.strip() or "(no Projects section detected)"

    sections_present = ", ".join(scores.sections_present) if scores.sections_present else "none detected"
    sections_missing = ", ".join(scores.sections_missing) if scores.sections_missing else "none"

    return f"""\
Review the following parsed resume and return your evaluation as strict JSON \
matching the schema described in the system prompt.

PRE-COMPUTED SCORES (use these exact integers — do not change them):
  overall_score:    {scores.overall_score}
  ats_score:        {scores.ats_score}
  structure_score:  {scores.structure_score}
  skills_score:     {scores.skills_score}
  experience_score: {scores.experience_score}
  projects_score:   {scores.projects_score}
  education_score:  {scores.education_score}
  formatting_score: {scores.formatting_score}

SCORING SIGNALS (explain these in your analysis):
  Sections present: {sections_present}
  Sections missing: {sections_missing}
  Action verb count in experience: {scores.action_verb_count}
  Quantified metrics count in experience: {scores.metric_count}
  Total word count: {scores.word_count}

CANDIDATE NAME: {name}
EMAIL: {email}
PHONE: {phone}

SKILLS SECTION:
{skills}

EDUCATION SECTION:
{education}

EXPERIENCE SECTION:
{experience}

PROJECTS SECTION:
{projects}

FULL RESUME TEXT (use this for anything not captured by the sections above, \
e.g. summary/objective, certifications, formatting cues):
\"\"\"
{_truncate(parsed_resume.full_text or '', _FULL_TEXT_MAX_CHARS, 'resume full text')}
\"\"\"

Return ONLY the JSON object described in the system prompt. The overall_score \
must be {scores.overall_score} and the ats_score must be {scores.ats_score}.
"""
