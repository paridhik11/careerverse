/**
 * Learning Roadmap API client.
 *
 * Calls POST /learning-roadmap/{resumeId} to generate and persist the
 * personalised 3-Month Learning Roadmap for the user's chosen career.
 *
 * Prerequisites (enforced by the backend):
 *   - Resume exists (POST /resumes).
 *   - Career recommendations have been generated (POST /job-matches/{id}).
 *   - User has chosen one career (PATCH /job-matches/{id}/choose).
 *   - Skill Gap Analysis has been run (POST /skill-gap/{resumeId}).
 */

import { apiFetch } from "@/services/api"
import type { LearningRoadmapResponse } from "@/types"

/**
 * Generate a personalised 3-Month Learning Roadmap for the chosen career.
 *
 * The backend loads the chosen JobMatch, JD text, resume text, and Skill Gap
 * Analysis, calls GPT-4o, persists the result, and returns the roadmap.
 *
 * May take up to ~60s for complex resumes + JDs — show a loading state.
 */
export function generateLearningRoadmap(
  resumeId: number,
): Promise<LearningRoadmapResponse> {
  return apiFetch<LearningRoadmapResponse>(`/learning-roadmap/${resumeId}`, {
    method: "POST",
  })
}
