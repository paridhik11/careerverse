/**
 * VirtualExperienceSection — unlocked only after Career Explorer Top 3 exists.
 *
 * Small cards: Start Experience + Choose this Career.
 * Expanded /experience page never shows those buttons.
 */

import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Loader2, Sparkles } from "lucide-react"

import { EmptyJourneyState } from "@/components/dashboard/EmptyJourneyState"
import { LockedSection } from "@/components/dashboard/LockedSection"
import { Button } from "@/components/ui/button"
import { useJourneyProgress } from "@/contexts/JourneyProgressContext"
import { ApiError } from "@/services/api"
import { chooseJobMatch } from "@/services/jobMatches"
import { simulateSingleCareer } from "@/services/simulation"
import type { JobMatch, JobSimulationRecord } from "@/types"
import { getCareerRecommendationMatches } from "@/utils/resumeMatch"

export function VirtualExperienceSection() {
  const navigate = useNavigate()
  const {
    unlocks,
    matches,
    resumeId,
    simulations,
    setSimulations,
    setCareerChosen,
    scrollToSection,
  } = useJourneyProgress()

  const locked = !unlocks.virtualExperience
  const displayMatches = getCareerRecommendationMatches(matches)
  const hasMatches = displayMatches.length > 0

  const [busyId, setBusyId] = useState<number | null>(null)
  const [choosingId, setChoosingId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  function cacheSimulation(sim: JobSimulationRecord) {
    const prev = simulations ?? []
    const without = prev.filter((s) => s.job_match_id !== sim.job_match_id)
    setSimulations([...without, sim])
  }

  async function openExperience(match: JobMatch) {
    if (!resumeId) return
    setError(null)
    setBusyId(match.id)
    try {
      const cached = simulations?.find((s) => s.job_match_id === match.id)
      const sim = cached ?? (await simulateSingleCareer(resumeId, match.id))
      if (!cached) cacheSimulation(sim)
      navigate(`/experience/${resumeId}/${match.id}`, {
        state: {
          simulation: sim,
          match,
          resumeId,
          allSimulations: simulations ?? [sim],
          returnToDashboard: true,
        },
      })
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Could not open experience.",
      )
    } finally {
      setBusyId(null)
    }
  }

  async function chooseCareer(match: JobMatch) {
    setError(null)
    setChoosingId(match.id)
    try {
      await chooseJobMatch(match.id)
      setCareerChosen({ ...match, is_chosen: true })
      scrollToSection("roadmap")
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Could not choose this career.",
      )
    } finally {
      setChoosingId(null)
    }
  }

  return (
    <LockedSection
      id="virtual-experience"
      title="Virtual Experience"
      locked={locked}
      lockHint="Open Career Explorer and generate your Top 3 careers to unlock Virtual Experience."
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
          Virtual experience
        </p>
        <h2
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h1)",
            fontWeight: 400,
            color: "var(--cv-ink)",
          }}
        >
          Try a day in the role
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
          Open a full simulation for any recommended career. When you&apos;re ready,
          choose one to unlock your skill gap and learning roadmap.
        </p>

        {error && (
          <p
            className="mb-4"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              color: "#FCA5A5",
            }}
          >
            {error}
          </p>
        )}

        {!locked && !hasMatches && (
          <EmptyJourneyState message="Generate your Top 3 in Career Explorer first, then start an experience here." />
        )}

        {hasMatches && (
          <div className="grid gap-4 md:grid-cols-3">
            {displayMatches.map((match) => {
              const sim = simulations?.find((s) => s.job_match_id === match.id)
              return (
                <div
                  key={match.id}
                  className="cv-card relative flex min-h-[220px] flex-col p-5"
                >
                  <span className="cv-badge mb-2 w-fit">Rank {match.displayRank}</span>
                  <h3
                    style={{
                      fontFamily: "var(--cv-font-serif)",
                      fontSize: "var(--cv-text-h3)",
                      fontWeight: 500,
                      color: "var(--cv-ink)",
                      lineHeight: 1.25,
                    }}
                  >
                    {match.role_title}
                  </h3>
                  <p
                    className="mt-2 flex-1"
                    style={{
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "var(--cv-text-caption)",
                      color: "var(--cv-ink-muted)",
                      lineHeight: 1.5,
                    }}
                  >
                    {sim
                      ? `${sim.simulation.tasks.length} tasks · ${sim.simulation.estimated_duration}`
                      : `${match.match_percent}% match · ${match.confidence_score} confidence`}
                  </p>
                  <div className="mt-4 flex flex-col gap-2">
                    <Button
                      type="button"
                      size="sm"
                      className="w-full rounded-full text-white"
                      style={{ background: "var(--cv-accent)" }}
                      disabled={busyId === match.id}
                      onClick={() => openExperience(match)}
                    >
                      {busyId === match.id ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <Sparkles size={14} />
                      )}
                      Start Experience
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      className="w-full rounded-full"
                      disabled={choosingId === match.id}
                      onClick={() => chooseCareer(match)}
                    >
                      {choosingId === match.id ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : null}
                      Choose this Career
                    </Button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </LockedSection>
  )
}
