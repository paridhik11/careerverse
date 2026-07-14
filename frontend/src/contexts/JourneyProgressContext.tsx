/**
 * JourneyProgressContext — unlock state for the continuous Dashboard scroll.
 *
 * Unlock model (independent modules):
 *   Before resume  → Resume only
 *   After resume   → Resume Analysis · Career Compatibility · Career Explorer
 *   After Top 3    → Virtual Experience
 *   After Choose   → Learning Roadmap (includes Skill Gap)
 *   Always         → Career Mentor
 *
 * Resume Analysis, Career Compatibility, and Career Explorer are independent.
 * Compatibility stores a single JD score (primaryMatch) and never feeds Top 3.
 * Explorer stores matches[] (Top 3) and is the only path that unlocks VE.
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
  | "resume-analysis"
  | "career-compatibility"
  | "career-match"
  | "virtual-experience"
  | "roadmap"

export type JdSourceMode = "own" | "sample" | null

export type JourneyUnlocks = {
  resumeUpload: true
  resumeAnalysis: boolean
  careerCompatibility: boolean
  careerMatch: boolean
  virtualExperience: boolean
  roadmap: boolean
  mentor: true
}

type JourneyProgressValue = {
  unlocks: JourneyUnlocks
  resumeId: number | null
  fileName: string | null
  report: ResumeReviewReport | null
  reviewedAt: string | null
  jdSourceMode: JdSourceMode
  selectedJdTitle: string | null
  primaryMatch: JobMatch | null
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
  setCompatibilityReady: (payload: {
    selectedJdTitle: string
    primaryMatch: JobMatch
  }) => void
  setExplorerReady: (payload: { matches: JobMatch[] }) => void
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
  const [selectedJdTitle, setSelectedJdTitle] = useState<string | null>(null)
  const [primaryMatch, setPrimaryMatch] = useState<JobMatch | null>(null)
  const [matches, setMatches] = useState<JobMatch[]>([])
  const [simulations, setSimulationsState] = useState<JobSimulationRecord[] | null>(null)
  const [chosenMatch, setChosenMatch] = useState<JobMatch | null>(null)
  const [skillGap, setSkillGapState] = useState<SkillGapContent | null>(null)
  const [roadmap, setRoadmapState] = useState<LearningRoadmapRecord | null>(null)

  const hasResume = report !== null && resumeId !== null
  const hasTop3 = matches.length > 0
  const hasChosenCareer = chosenMatch !== null

  const unlocks = useMemo<JourneyUnlocks>(
    () => ({
      resumeUpload: true,
      resumeAnalysis: hasResume,
      careerCompatibility: hasResume,
      careerMatch: hasResume,
      virtualExperience: hasTop3,
      roadmap: hasChosenCareer,
      mentor: true,
    }),
    [hasResume, hasTop3, hasChosenCareer],
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
      setSelectedJdTitle(null)
      setPrimaryMatch(null)
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

  /** Career Compatibility only — never populates Explorer Top 3. */
  const setCompatibilityReady = useCallback(
    (payload: { selectedJdTitle: string; primaryMatch: JobMatch }) => {
      setSelectedJdTitle(payload.selectedJdTitle)
      setPrimaryMatch(payload.primaryMatch)
    },
    [],
  )

  /** Career Explorer Top 3 — unlocks Virtual Experience. Independent of Compatibility. */
  const setExplorerReady = useCallback((payload: { matches: JobMatch[] }) => {
    setMatches(payload.matches)
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
    setSkillGapState(null)
    setRoadmapState(null)
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
      selectedJdTitle,
      primaryMatch,
      matches,
      simulations,
      chosenMatch,
      skillGap,
      roadmap,
      setResumeComplete,
      setJdSourceMode,
      setCompatibilityReady,
      setExplorerReady,
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
      selectedJdTitle,
      primaryMatch,
      matches,
      simulations,
      chosenMatch,
      skillGap,
      roadmap,
      setResumeComplete,
      setJdSourceMode,
      setCompatibilityReady,
      setExplorerReady,
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
