/**
 * Resume API client — all resume-related API calls in one module.
 * Pages and hooks import from here; raw fetch/FormData details stay hidden.
 */

import { apiFetch } from "@/services/api"
import type { ResumeRecord, ResumeReviewReport, ResumeUploadResponse } from "@/types"

/**
 * Legacy upload — POST /resume/upload.
 * Stores the PDF on disk; does not persist a DB record or run AI.
 * Kept for backwards compatibility with the existing ResumeUpload page.
 */
export function uploadResume(file: File): Promise<ResumeUploadResponse> {
  const formData = new FormData()
  formData.append("file", file)

  return apiFetch<ResumeUploadResponse>("/resume/upload", {
    method: "POST",
    body: formData,
  })
}

/**
 * Upload, parse, and persist a resume — POST /resumes.
 * Returns a ResumeRecord with a stable `id` that downstream agents need.
 * The backend extracts text via PyMuPDF and stores the result in the DB.
 */
export function createResume(file: File): Promise<ResumeRecord> {
  const formData = new FormData()
  formData.append("file", file)

  return apiFetch<ResumeRecord>("/resumes", {
    method: "POST",
    body: formData,
  })
}

/**
 * Run the Resume Reviewer Agent — POST /resumes/{id}/review.
 * Loads the stored resume by id, calls GPT-4o, persists and returns the
 * structured ResumeReviewReport. May take up to ~30s for large resumes.
 */
export function reviewResume(resumeId: number): Promise<ResumeReviewReport> {
  return apiFetch<ResumeReviewReport>(`/resumes/${resumeId}/review`, {
    method: "POST",
  })
}
