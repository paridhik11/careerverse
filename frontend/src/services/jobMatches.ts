/**
 * Career Recommendation Agent API client — mirrors `services/resume.ts`.
 */

import { apiFetch } from "@/services/api"
import type { CareerChoiceResponse, ChosenJobMatch, JobMatchListResponse } from "@/types"

/**
 * Run the Career Recommendation Agent — POST /job-matches/{resume_id}.
 * Retrieves the Top-K job descriptions via RAG, compares them against the
 * resume, and persists + returns exactly three ranked `JobMatch` records.
 * May take up to ~30s (single GPT-4o call).
 */
export function generateJobMatches(resumeId: number): Promise<JobMatchListResponse> {
  return apiFetch<JobMatchListResponse>(`/job-matches/${resumeId}`, {
    method: "POST",
  })
}

/**
 * Choose a career — PATCH /job-matches/{jobMatchId}/choose.
 * Sets is_chosen=true for this match and is_chosen=false for every other
 * match that belongs to the same resume. Safe to call more than once —
 * switching careers simply deselects the previous choice automatically.
 */
export function chooseJobMatch(jobMatchId: number): Promise<CareerChoiceResponse> {
  return apiFetch<CareerChoiceResponse>(`/job-matches/${jobMatchId}/choose`, {
    method: "PATCH",
  })
}

/**
 * Retrieve the already-chosen career — GET /job-matches/{resumeId}/chosen.
 * Returns the selected JobMatch or throws a 404 ApiError if no career has
 * been chosen yet. Downstream pages (Skill Gap, Roadmap, Mentor) should call
 * this to obtain the source-of-truth career for a resume.
 */
export function getChosenJobMatch(resumeId: number): Promise<ChosenJobMatch> {
  return apiFetch<ChosenJobMatch>(`/job-matches/${resumeId}/chosen`, {
    method: "GET",
  })
}
