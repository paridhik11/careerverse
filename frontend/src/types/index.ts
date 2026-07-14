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

/* ─── Job Description upload (POST /job-descriptions/upload) ────────────── */

export type JobDescriptionUploadItem = {
  id: string
  filename: string
  role_title: string
  status: string
}

export type JobDescriptionUploadResponse = {
  uploaded: JobDescriptionUploadItem[]
}

/**
 * Shape passed via React Router location.state from ResumeReportPage to
 * JobDescriptionUploadPage — resume id plus optional review report so the
 * Resume Match Report page can reuse strengths / ATS without re-calling AI.
 */
export type JobDescriptionUploadState = {
  resumeId: number
  report?: ResumeReviewReport
  fileName?: string
}

/* ─── Career Recommendation Agent (POST /job-matches/{resume_id}) ───────── */

export type ConfidenceScore = "High" | "Medium" | "Low"

/** One persisted Career Recommendation Agent output, linked to a JobDescription. */
export type JobMatch = {
  id: number
  resume_id: number
  job_description_id: number
  role_title: string
  match_percent: number
  confidence_score: ConfidenceScore
  reasoning: string
  career_overview: string
  missing_skills: string[]
  rank: 1 | 2 | 3
  is_chosen: boolean
  created_at: string
}

/** Returned by POST /job-matches/{resume_id} — always exactly three matches. */
export type JobMatchListResponse = {
  matches: JobMatch[]
}

/* ─── Career Selection (PATCH /job-matches/{id}/choose, GET /job-matches/{resume_id}/chosen) ── */

/** Returned by PATCH /job-matches/{job_match_id}/choose. */
export type CareerChoiceResponse = {
  job_match_id: number
  role_title: string
  message: string
}

/**
 * Returned by GET /job-matches/{resume_id}/chosen.
 * Contains only the fields downstream features (Skill Gap, Roadmap, Mentor) need.
 */
export type ChosenJobMatch = {
  id: number
  role_title: string
  match_percent: number
  confidence_score: ConfidenceScore
  career_overview: string
  missing_skills: string[]
  is_chosen: true
}

/* ─── Virtual Work Experience (POST /job-matches/{resume_id}/simulate-all) ── */

export type TaskResource = {
  type: string
  content: string
}

export type TaskActivityType =
  | "multiple_choice"
  | "short_answer"
  | "prioritize"
  | "bug_analysis"
  | "email"
  | "report"

export type TaskActivity = {
  type: TaskActivityType
  question: string
  options: string[]
}

export type TaskFeedback = {
  positive: string
  improvement: string
  real_world_importance: string
}

export type TaskEvaluation = {
  communication: number
  problem_solving: number
  technical_judgment: number
  collaboration: number
  leadership: number
  adaptability: number
}

export type SimulationTask = {
  task_number: number
  title: string
  estimated_time: string
  difficulty: string
  objective: string
  context: string
  resources: TaskResource[]
  activity: TaskActivity
  expected_solution: string
  feedback: TaskFeedback
  evaluation: TaskEvaluation
  jd_reference: string
}

export type SimulationOverview = {
  company_context: string
  team_context: string
  your_role: string
  project_background: string
}

export type SimulationContent = {
  job_title: string
  estimated_duration: string
  difficulty: string
  overview: SimulationOverview
  what_youll_learn: string[]
  what_youll_do: string[]
  tasks: SimulationTask[]
}

export type JobSimulationRecord = {
  id: number
  job_match_id: number
  simulation: SimulationContent
  created_at: string
}

/** Returned by POST /job-matches/{resume_id}/simulate-all */
export type SimulateAllResponse = {
  simulations: JobSimulationRecord[]
}

/* ─── Page-to-page navigation state shapes ──────────────────────────────── */

/** Passed from JobDescriptionUploadPage → ResumeMatchPage via location.state */
export type ResumeMatchPageState = {
  matches: JobMatch[]
  resumeId: number
  selectedJdTitle: string
  primaryMatch: JobMatch
  report?: ResumeReviewReport
  fileName?: string
}

/** Passed from ResumeMatchPage / JobDescriptionUploadPage → CareerMatchesPage via location.state */
export type CareerMatchesState = {
  matches: JobMatch[]
  resumeId: number
  selectedJdTitle?: string
  primaryMatch?: JobMatch
}

/** Passed from CareerMatchesPage → VirtualExperiencePage via location.state */
export type VirtualExperienceState = {
  simulation: JobSimulationRecord
  match: JobMatch
  resumeId: number
  allSimulations: JobSimulationRecord[]
  /** When true, choosing a career returns to the Dashboard roadmap section. */
  returnToDashboard?: boolean
}

/* ─── Learning Roadmap (POST /learning-roadmap/{resume_id}) ─────────────── */

/** One month of the 3-Month Learning Roadmap. */
export type MonthPlan = {
  focus: string
  topics: string[]
  projects: string[]
  resources: string[]
  milestones: string[]
}

/** Full 3-month roadmap returned by the Learning Roadmap Agent. */
export type RoadmapContent = {
  month_1: MonthPlan
  month_2: MonthPlan
  month_3: MonthPlan
}

/** Persisted Learning Roadmap record returned by the API. */
export type LearningRoadmapRecord = {
  id: number
  resume_id: number
  job_match_id: number
  roadmap: RoadmapContent
  created_at: string
}

/** Returned by POST /learning-roadmap/{resume_id}. */
export type LearningRoadmapResponse = {
  roadmap: LearningRoadmapRecord
}

/** Passed from SkillGapPage → LearningRoadmapPage via location.state. */
export type LearningRoadmapState = {
  roadmap: LearningRoadmapRecord
  match: JobMatch
  resumeId: number
}

/* ─── Career Mentor Chatbot ─────────────────────────────────────────────── */

export type MentorMessageRole = "user" | "assistant"

/** One persisted message in the Career Mentor conversation. */
export type MentorMessageRecord = {
  id: number
  resume_id: number
  role: MentorMessageRole
  content: string
  created_at: string
}

/** Returned by GET /career-mentor/history/{resume_id}. */
export type MentorHistoryResponse = {
  messages: MentorMessageRecord[]
}

/** Request body for POST /career-mentor/chat. */
export type MentorChatRequest = {
  resume_id: number
  message: string
}
