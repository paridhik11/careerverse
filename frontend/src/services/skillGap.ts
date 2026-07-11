/**
 * Skill Gap API client.
 *
 * Calls POST /skill-gap/{resumeId} to generate and persist the personalised
 * Skill Gap Analysis for the user's chosen career.
 *
 * Prerequisites (enforced by the backend):
 *   - Resume exists (POST /resumes).
 *   - Career recommendations have been generated (POST /job-matches/{id}).
 *   - User has chosen one career (PATCH /job-matches/{id}/choose).
 */

import { apiFetch } from "@/services/api"

export type SkillGapContent = {
  id: number
  resume_id: number
  job_match_id: number
  readiness_score: number
  summary: string
  existing_skills: string[]
  missing_technical_skills: string[]
  missing_soft_skills: string[]
  recommended_next_steps: string[]
  created_at: string
}

export type SkillGapApiResponse = {
  skill_gap: SkillGapContent
}

/**
 * Generate a personalised Skill Gap Analysis for the chosen career.
 *
 * The backend loads the chosen JobMatch, JD text, and resume text, calls
 * GPT-4o, persists the result, and returns the skill gap analysis.
 *
 * May take up to ~45s — show a loading state.
 */
export function generateSkillGap(resumeId: number): Promise<SkillGapApiResponse> {
  return apiFetch<SkillGapApiResponse>(`/skill-gap/${resumeId}`, {
    method: "POST",
  })
}
