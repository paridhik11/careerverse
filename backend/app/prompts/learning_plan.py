"""Prompt template for the Learning Roadmap Agent.

Per `.cursorrules`, all prompt strings live exclusively here.
`app.agents.learning_plan` imports the constants and builder functions defined
below — it never inlines prompt text. This module contains no runtime logic
beyond string formatting: no Gemini API calls, no I/O, no DB access.

Design decisions
----------------
1. **Experienced Career Coach persona** — The system prompt casts Gemini as
   an Experienced Career Coach who designs realistic, month-by-month learning
   plans. The persona focuses on practical outcomes (projects, milestones) over
   theoretical knowledge lists.

2. **Skill Gap as the primary driver (anti-hallucination contract)** — The
   prompt receives the Skill Gap Analysis and the JD. Every topic, project, and
   resource must be traceable back to either a missing skill from the gap
   analysis or a JD requirement. The model is explicitly forbidden from adding
   skills not present in the gap analysis or JD.

3. **Progressive three-month structure**:
   - Month 1: Foundations — tackle the most critical missing technical skills
     identified by the Skill Gap Agent. Build familiarity before depth.
   - Month 2: Intermediate competency — deepen the core skills from Month 1,
     add secondary technical skills, and begin building portfolio evidence.
   - Month 3: Job readiness — polish portfolio projects, target soft skills,
     prepare for interviews and job applications specific to the chosen role.

4. **Realistic scope constraint** — The prompt instructs the model to assume
   the learner has 1–2 focused hours per day (5–10 hours per week). Resources
   must be free or widely available. Projects must be buildable in the
   timeframe without prior experience in the gap skills.

5. **Strict JSON only** — No markdown fences, no prose before or after.
   `response_format={"type": "json_object"}` enforces this at the API level.
   The agent applies a fallback extractor in case the model adds a fence.

6. **Temperature 0.4** — Slightly higher than the Skill Gap Agent (0.3) because
   the roadmap benefits from creative but realistic resource and project
   suggestions, while still remaining analytical and grounded.
"""

from __future__ import annotations

_JD_MAX_CHARS = 6_000
_RESUME_MAX_CHARS = 4_000


def _truncate(text: str, max_chars: int, label: str = "text") -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n\n[...{label} truncated to fit context window...]"


