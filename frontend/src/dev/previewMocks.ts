/**
 * DEV ONLY — mock location.state payloads for /preview routes.
 * Delete this file (and the rest of src/dev/) before production.
 */

import type { SkillGapContent } from "@/services/skillGap"
import type {
  CareerMatchesState,
  JobDescriptionUploadState,
  JobMatch,
  JobSimulationRecord,
  LearningRoadmapState,
  ResumeReportState,
  VirtualExperienceState,
} from "@/types"

export const PREVIEW_RESUME_ID = 9001

const previewMatch: JobMatch = {
  id: 101,
  resume_id: PREVIEW_RESUME_ID,
  job_description_id: 201,
  role_title: "Frontend Engineer",
  match_percent: 82,
  confidence_score: "High",
  reasoning:
    "Strong React and TypeScript experience aligns with the JD’s core stack. Gaps are mostly in testing maturity and system design depth.",
  career_overview:
    "Build user-facing product features, collaborate with design, and ship polished web experiences in a product-led team.",
  missing_skills: ["Playwright", "GraphQL", "System Design"],
  rank: 1,
  is_chosen: false,
  created_at: "2026-07-01T10:00:00Z",
}

const previewMatches: JobMatch[] = [
  previewMatch,
  {
    ...previewMatch,
    id: 102,
    job_description_id: 202,
    role_title: "Full-Stack Developer",
    match_percent: 74,
    confidence_score: "Medium",
    reasoning:
      "Solid frontend foundation with some backend exposure. Would benefit from deeper API and database experience.",
    career_overview:
      "Own features end-to-end across React clients and Node/Python services, with ownership of deployment basics.",
    missing_skills: ["PostgreSQL", "Docker", "REST API Design"],
    rank: 2,
  },
  {
    ...previewMatch,
    id: 103,
    job_description_id: 203,
    role_title: "Product Designer (UI)",
    match_percent: 61,
    confidence_score: "Low",
    reasoning:
      "Design sensibility shows in portfolio projects, but formal UX research and Figma systems experience is limited.",
    career_overview:
      "Shape product flows, craft interface systems, and partner with engineers to ship accessible UI.",
    missing_skills: ["Figma Auto Layout", "User Research", "Design Systems"],
    rank: 3,
  },
]

const previewSimulation: JobSimulationRecord = {
  id: 301,
  job_match_id: previewMatch.id,
  created_at: "2026-07-01T11:00:00Z",
  simulation: {
    job_title: "Frontend Engineer",
    estimated_duration: "45–60 min",
    difficulty: "Intermediate",
    overview: {
      company_context:
        "You’re joining Northline, a Series B SaaS company building collaboration tools for remote teams.",
      team_context:
        "The web platform squad is 6 engineers + 1 designer. You’ll pair with Maya (senior FE) on the dashboard rewrite.",
      your_role:
        "As a Frontend Engineer intern-for-a-day, you’ll ship a small feature, review feedback, and communicate tradeoffs.",
      project_background:
        "The team is migrating the analytics dashboard from legacy jQuery widgets to a React + TypeScript design system.",
    },
    what_youll_learn: [
      "How product engineers triage UI bugs under time pressure",
      "How to write a crisp PR description for a frontend change",
      "How accessibility checks fit into a normal ship checklist",
    ],
    what_youll_do: [
      "Triage a reported dashboard bug",
      "Propose a fix and defend the approach",
      "Draft stakeholder-ready status updates",
    ],
    tasks: [
      {
        task_number: 1,
        title: "Triage the chart flicker",
        estimated_time: "10 min",
        difficulty: "Easy",
        objective: "Identify the most likely root cause of a flickering chart.",
        context:
          "A PM reports that the weekly active users chart flickers when switching date ranges. Design suspects a remount; backend says the payload is stable.",
        resources: [
          {
            type: "snippet",
            content: "useEffect(() => { fetchRange(range); }, [range])",
          },
          {
            type: "note",
            content: "React Strict Mode is enabled in development only.",
          },
        ],
        activity: {
          type: "multiple_choice",
          question: "What should you investigate first?",
          options: [
            "Force a full page reload on every range change",
            "Check whether the chart unmounts/remounts when range state updates",
            "Ask backend to cache every date range forever",
            "Disable Strict Mode in production",
          ],
        },
        expected_solution:
          "Inspect whether range updates remount the chart and whether loading placeholders replace the canvas mid-transition.",
        feedback: {
          positive: "You focused on the component lifecycle — the right first move.",
          improvement: "Also check whether the loading skeleton replaces the chart node entirely.",
          real_world_importance:
            "Most UI flicker bugs are remount or key-identity issues, not mysterious CSS.",
        },
        evaluation: {
          communication: 4,
          problem_solving: 5,
          technical_judgment: 5,
          collaboration: 3,
          leadership: 2,
          adaptability: 4,
        },
        jd_reference: "Debug and resolve UI defects in production React apps",
      },
      {
        task_number: 2,
        title: "Write the PR summary",
        estimated_time: "8 min",
        difficulty: "Easy",
        objective: "Draft a clear PR description for your chart fix.",
        context:
          "Maya asks you to open a PR. Reviewers care about risk, test plan, and user-visible impact.",
        resources: [
          {
            type: "diff",
            content: "- key={Math.random()}\n+ key={range}",
          },
        ],
        activity: {
          type: "short_answer",
          question: "Write a 3–5 sentence PR summary covering change, risk, and test plan.",
          options: [],
        },
        expected_solution:
          "Explain the remount cause, the stable key fix, low visual risk, and how you verified range switches.",
        feedback: {
          positive: "Clear structure helps reviewers move fast.",
          improvement: "Call out accessibility and empty-state checks when relevant.",
          real_world_importance:
            "PR writing is part of the job — it reduces review latency and production risk.",
        },
        evaluation: {
          communication: 5,
          problem_solving: 3,
          technical_judgment: 4,
          collaboration: 5,
          leadership: 3,
          adaptability: 3,
        },
        jd_reference: "Collaborate via code review and clear written communication",
      },
    ],
  },
}

