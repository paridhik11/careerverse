/**
 * Virtual Work Experience API client.
 *
 * simulateSingleCareer  — POST /job-matches/{resumeId}/simulate/{jobMatchId}
 *   Generate (or return cached) simulation for ONE career match.
 *   This is the preferred "Start Experience" flow — ~15-20 s instead of ~60 s.
 *
 * simulateAllCareers    — POST /job-matches/{resumeId}/simulate-all
 *   Legacy: generate all three simulations concurrently.
 *   Kept for backward compatibility.
 */

import { apiFetch } from "@/services/api"
import type { JobSimulationRecord, SimulateAllResponse } from "@/types"

/** Generate (or return cached) simulation for a single career match. */
export function simulateSingleCareer(
  resumeId: number,
  jobMatchId: number,
): Promise<JobSimulationRecord> {
  return apiFetch<JobSimulationRecord>(
    `/job-matches/${resumeId}/simulate/${jobMatchId}`,
    { method: "POST" },
  )
}

/** Legacy: generate all three simulations concurrently. */
export function simulateAllCareers(resumeId: number): Promise<SimulateAllResponse> {
  return apiFetch<SimulateAllResponse>(`/job-matches/${resumeId}/simulate-all`, {
    method: "POST",
  })
}
