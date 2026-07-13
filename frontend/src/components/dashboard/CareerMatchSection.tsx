/**
 * CareerMatchSection — top 3 matches using existing CareerCard + simulation APIs.
 */

import { useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { AlertCircle, Sparkles } from "lucide-react"

import { LockedSection } from "@/components/dashboard/LockedSection"
import { CareerCard } from "@/components/CareerCard"
import { Button } from "@/components/ui/button"
import { useJourneyProgress } from "@/contexts/JourneyProgressContext"
import { ApiError } from "@/services/api"
import { simulateAllCareers } from "@/services/simulation"
import type { JobMatch } from "@/types"

export function CareerMatchSection() {
  const {
    unlocks,
    matches,
    resumeId,
    simulations,
    setSimulations,
    scrollToSection,
  } = useJourneyProgress()

  const locked = !unlocks.careerMatch
  const sorted = [...matches].sort((a, b) => a.rank - b.rank)

  const [isGenerating, setIsGenerating] = useState(false)
  const [generatingFor, setGeneratingFor] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleExplore(match: JobMatch) {
    if (!resumeId) return
    setError(null)

    if (simulations) {
      scrollToSection("virtual-experience")
      return
    }

    setIsGenerating(true)
    setGeneratingFor(match.id)
    try {
      const response = await simulateAllCareers(resumeId)
      setSimulations(response.simulations)
      scrollToSection("virtual-experience")
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Could not generate virtual experiences.",
      )
    } finally {
      setIsGenerating(false)
      setGeneratingFor(null)
    }
  }

  return (
    <LockedSection
      id="career-match"
      title="Career Match"
      locked={locked}
      lockHint="Choose a job description source in the Resume Report section above."
      className="px-6 lg:px-10"
    >
      <div className="mx-auto max-w-3xl">
        <p
          className="mb-2"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-caption)",
            fontWeight: 700,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            color: "var(--cv-accent)",
          }}
        >
          Career match
        </p>
        <h2
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h1)",
            fontWeight: 400,
            color: "var(--cv-ink)",
          }}
        >
          Your top 3 matches
        </h2>
        <p
          className="mt-3 mb-8 max-w-lg"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            color: "var(--cv-ink-muted)",
            lineHeight: 1.6,
          }}
        >
          Ranked by how closely your resume aligns with each role. Explore a virtual
          workday to unlock the experience section.
        </p>

        <AnimatePresence>
          {isGenerating && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="mb-6 flex items-center gap-3 rounded-[var(--cv-radius-card)] bg-[var(--cv-card-surface)] p-4"
              style={{ boxShadow: "var(--cv-shadow-card)" }}
            >
              <Sparkles size={20} className="animate-pulse" style={{ color: "var(--cv-accent)" }} />
              <p style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "var(--cv-ink)" }}>
                Generating virtual work experiences for all three roles…
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {error && (
          <div className="mb-5 flex items-start gap-3 rounded-[var(--cv-radius-card)] p-4" style={{ background: "rgba(239, 68, 68, 0.14)" }}>
            <AlertCircle size={18} color="#F87171" className="mt-0.5 shrink-0" />
            <p style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "#FCA5A5" }}>{error}</p>
            <Button type="button" variant="ghost" size="sm" onClick={() => setError(null)}>
              ×
            </Button>
          </div>
        )}

        <div className="flex flex-col gap-5">
          {sorted.map((match) => (
            <CareerCard
              key={match.id}
              match={match}
              onExplore={handleExplore}
              isExploring={isGenerating && generatingFor === match.id}
            />
          ))}
        </div>

        {simulations && (
          <div className="mt-6 text-center">
            <Button
              type="button"
              className="rounded-full text-white"
              style={{ background: "var(--cv-accent)" }}
              onClick={() => scrollToSection("virtual-experience")}
            >
              Continue to Virtual Experience
            </Button>
          </div>
        )}
      </div>
    </LockedSection>
  )
}
