/**
 * Shared TypeScript types for the CareerVerse frontend.
 * Domain types will be added as features are implemented.
 */

export type ApiHealthResponse = {
  status: string
}

/* ─── Auth ───────────────────────────────────────────────────────────────── */

export type AuthUser = {
  id: number
  email: string
}

export type AuthResponse = {
  access_token: string
  token_type: string
  user: AuthUser
}

/* ─── Resume upload (legacy /resume/upload endpoint) ────────────────────── */

export type ResumeUploadResponse = {
  file_name: string
  file_path: string
  status: string
}

/* ─── Resume (POST /resumes — upload + parse + persist) ─────────────────── */

export type ParsedResume = {
  full_text: string
  name: string | null
  email: string | null
  phone: string | null
  skills: string
  education: string
  experience: string
  projects: string
}

/** Returned by POST /resumes — a resume stored with a stable DB id. */
export type ResumeRecord = {
  id: number
  file_name: string
  parsed_resume: ParsedResume
  status: string
}

/* ─── Resume Review Report (POST /resumes/{id}/review) ──────────────────── */

/** Structured output of the Resume Reviewer Agent. */
export type ResumeReviewReport = {
  overall_score: number
  ats_score: number
  summary: string
  strengths: string[]
  weaknesses: string[]
  ats_issues: string[]
  suggestions: string[]
  recommended_roles: string[]
}

/**
 * Shape passed via React Router location.state from UploadResumePage
 * to ResumeReportPage so the report never needs to be re-fetched.
 */
export type ResumeReportState = {
  report: ResumeReviewReport
  resumeId: number
  fileName: string
  reviewedAt: string
}
