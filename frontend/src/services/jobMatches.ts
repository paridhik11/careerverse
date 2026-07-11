/**
 * Career Recommendation Agent API client — mirrors `services/resume.ts`.
 */

import { apiFetch } from "@/services/api"
import type { JobMatchListResponse } from "@/types"

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
