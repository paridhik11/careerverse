/**
 * Virtual Work Experience API client.
 * POST /job-matches/{resume_id}/simulate-all — generates all three concurrent
 * AI workplace simulations (one per Top 3 career match) and returns them.
 * May take up to ~60 seconds due to concurrent GPT-4o calls.
 */

import { apiFetch } from "@/services/api"
import type { SimulateAllResponse } from "@/types"

export function simulateAllCareers(resumeId: number): Promise<SimulateAllResponse> {
  return apiFetch<SimulateAllResponse>(`/job-matches/${resumeId}/simulate-all`, {
    method: "POST",
  })
}
