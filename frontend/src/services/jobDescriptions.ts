/**
 * Job description API client — mirrors `services/resume.ts`.
 * Pages and hooks import from here; raw fetch/FormData details stay hidden.
 */

import { apiFetch } from "@/services/api"
import type { JobDescriptionUploadResponse } from "@/types"

/**
 * Upload one or more job description PDF/TXT files — POST /job-descriptions/upload.
 * Text is extracted and each file is persisted + indexed into ChromaDB on the
 * backend so the Career Recommendation Agent can retrieve it via RAG.
 */
export function uploadJobDescriptions(files: File[]): Promise<JobDescriptionUploadResponse> {
  const formData = new FormData()
  for (const file of files) {
    formData.append("files", file)
  }

  return apiFetch<JobDescriptionUploadResponse>("/job-descriptions/upload", {
    method: "POST",
    body: formData,
  })
}
