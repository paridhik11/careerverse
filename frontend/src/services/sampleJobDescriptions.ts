/**
 * Sample JD fixtures — frontend client for seeded backend job descriptions.
 */

import { apiFetch } from "@/services/api"
import type { JobDescriptionUploadResponse } from "@/types"

export type SampleJobDescription = {
  id: string
  role_title: string
  category: string
  summary: string
}

export type SampleJobDescriptionListResponse = {
  samples: SampleJobDescription[]
}

export function getSampleJobDescriptions(): Promise<SampleJobDescription[]> {
  return apiFetch<SampleJobDescriptionListResponse>("/job-descriptions/samples").then(
    (res) => res.samples,
  )
}

export function seedSampleJobDescriptions(
  sampleIds: string[],
): Promise<JobDescriptionUploadResponse> {
  return apiFetch<JobDescriptionUploadResponse>("/job-descriptions/samples/seed", {
    method: "POST",
    body: { sample_ids: sampleIds },
  })
}
