/**
 * CareerMatchesPage — displays the Top 3 career matches as premium animated cards.
 *
 * Data flow:
 *   JobDescriptionUploadPage navigates here with `CareerMatchesState` in
 *   location.state: { matches: JobMatch[], resumeId: number }.
 *
 * When the user clicks "Explore Experience" on any card:
 *   1. Calls POST /job-matches/{resumeId}/simulate-all (once — cached afterward).
 *   2. Finds the simulation for the clicked job match by job_match_id.
 *   3. Navigates to /experience/{resumeId}/{jobMatchId} with all data in state.
 *
 * Animation:
 *   Framer Motion container with staggerChildren drives cards into view.
 *   Each CareerCard handles its own hover elevation.
 */

import { useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { AnimatePresence, motion } from "framer-motion"
import { AlertCircle, ArrowLeft, Sparkles } from "lucide-react"

import { CareerCard } from "@/components/CareerCard"
import { Button } from "@/components/ui/button"
import { simulateAllCareers } from "@/services/simulation"
import { ApiError } from "@/services/api"
import type { CareerMatchesState, JobMatch, JobSimulationRecord } from "@/types"

const EASE = [0.22, 1, 0.36, 1] as const

/* ─── Skeleton card ─────────────────────────────────────────────────────── */

function SkeletonCard({ delay = 0 }: { delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: EASE }}
      className="rounded-[var(--cv-radius-card)] p-6"
      style={{ background: "#F9FAFB", boxShadow: "var(--cv-shadow-card)" }}
    >
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="size-12 animate-pulse rounded-full bg-gray-200" />
          <div className="flex flex-col gap-2">
            <div className="h-7 w-48 animate-pulse rounded-lg bg-gray-200" />
            <div className="h-4 w-28 animate-pulse rounded-full bg-gray-200" />
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <div className="h-10 w-16 animate-pulse rounded-lg bg-gray-200" />
          <div className="h-3 w-10 animate-pulse rounded bg-gray-200" />
        </div>
      </div>
      <div className="mb-3 space-y-2">
        <div className="h-4 w-full animate-pulse rounded bg-gray-200" />
        <div className="h-4 w-5/6 animate-pulse rounded bg-gray-200" />
        <div className="h-4 w-4/6 animate-pulse rounded bg-gray-200" />
      </div>
      <div className="mb-5 flex gap-2">
        {[80, 96, 64].map((w, i) => (
          <div key={i} className="h-6 animate-pulse rounded-full bg-gray-200" style={{ width: w }} />
        ))}
      </div>
      <div className="h-10 w-full animate-pulse rounded-[var(--cv-radius-card)] bg-gray-200" />
    </motion.div>
  )
}

/* ─── Missing state ─────────────────────────────────────────────────────── */

function MissingMatchesState() {
  const navigate = useNavigate()
  return (
    <div
      className="flex min-h-screen w-full items-center justify-center px-4 py-10"
      style={{ background: "var(--cv-bg)" }}
    >
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: EASE }}
        className="w-full max-w-md rounded-[var(--cv-radius-main)] bg-white p-8 text-center"
        style={{ boxShadow: "var(--cv-shadow-main)" }}
      >
        <div
          className="mx-auto mb-4 flex size-14 items-center justify-center rounded-full"
          style={{ background: "var(--cv-card-sage-icon)" }}
          aria-hidden
        >
          <Sparkles size={24} strokeWidth={1.6} color="#111827" />
        </div>
        <h1
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h2)",
            fontWeight: 400,
            color: "#111827",
            lineHeight: 1.2,
          }}
        >
          No career matches found
        </h1>
        <p
          className="mt-3 text-gray-500"
          style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", lineHeight: 1.6 }}
        >
          Career matches are generated from your resume and uploaded job descriptions.
          Please start from the beginning of the flow.
        </p>
        <Button
          type="button"
          className="mt-6 w-full text-white hover:opacity-90"
          style={{ background: "var(--cv-accent)" }}
          onClick={() => navigate("/resume/upload")}
        >
          Start over
        </Button>
      </motion.div>
    </div>
  )
}

/* ─── Generating simulation overlay ─────────────────────────────────────── */

function GeneratingOverlay() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.25 }}
      className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-6 px-4"
      style={{ background: "rgba(237,234,227,0.85)", backdropFilter: "blur(6px)" }}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.35, ease: EASE }}
        className="flex max-w-sm flex-col items-center gap-4 rounded-[var(--cv-radius-main)] bg-white p-8 text-center"
        style={{ boxShadow: "var(--cv-shadow-main)" }}
      >
        <div
          className="flex size-14 items-center justify-center rounded-full"
          style={{ background: "var(--cv-card-lavender-icon)" }}
        >
          <Sparkles size={24} strokeWidth={1.8} color="#111827" aria-hidden />
        </div>
        <div>
          <h2
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize: "var(--cv-text-h2)",
              fontWeight: 400,
              color: "#111827",
              lineHeight: 1.2,
            }}
          >
            Generating your Virtual Work Experience
          </h2>
          <p
            className="mt-2 text-gray-500"
            style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", lineHeight: 1.6 }}
          >
            CareerVerse is crafting realistic workplace tasks for all three roles.
            This may take up to 60 seconds.
          </p>
        </div>
        {/* Pulsing dots */}
        <div className="flex items-center gap-2">
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              className="inline-block size-2 rounded-full"
              style={{ background: "var(--cv-accent)" }}
              animate={{ scale: [1, 1.4, 1], opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.2, delay: i * 0.2, repeat: Infinity, ease: "easeInOut" }}
              aria-hidden
            />
          ))}
        </div>
      </motion.div>
    </motion.div>
  )
}

