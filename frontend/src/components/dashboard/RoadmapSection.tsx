/**
 * RoadmapSection — skill gap (missing skills) + 3-month learning plan in one section.
 * Calls the same generateSkillGap / generateLearningRoadmap services as the
 * standalone pages.
 */

import { useEffect, useState } from "react"
import { CheckCircle2, Loader2, Map, RefreshCw } from "lucide-react"

import { LockedSection } from "@/components/dashboard/LockedSection"
import { Button } from "@/components/ui/button"
import { useJourneyProgress } from "@/contexts/JourneyProgressContext"
import { ApiError } from "@/services/api"
import { generateSkillGap, type SkillGapContent } from "@/services/skillGap"
import { generateLearningRoadmap } from "@/services/learningRoadmap"

const MONTH_STYLES = [
  { label: "Month 1" },
  { label: "Month 2" },
  { label: "Month 3" },
]

export function RoadmapSection() {
  const {
    unlocks,
    resumeId,
    chosenMatch,
    skillGap,
    roadmap,
    setSkillGap,
    setRoadmap,
  } = useJourneyProgress()

  const locked = !unlocks.roadmap
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    if (!resumeId || !chosenMatch) return
    setLoading(true)
    setError(null)
    try {
      let gap: SkillGapContent | null = skillGap
      if (!gap) {
        const gapRes = await generateSkillGap(resumeId)
        gap = gapRes.skill_gap
        setSkillGap(gap)
      }

      if (!roadmap) {
        const plan = await generateLearningRoadmap(resumeId)
        setRoadmap(plan.roadmap)
      }
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Could not generate roadmap.",
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!locked && resumeId && chosenMatch && (!skillGap || !roadmap)) {
      void load()
    }
    // intentionally re-run when unlock / chosen career changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locked, resumeId, chosenMatch?.id])

  const months = roadmap
    ? [
        { ...MONTH_STYLES[0], plan: roadmap.roadmap.month_1 },
        { ...MONTH_STYLES[1], plan: roadmap.roadmap.month_2 },
        { ...MONTH_STYLES[2], plan: roadmap.roadmap.month_3 },
      ]
    : []

  return (
    <LockedSection
      id="roadmap"
      title="Roadmap"
      locked={locked}
      lockHint="Choose a career after Virtual Experience to unlock your skill gap and learning plan."
      className="px-6 lg:px-10 pb-24"
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
          Roadmap
        </p>
        <h2
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h1)",
            fontWeight: 400,
            color: "var(--cv-ink)",
          }}
        >
          Skill gaps &amp; 3-month plan
        </h2>
        {chosenMatch && (
          <p
            className="mt-3 mb-8"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              color: "var(--cv-ink-muted)",
            }}
          >
            Tailored for <strong style={{ color: "var(--cv-ink)" }}>{chosenMatch.role_title}</strong>
          </p>
        )}

        {loading && (
          <div className="flex items-center gap-3 py-12">
            <Loader2 className="animate-spin" style={{ color: "var(--cv-accent)" }} />
            <span style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)" }}>
              Building your personalized roadmap…
            </span>
          </div>
        )}

        {error && (
          <div className="mb-6 flex flex-col items-start gap-3">
            <p style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "#FCA5A5" }}>{error}</p>
            <Button type="button" variant="outline" className="rounded-full" onClick={load}>
              <RefreshCw size={14} /> Retry
            </Button>
          </div>
        )}

        {skillGap && (
          <div className="cv-card mb-8 p-6">
            <span className="cv-badge mb-3">Skill gap</span>
            <h3 className="mb-4" style={{ fontFamily: "var(--cv-font-serif)", fontSize: "var(--cv-text-h3)", fontWeight: 500, color: "var(--cv-ink)" }}>
              Missing skills
            </h3>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <p className="mb-2" style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-caption)", fontWeight: 700, textTransform: "uppercase", color: "var(--cv-ink-muted)" }}>
                  Technical
                </p>
                <ul className="space-y-2">
                  {skillGap.missing_technical_skills.map((s, i) => (
                    <li key={i} className="flex gap-2" style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)" }}>
                      <CheckCircle2 size={14} className="mt-0.5 shrink-0" style={{ color: "var(--cv-accent)" }} />
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="mb-2" style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-caption)", fontWeight: 700, textTransform: "uppercase", color: "var(--cv-ink-muted)" }}>
                  Soft skills
                </p>
                <ul className="space-y-2">
                  {skillGap.missing_soft_skills.map((s, i) => (
                    <li key={i} className="flex gap-2" style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)" }}>
                      <CheckCircle2 size={14} className="mt-0.5 shrink-0" style={{ color: "var(--cv-accent)" }} />
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {months.length > 0 && (
          <div className="space-y-4">
            <div className="mb-2 flex items-center gap-2">
              <Map size={18} style={{ color: "var(--cv-accent)" }} />
              <h3 style={{ fontFamily: "var(--cv-font-serif)", fontSize: "var(--cv-text-h3)", fontWeight: 500 }}>
                3-month learning plan
              </h3>
            </div>
            {months.map((m) => (
              <div key={m.label} className="cv-card p-6">
                <span className="cv-badge mb-2">{m.label}</span>
                <h4 style={{ fontFamily: "var(--cv-font-serif)", fontSize: "var(--cv-text-h3)", fontWeight: 500, marginBottom: 12, color: "var(--cv-ink)" }}>
                  {m.plan.focus}
                </h4>
                <ul className="space-y-1.5">
                  {m.plan.topics.slice(0, 5).map((t, i) => (
                    <li key={i} style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "var(--cv-ink-muted)" }}>
                      · {t}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </div>
    </LockedSection>
  )
}