export const mockResumeReportState: ResumeReportState = {
  resumeId: PREVIEW_RESUME_ID,
  fileName: "preview-resume.pdf",
  reviewedAt: "2026-07-01T09:30:00Z",
  report: {
    overall_score: 78,
    ats_score: 84,
    summary:
      "A solid early-career frontend resume with clear project impact. Strengthen quantification, ATS keyword coverage, and testing experience to push into the 85+ band.",
    strengths: [
      "Projects show end-to-end ownership",
      "TypeScript and React called out clearly",
      "Education and skills sections are easy to scan",
    ],
    weaknesses: [
      "Impact metrics are sparse on older roles",
      "No dedicated testing or accessibility section",
      "Summary is generic rather than role-targeted",
    ],
    ats_issues: [
      "Missing keywords: accessibility, CI/CD, Playwright",
      "Multi-column header may confuse some parsers",
    ],
    suggestions: [
      "Add 1–2 quantified outcomes per project",
      "Mirror language from your target JD in the summary",
      "List testing tools you have used, even lightly",
    ],
    recommended_roles: [
      "Frontend Engineer",
      "Full-Stack Developer",
      "UI Engineer",
    ],
  },
}

export const mockJobDescriptionUploadState: JobDescriptionUploadState = {
  resumeId: PREVIEW_RESUME_ID,
}

export const mockCareerMatchesState: CareerMatchesState = {
  resumeId: PREVIEW_RESUME_ID,
  matches: previewMatches,
}

export const mockVirtualExperienceState: VirtualExperienceState = {
  resumeId: PREVIEW_RESUME_ID,
  match: previewMatch,
  simulation: previewSimulation,
  allSimulations: [previewSimulation],
}

export const mockSkillGapState: {
  match: JobMatch
  resumeId: number
  skillGap: SkillGapContent
} = {
  match: { ...previewMatch, is_chosen: true },
  resumeId: PREVIEW_RESUME_ID,
  skillGap: {
    id: 401,
    resume_id: PREVIEW_RESUME_ID,
    job_match_id: previewMatch.id,
    readiness_score: 68,
    summary:
      "You’re close on core frontend craft. Closing testing, GraphQL, and structured system-design practice would make you competitive for mid-level Frontend Engineer roles.",
    existing_skills: [
      "React",
      "TypeScript",
      "CSS / Tailwind",
      "Git",
      "REST APIs",
    ],
    missing_technical_skills: [
      "Playwright",
      "GraphQL",
      "Performance profiling",
      "Design system contribution",
    ],
    missing_soft_skills: [
      "Stakeholder status writing",
      "Estimation under ambiguity",
    ],
    recommended_next_steps: [
      "Ship one Playwright smoke suite for a personal project",
      "Complete a small GraphQL client integration",
      "Practice a 30-minute system design for a dashboard product",
      "Write weekly status updates in a PR / journal habit",
    ],
    created_at: "2026-07-01T12:00:00Z",
  },
}

export const mockLearningRoadmapState: LearningRoadmapState = {
  resumeId: PREVIEW_RESUME_ID,
  match: { ...previewMatch, is_chosen: true },
  roadmap: {
    id: 501,
    resume_id: PREVIEW_RESUME_ID,
    job_match_id: previewMatch.id,
    created_at: "2026-07-01T12:30:00Z",
    roadmap: {
      month_1: {
        focus: "Testing foundation & shipping confidence",
        topics: ["Playwright basics", "Component testing", "CI smoke checks"],
        projects: ["Add Playwright smoke tests to a portfolio app"],
        resources: ["Playwright docs — Getting Started", "Kent C. Dodds testing trophy"],
        milestones: ["Green CI with 5 smoke tests", "Document a test plan template"],
      },
      month_2: {
        focus: "Data layer & GraphQL fluency",
        topics: ["GraphQL queries/mutations", "Cache updates", "Error states"],
        projects: ["Build a tiny GraphQL-backed dashboard"],
        resources: ["Apollo Client docs", "How to GraphQL"],
        milestones: ["Ship read + write flows", "Handle loading/error UX cleanly"],
      },
      month_3: {
        focus: "System design & stakeholder communication",
        topics: ["Dashboard architecture", "Perf budgets", "Status writing"],
        projects: ["Design a scalable analytics dashboard (write-up + diagram)"],
        resources: ["Web.dev performance", "Staff Eng communication essays"],
        milestones: ["Present a 1-page design doc", "Mock interview pass"],
      },
    },
  },
}