/* ─── Main page ─────────────────────────────────────────────────────────── */

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.1, delayChildren: 0.1 },
  },
}

export function CareerMatchesPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as CareerMatchesState | null

  const [simulations, setSimulations] = useState<JobSimulationRecord[] | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatingForMatchId, setGeneratingForMatchId] = useState<number | null>(null)
  const [simulationError, setSimulationError] = useState<string | null>(null)

  if (!state?.matches || state.matches.length === 0) {
    return <MissingMatchesState />
  }

  const { matches, resumeId } = state
  const sortedMatches = [...matches].sort((a, b) => a.rank - b.rank)

  /* ── Explore Experience handler ─────────────────────────────────────── */

  async function handleExplore(match: JobMatch) {
    setSimulationError(null)

    // Use cached simulations if already generated
    const existingSimulations = simulations

    if (existingSimulations) {
      const sim = existingSimulations.find((s) => s.job_match_id === match.id)
      if (sim) {
        navigate(`/experience/${resumeId}/${match.id}`, {
          state: {
            simulation: sim,
            match,
            resumeId,
            allSimulations: existingSimulations,
          },
        })
        return
      }
    }

    // Generate all three simulations
    setIsGenerating(true)
    setGeneratingForMatchId(match.id)

    try {
      const response = await simulateAllCareers(resumeId)
      setSimulations(response.simulations)

      const sim = response.simulations.find((s) => s.job_match_id === match.id)
      if (!sim) {
        throw new Error("Simulation not found for this career match.")
      }

      navigate(`/experience/${resumeId}/${match.id}`, {
        state: {
          simulation: sim,
          match,
          resumeId,
          allSimulations: response.simulations,
        },
      })
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : error instanceof Error
            ? error.message
            : "Failed to generate the virtual experience. Please try again."
      setSimulationError(message)
    } finally {
      setIsGenerating(false)
      setGeneratingForMatchId(null)
    }
  }

  return (
    <div
      className="relative min-h-screen w-full px-4 py-8 md:px-6"
      style={{ background: "var(--cv-bg)" }}
    >
      {/* Simulation generation overlay */}
      <AnimatePresence>{isGenerating && <GeneratingOverlay />}</AnimatePresence>

      <motion.div
        className="mx-auto max-w-3xl"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Back navigation */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: EASE }}
          className="mb-6"
        >
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="flex items-center gap-1.5 rounded-full px-3 py-1.5 transition-colors duration-150 hover:bg-black/5"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              fontWeight: 500,
              color: "#6B7280",
            }}
          >
            <ArrowLeft size={15} strokeWidth={2} aria-hidden />
            Back
          </button>
        </motion.div>

        {/* Page header */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: EASE }}
          className="mb-8 text-center"
        >
          <div
            className="mx-auto mb-4 flex size-12 items-center justify-center rounded-full"
            style={{ background: "var(--cv-card-sage-icon)" }}
            aria-hidden
          >
            <Sparkles size={22} strokeWidth={1.8} color="#111827" />
          </div>
          <h1
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize: "var(--cv-text-h1)",
              fontWeight: 400,
              color: "#111827",
              lineHeight: 1.15,
            }}
          >
            Your Top 3 Career Matches
          </h1>
          <p
            className="mx-auto mt-3 max-w-lg text-gray-500"
            style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", lineHeight: 1.7 }}
          >
            Ranked by how closely your resume aligns with each role.
            Explore a virtual work experience to see what each career really feels like — then choose your path.
          </p>
        </motion.div>

        {/* Error banner */}
        <AnimatePresence>
          {simulationError && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.3, ease: EASE }}
              className="mb-5 flex items-start gap-3 rounded-[var(--cv-radius-card)] p-4"
              style={{ background: "#FEF2F2", boxShadow: "var(--cv-shadow-card)" }}
            >
              <AlertCircle size={18} strokeWidth={2} color="#DC2626" className="mt-0.5 shrink-0" aria-hidden />
              <div className="min-w-0 flex-1">
                <p style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", fontWeight: 600, color: "#991B1B" }}>
                  Could not generate experience
                </p>
                <p className="mt-0.5" style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-caption)", color: "#B91C1C" }}>
                  {simulationError}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSimulationError(null)}
                className="shrink-0 text-red-400 hover:text-red-600 transition-colors"
                aria-label="Dismiss error"
              >
                ×
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Career cards */}
        <motion.div
          variants={containerVariants}
          className="flex flex-col gap-5"
        >
          {sortedMatches.map((match) => (
            <CareerCard
              key={match.id}
              match={match}
              onExplore={handleExplore}
              isExploring={isGenerating && generatingForMatchId === match.id}
            />
          ))}
        </motion.div>

        {/* Footer action */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.5, ease: EASE }}
          className="mt-8 pb-4 text-center"
        >
          <p
            className="mb-3 text-gray-400"
            style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)" }}
          >
            Not happy with these matches?
          </p>
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate("/resume/upload")}
          >
            Analyze a different resume
          </Button>
        </motion.div>
      </motion.div>
    </div>
  )
}
