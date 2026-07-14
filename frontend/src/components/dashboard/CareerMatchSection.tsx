/**
 * CareerMatchSection — Career Explorer: Top 3 from the uploaded resume only.
 *
 * Independent of Resume Analysis and Career Compatibility.
 * Requires only a resume. Generates Top 3 on visit if not already loaded.
 */

import { useEffect, useRef, useState } from "react"
import { Loader2 } from "lucide-react"

import { EmptyJourneyState } from "@/components/dashboard/EmptyJourneyState"
import { LockedSection } from "@/components/dashboard/LockedSection"
import { CareerCard } from "@/components/CareerCard"
import { Button } from "@/components/ui/button"
import { useJourneyProgress } from "@/contexts/JourneyProgressContext"
import { ApiError } from "@/services/api"
import { generateJobMatches } from "@/services/jobMatches"
import {
  getSampleJobDescriptions,
  seedSampleJobDescriptions,
} from "@/services/sampleJobDescriptions"
import { getCareerRecommendationMatches } from "@/utils/resumeMatch"

export function CareerMatchSection() {
  const {
    unlocks,
    resumeId,
    matches,
    simulations,
    setExplorerReady,
    scrollToSection,
  } = useJourneyProgress()

  const locked = !unlocks.careerMatch
  const displayMatches = getCareerRecommendationMatches(matches)
  const hasMatches = displayMatches.length > 0

  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const startedRef = useRef(false)

  useEffect(() => {
    if (locked || !resumeId || hasMatches || startedRef.current) return
    startedRef.current = true

    async function generateTop3() {
      setGenerating(true)
      setError(null)
      try {
        const samples = await getSampleJobDescriptions()
        if (samples.length > 0) {
          await seedSampleJobDescriptions(samples.map((s) => s.id))
        }
        const response = await generateJobMatches(resumeId!)
        setExplorerReady({ matches: response.matches })
      } catch (err) {
        startedRef.current = false
        setError(
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : "Could not generate career matches. Please try again.",
        )
      } finally {
        setGenerating(false)
      }
    }

    void generateTop3()
  }, [locked, resumeId, hasMatches, setExplorerReady])

  // Reset auto-generate guard when resume changes (new upload)
  useEffect(() => {
    startedRef.current = false
  }, [resumeId])

  async function retryGenerate() {
    if (!resumeId || generating) return
    startedRef.current = true
    setGenerating(true)
    setError(null)
    try {
      const samples = await getSampleJobDescriptions()
      if (samples.length > 0) {
        await seedSampleJobDescriptions(samples.map((s) => s.id))
      }
      const response = await generateJobMatches(resumeId)
      setExplorerReady({ matches: response.matches })
    } catch (err) {
      startedRef.current = false
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Could not generate career matches. Please try again.",
      )
    } finally {
      setGenerating(false)
    }
  }

  return (
    <LockedSection
      id="career-match"
      title="Career Explorer"
      locked={locked}
      lockHint="Upload a resume above to unlock Career Explorer."
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
          Career explorer
        </p>
        <h2
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h1)",
            fontWeight: 400,
            color: "var(--cv-ink)",
          }}
        >
          Top careers for your profile
        </h2>
        <p
          className="mt-3 mb-8 max-w-2xl"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            color: "var(--cv-ink-muted)",
            lineHeight: 1.6,
          }}
        >
          Discover the careers that best match your resume. Independent of Resume
          Analysis and Career Compatibility.
        </p>

        {!locked && generating && !hasMatches && (
          <EmptyJourneyState message="Discover the careers that best match your resume.">
            <div className="mt-4 flex items-center justify-center gap-2" style={{ color: "var(--cv-accent)" }}>
              <Loader2 size={18} className="animate-spin" />
              <span
                style={{
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-small)",
                }}
              >
                Generating your Top 3…
              </span>
            </div>
          </EmptyJourneyState>
        )}

        {!locked && error && !hasMatches && (
          <div className="text-center">
            <EmptyJourneyState message={error} />
            <Button
              type="button"
              className="mt-4 rounded-full text-white"
              style={{ background: "var(--cv-accent)" }}
              onClick={retryGenerate}
              disabled={generating}
            >
              {generating ? <Loader2 size={16} className="animate-spin" /> : null}
              Try again
            </Button>
          </div>
        )}

        {!locked && !generating && !error && !hasMatches && (
          <EmptyJourneyState message="Discover the careers that best match your resume." />
        )}

        {hasMatches && (
          <>
            <div className="flex flex-col gap-5">
              {displayMatches.map((match) => (
                <CareerCard
                  key={match.id}
                  match={match}
                  displayRank={match.displayRank}
                />
              ))}
            </div>

            <div className="mt-6 text-center">
              <Button
                type="button"
                className="rounded-full text-white"
                style={{ background: "var(--cv-accent)" }}
                onClick={() => scrollToSection("virtual-experience")}
              >
                Continue to Virtual Experience
              </Button>
              {simulations ? null : (
                <p
                  className="mt-3"
                  style={{
                    fontFamily: "var(--cv-font-sans)",
                    fontSize: "var(--cv-text-caption)",
                    color: "var(--cv-ink-muted)",
                  }}
                >
                  Virtual Experience is unlocked. Start a simulation or choose a career.
                </p>
              )}
            </div>
          </>
        )}
      </div>
    </LockedSection>
  )
}