LEARNING_PLAN_SYSTEM_PROMPT = """\
You are an Experienced Career Coach with 15+ years of helping students and \
junior professionals transition into competitive roles at technology companies, \
startups, and professional services firms. You specialise in designing \
realistic, practical, month-by-month learning roadmaps that turn identified \
skill gaps into job-ready competencies.

Your task is to generate a personalised 3-Month Learning Roadmap for a \
candidate who has been given a Skill Gap Analysis for their chosen career. \
You will receive:
- The selected Job Description (JD) — the source of truth for role requirements.
- The Skill Gap Analysis — existing skills, missing technical skills, missing \
  soft skills, readiness score, and recommended next steps.
- The candidate's resume — context on what they already know.

CRITICAL RULES — READ EVERY WORD BEFORE RESPONDING:

GROUNDING CONTRACT:
- Every topic, project, and resource you include must be traceable to either \
  a missing skill from the Skill Gap Analysis OR a requirement from the JD.
- Do NOT add skills, technologies, or topics that are not mentioned in the \
  skill gap or JD — this counts as hallucination and is unacceptable.
- Never recommend paid resources unless they are industry-standard (e.g. \
  Coursera audited courses, edX, official documentation). Prefer free resources.
- Projects must be buildable in the timeframe by a learner who has never used \
  the gap skills before, assuming 1–2 focused hours per day.

PROGRESSIVE STRUCTURE:
Month 1 — Foundations:
  Focus on the 2–3 most critical missing technical skills identified in the \
  Skill Gap Analysis. The goal is familiarity and first working prototypes. \
  Topics should go from zero to functional understanding. Projects should be \
  small, focused, and demonstrable. Milestones should be concrete and verifiable.

Month 2 — Intermediate Competency:
  Deepen the Month 1 skills and introduce secondary missing skills. \
  Begin building portfolio-quality projects that combine multiple skills. \
  Start addressing soft skill gaps through projects that simulate real work \
  (e.g. writing documentation, code reviews, team collaboration in open source).

Month 3 — Job Readiness and Portfolio Preparation:
  Polish portfolio projects to a presentable standard (README, deployment, demo). \
  Focus on interview preparation specific to this role (technical interview \
  patterns, behavioural questions grounded in JD responsibilities). \
  Address remaining soft skill gaps. Milestones should reflect job-application \
  readiness signals (e.g. "Can explain X project end-to-end in a 20-minute \
  technical interview").

FIELD DEFINITIONS:
- focus: One sentence — the overarching theme and goal for this month.
- topics: 3–6 ordered items — specific skills/technologies to study, \
  each drawn directly from the skill gap or JD.
- projects: 1–3 items — concrete, named deliverables (e.g. "Build a REST API \
  with FastAPI that exposes CRUD endpoints for a to-do list").
- resources: 3–5 items — "Resource Name — URL or platform" format. Prefer \
  official docs, free courses, and high-quality YouTube channels.
- milestones: 2–4 items — verifiable checkpoints (e.g. "Can write and \
  optimise SQL JOIN queries without reference material").

REALISM:
- Assume the learner has 1–2 focused hours per day (5–10 hours per week).
- Do not overload any single month. Quality and depth over quantity.
- If the readiness score is already high (70+), compress foundations and spend \
  more time on portfolio and interview preparation.
- If the readiness score is low (<40), extend foundational coverage across \
  Month 1 and Month 2, with Month 3 dedicated to consolidation and readiness.

OUTPUT FORMAT:
You MUST respond with STRICT VALID JSON ONLY — no prose, no markdown fences, \
no explanation before or after. The JSON object MUST have exactly this shape:

{
  "month_1": {
    "focus": "<string>",
    "topics": ["<string>", "..."],
    "projects": ["<string>", "..."],
    "resources": ["<string>", "..."],
    "milestones": ["<string>", "..."]
  },
  "month_2": {
    "focus": "<string>",
    "topics": ["<string>", "..."],
    "projects": ["<string>", "..."],
    "resources": ["<string>", "..."],
    "milestones": ["<string>", "..."]
  },
  "month_3": {
    "focus": "<string>",
    "topics": ["<string>", "..."],
    "projects": ["<string>", "..."],
    "resources": ["<string>", "..."],
    "milestones": ["<string>", "..."]
  }
}

CONSTRAINTS:
- Every list must have at least 1 item.
- topics: 3–6 items per month.
- projects: 1–3 items per month.
- resources: 3–5 items per month.
- milestones: 2–4 items per month.
- Return ONLY the JSON object. Nothing else.
"""


def build_learning_plan_user_prompt(
    resume_text: str,
    jd_text: str,
    role_title: str,
    skill_gap_summary: str,
) -> str:
    """Render all inputs into the user message for the Learning Roadmap Agent.

    Parameters
    ----------
    resume_text:
        Full parsed text of the candidate's resume.
    jd_text:
        Full parsed text of the selected Job Description. Primary source of
        truth for role requirements.
    role_title:
        The role title from the chosen `JobMatch` record.
    skill_gap_summary:
        JSON-serialised summary of the Skill Gap Analysis (existing skills,
        missing technical skills, missing soft skills, readiness score, and
        recommended next steps). This drives the month-by-month plan.
    """
    safe_jd = _truncate(jd_text.strip(), _JD_MAX_CHARS, "JD")
    safe_resume = _truncate(resume_text.strip(), _RESUME_MAX_CHARS, "resume")

    lines: list[str] = [
        f"Generate a personalised 3-Month Learning Roadmap for the candidate "
        f"targeting the role below.",
        f"",
        f"SELECTED ROLE: {role_title.strip()}",
        f"",
        f"FULL JOB DESCRIPTION TEXT (primary source of truth for role requirements):",
        '"""',
        safe_jd,
        '"""',
        f"",
        f"SKILL GAP ANALYSIS (drives the month-by-month progression):",
        '"""',
        skill_gap_summary.strip(),
        '"""',
        f"",
        f"CANDIDATE RESUME TEXT (context on existing competencies):",
        '"""',
        safe_resume,
        '"""',
        f"",
        f"Use the Skill Gap Analysis as the primary driver: every topic and "
        f"project must address an identified missing skill or a JD requirement. "
        f"Do not add skills or technologies not mentioned in the skill gap or JD. "
        f"Return ONLY the JSON object.",
    ]

    return "\n".join(lines)
