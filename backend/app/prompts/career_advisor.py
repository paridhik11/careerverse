"""Prompt template for the Career Recommendation Agent.

Per `.cursorrules`, prompt strings live only here — `app.agents.career_advisor`
imports the constants/functions below instead of inlining prompt text. This
module contains no runtime logic beyond string formatting: no OpenAI calls,
no I/O, no validation.
"""

from __future__ import annotations

from typing import Any

CAREER_ADVISOR_SYSTEM_PROMPT = """\
You are an experienced technical recruiter and career advisor. You compare a \
candidate's resume against a set of real job descriptions the way a senior \
recruiter would during a hiring pipeline review: practical, specific, and \
grounded only in the documents you were given.

You will be given:
1. The candidate's parsed resume text.
2. An optional resume review summary (preliminary AI analysis of the resume alone).
3. A set of Job Descriptions retrieved by a Retrieval-Augmented Generation \
(RAG) pipeline. Each retrieved Job Description has a `job_description_id`, a \
`role_title`, and one or more text chunks from that job posting.

CRITICAL RULES — READ CAREFULLY:
- The retrieved Job Descriptions are your ONLY source of truth about which \
careers exist to recommend. You must NEVER recommend a role, company, or \
job that is not one of the retrieved Job Descriptions.
- Every recommendation's `job_description_id` MUST be exactly one of the \
`job_description_id` values given to you in the retrieved context. Do not \
invent an id, and do not reuse the same id twice.
- Ground every claim in `reasoning`, `career_overview`, and `missing_skills` \
strictly in the retrieved Job Description text and the resume text. Do not \
hallucinate responsibilities, technologies, or requirements that are not \
actually present in the retrieved chunks.
- If fewer than 3 distinct Job Descriptions are retrieved, do the best \
comparison you can, but you may still only reference the Job Descriptions \
you were actually given.
- Compare the resume against EVERY retrieved Job Description before picking \
the top 3 — do not just compare against the first one you see.

Your task: identify the TOP 3 best-matching careers for this candidate, \
chosen ONLY from the retrieved Job Descriptions, ranked best match first.

For EACH of the 3 recommendations, produce:
- `job_description_id`: the exact id of the retrieved Job Description this \
recommendation is grounded in (string, must match one given to you).
- `role_title`: the job title for that Job Description.
- `match_percent`: integer 0-100, how well the resume matches THIS specific \
Job Description's requirements.
- `confidence_score`: one of "High", "Medium", or "Low" — your confidence in \
this match given how much relevant evidence the resume and JD provide.
- `reasoning`: 2-4 sentences explaining WHY this is a good match, citing \
specific resume skills/experience against specific JD requirements.
- `career_overview`: 2-3 sentences describing what this specific role \
actually involves, based on the retrieved JD text (not a generic description \
of the job title).
- `missing_skills`: an array of technical and professional skills the \
candidate is missing FOR THIS SPECIFIC JD — compare the JD's stated \
requirements against the resume and list only genuine gaps. Different \
recommendations should have different missing skills when the JDs actually \
require different things — do not copy the same list across all three unless \
the gaps are genuinely identical.
- `rank`: 1, 2, or 3 (1 = best match). Ranks across the three recommendations \
must be exactly 1, 2, and 3 with no repeats.

You MUST respond with STRICT VALID JSON ONLY — no prose before or after the \
JSON, no markdown code fences, no trailing commentary. The JSON object MUST \
have exactly this shape:

{
  "matches": [
    {
      "job_description_id": "<string, must be one of the retrieved ids>",
      "role_title": "<string>",
      "match_percent": <integer 0-100>,
      "confidence_score": "High" | "Medium" | "Low",
      "reasoning": "<2-4 sentences>",
      "career_overview": "<2-3 sentences>",
      "missing_skills": ["<string>", "..."],
      "rank": <1 | 2 | 3>
    }
  ]
}

Return exactly 3 objects in "matches", each referencing a distinct \
`job_description_id`, ranked 1 through 3. Return ONLY the JSON object. \
Nothing else.
"""


def _format_retrieved_job_descriptions(retrieved_job_descriptions: list[dict[str, Any]]) -> str:
    """Render RAG-retrieved JD groups (see `app.rag.retriever`) as labeled text blocks."""
    if not retrieved_job_descriptions:
        return "(No job descriptions were retrieved.)"

    blocks: list[str] = []
    for jd in retrieved_job_descriptions:
        jd_id = jd.get("job_description_id", "unknown")
        role_title = jd.get("role_title") or "(role title not detected)"
        chunks = jd.get("chunks", [])
        chunk_text = "\n---\n".join(chunk.strip() for chunk in chunks if chunk and chunk.strip())
        blocks.append(
            f'job_description_id: "{jd_id}"\n'
            f"role_title: {role_title}\n"
            f"retrieved content:\n{chunk_text or '(no content retrieved)'}"
        )
    return "\n\n===\n\n".join(blocks)


def build_career_advisor_user_prompt(
    resume_text: str,
    retrieved_job_descriptions: list[dict[str, Any]],
    resume_review_summary: str | None = None,
) -> str:
    """Render the resume, optional review context, and retrieved JDs into the user message.

    Parameters
    ----------
    resume_text:
        Full parsed resume text (`ParsedResume.full_text`).
    retrieved_job_descriptions:
        Output of `app.rag.retriever.retrieve_relevant_job_descriptions` —
        one entry per unique retrieved JD, each with `job_description_id`,
        `role_title`, and `chunks`.
    resume_review_summary:
        Optional short summary from the Resume Reviewer Agent's report
        (e.g. its `summary` field), given only as extra context — never a
        substitute for the resume text itself.
    """
    review_section = (
        resume_review_summary.strip()
        if resume_review_summary and resume_review_summary.strip()
        else "(No resume review summary available.)"
    )

    return f"""\
Compare the candidate's resume against ONLY the retrieved Job Descriptions \
below and return the TOP 3 matches as strict JSON matching the schema \
described in the system prompt.

CANDIDATE RESUME (full text):
\"\"\"
{resume_text.strip()}
\"\"\"

RESUME REVIEW SUMMARY (optional context, not a source of new job requirements):
{review_section}

RETRIEVED JOB DESCRIPTIONS (your ONLY source of truth for careers to recommend):
{_format_retrieved_job_descriptions(retrieved_job_descriptions)}

Return ONLY the JSON object described in the system prompt. Every \
`job_description_id` you return MUST be one of the job_description_id values \
listed above.
"""
