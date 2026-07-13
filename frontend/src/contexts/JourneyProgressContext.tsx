/**
 * JourneyProgressContext — unlock state for the continuous Dashboard scroll.
 *
 * Lock chain (each step unlocks the next):
 *   Home (always) → Resume Upload (always) → Resume Report (after review)
 *   → Career Match (after JD source chosen + matches generated)
 *   → Virtual Experience (after matches ready)
 *   → Roadmap (after a career is chosen)
 *
 * JD choice lives inside ResumeReportSection: "own" upload or "sample" picker.
 * Selecting + confirming a JD source is what unlocks Career Match.
 */

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react"

import type {
  JobMatch,
  JobSimulationRecord,
  ResumeReviewReport,
} from "@/types"
import type { SkillGapContent } from "@/services/skillGap"
import type { LearningRoadmapRecord } from "@/types"

export type DashboardSectionId =
  | "home"
  | "resume"
  | "resume-report"
  | "career-match"
  | "virtual-experience"
  | "roadmap"

export type JdSourceMode = "own" | "sample" | null

export type JourneyUnlocks = {
  resumeUpload: true
  resumeReport: boolean
  careerMatch: boolean
  virtualExperience: boolean
  roadmap: boolean
}

type JourneyProgressValue = {
  unlocks: JourneyUnlocks
  resumeId: number | null
  fileName: string | null
  report: ResumeReviewReport | null
  reviewedAt: string | null
  jdSourceMode: JdSourceMode
  matches: JobMatch[]
  simulations: JobSimulationRecord[] | null
  chosenMatch: JobMatch | null
  skillGap: SkillGapContent | null
  roadmap: LearningRoadmapRecord | null
  setResumeComplete: (payload: {
    resumeId: number
    fileName: string
    report: ResumeReviewReport
    reviewedAt: string
  }) => void
  setJdSourceMode: (mode: JdSourceMode) => void
  setMatchesReady: (matches: JobMatch[]) => void
  setSimulations: (sims: JobSimulationRecord[]) => void
  setCareerChosen: (match: JobMatch) => void
  setSkillGap: (gap: SkillGapContent) => void
  setRoadmap: (roadmap: LearningRoadmapRecord) => void
  scrollToSection: (id: DashboardSectionId) => void
}

const JourneyProgressContext = createContext<JourneyProgressValue | null>(null)

export function JourneyProgressProvider({ children }: { children: ReactNode }) {
  const [resumeId, setResumeId] = useState<number | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const [report, setReport] = useState<ResumeReviewReport | null>(null)
  const [reviewedAt, setReviewedAt] = useState<string | null>(null)
  const [jdSourceMode, setJdSourceModeState] = useState<JdSourceMode>(null)
  const [matches, setMatches] = useState<JobMatch[]>([])
  const [simulations, setSimulationsState] = useState<JobSimulationRecord[] | null>(null)
  const [chosenMatch, setChosenMatch] = useState<JobMatch | null>(null)
  const [skillGap, setSkillGapState] = useState<SkillGapContent | null>(null)
  const [roadmap, setRoadmapState] = useState<LearningRoadmapRecord | null>(null)

  const unlocks = useMemo<JourneyUnlocks>(
    () => ({
      resumeUpload: true,
      resumeReport: report !== null && resumeId !== null,
      careerMatch: matches.length > 0,
      virtualExperience: matches.length > 0,
      roadmap: chosenMatch !== null,
    }),
    [report, resumeId, matches.length, chosenMatch],
  )

  const setResumeComplete = useCallback(
    (payload: {
      resumeId: number
      fileName: string
      report: ResumeReviewReport
      reviewedAt: string
    }) => {
      setResumeId(payload.resumeId)
      setFileName(payload.fileName)
      setReport(payload.report)
      setReviewedAt(payload.reviewedAt)
      // Fresh resume resets downstream journey state
      setJdSourceModeState(null)
      setMatches([])
      setSimulationsState(null)
      setChosenMatch(null)
      setSkillGapState(null)
      setRoadmapState(null)
    },
    [],
  )

  const setJdSourceMode = useCallback((mode: JdSourceMode) => {
    setJdSourceModeState(mode)
  }, [])

  const setMatchesReady = useCallback((next: JobMatch[]) => {
    setMatches(next)
    setSimulationsState(null)
    setChosenMatch(null)
    setSkillGapState(null)
    setRoadmapState(null)
  }, [])

  const setSimulations = useCallback((sims: JobSimulationRecord[]) => {
    setSimulationsState(sims)
  }, [])

  const setCareerChosen = useCallback((match: JobMatch) => {
    setChosenMatch(match)
  }, [])

  const setSkillGap = useCallback((gap: SkillGapContent) => {
    setSkillGapState(gap)
  }, [])

  const setRoadmap = useCallback((plan: LearningRoadmapRecord) => {
    setRoadmapState(plan)
  }, [])

  const scrollToSection = useCallback((id: DashboardSectionId) => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }, [])

  const value = useMemo<JourneyProgressValue>(
    () => ({
      unlocks,
      resumeId,
      fileName,
      report,
      reviewedAt,
      jdSourceMode,
      matches,
      simulations,
      chosenMatch,
      skillGap,
      roadmap,
      setResumeComplete,
      setJdSourceMode,
      setMatchesReady,
      setSimulations,
      setCareerChosen,
      setSkillGap,
      setRoadmap,
      scrollToSection,
    }),
    [
      unlocks,
      resumeId,
      fileName,
      report,
      reviewedAt,
      jdSourceMode,
      matches,
      simulations,
      chosenMatch,
      skillGap,
      roadmap,
      setResumeComplete,
      setJdSourceMode,
      setMatchesReady,
      setSimulations,
      setCareerChosen,
      setSkillGap,
      setRoadmap,
      scrollToSection,
    ],
  )

  return (
    <JourneyProgressContext.Provider value={value}>
      {children}
    </JourneyProgressContext.Provider>
  )
}

export function useJourneyProgress(): JourneyProgressValue {
  const ctx = useContext(JourneyProgressContext)
  if (!ctx) {
    throw new Error("useJourneyProgress must be used within JourneyProgressProvider")
  }
  return ctx
}
