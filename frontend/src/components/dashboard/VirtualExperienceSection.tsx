/**
 * VirtualExperienceSection — wraps simulation selection + career choice.
 * Full interactive tasks still live on /experience/:resumeId/:jobMatchId;
 * this section is the dashboard gate: pick a match, open the experience, then
 * return here after choosing a career to unlock Roadmap.
 */

import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Loader2, Sparkles } from "lucide-react"

import { LockedSection } from "@/components/dashboard/LockedSection"
import { Button } from "@/components/ui/button"
import { useJourneyProgress } from "@/contexts/JourneyProgressContext"
import { ApiError } from "@/services/api"
import { chooseJobMatch } from "@/services/jobMatches"
import { simulateAllCareers } from "@/services/simulation"
import type { JobMatch } from "@/types"

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
  const sorted = [...matches].sort((a, b) => a.rank - b.rank)

  const [busyId, setBusyId] = useState<number | null>(null)
  const [choosingId, setChoosingId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function ensureSimulations() {
    if (simulations || !resumeId) return simulations
    const response = await simulateAllCareers(resumeId)
    setSimulations(response.simulations)
    return response.simulations
  }

  async function openExperience(match: JobMatch) {
    if (!resumeId) return
    setError(null)
    setBusyId(match.id)
    try {
      const sims = await ensureSimulations()
      const sim = sims?.find((s) => s.job_match_id === match.id)
      if (!sim) throw new Error("Simulation not found for this match.")
      navigate(`/experience/${resumeId}/${match.id}`, {
        state: {
          simulation: sim,
          match,
          resumeId,
          allSimulations: sims,
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
      lockHint="Generate career matches first, then explore a role."
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
          Open a full simulation for any match. When you&apos;re ready, choose one
          career to unlock your skill gap and 3-month roadmap.
        </p>

        {error && (
          <p className="mb-4" style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "#FCA5A5" }}>
            {error}
          </p>
        )}

        <div className="grid gap-4 md:grid-cols-3">
          {sorted.map((match) => {
            const sim = simulations?.find((s) => s.job_match_id === match.id)
            return (
              <div
                key={match.id}
                className="cv-card relative flex min-h-[220px] flex-col p-5"
              >
                <span className="cv-badge mb-2 w-fit">Rank {match.rank}</span>
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
                    {busyId === match.id ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
                    Start experience
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    className="w-full rounded-full"
                    disabled={choosingId === match.id}
                    onClick={() => chooseCareer(match)}
                  >
                    {choosingId === match.id ? <Loader2 size={14} className="animate-spin" /> : null}
                    Choose this career
                  </Button>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </LockedSection>
  )
}
