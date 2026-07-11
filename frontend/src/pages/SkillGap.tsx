/**
 * SkillGapPage — runs the Skill Gap Analysis Agent and shows results,
 * then offers roadmap generation as the next step.
 *
 * Receives the chosen career via location.state from VirtualExperiencePage:
 *   { match: JobMatch, resumeId: number }
 *
 * Flow:
 *   1. On mount, call POST /skill-gap/{resumeId} to generate the analysis.
 *   2. Display existing skills, missing skills, readiness score, and next steps.
 *   3. Show a "Generate My 3-Month Roadmap" button.
 *   4. On click, call POST /learning-roadmap/{resumeId}.
 *   5. Navigate to /learning-roadmap with the result.
 */

import { useEffect, useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  AlertCircle,
  ArrowRight,
  BarChart2,
  CheckCircle2,
  ChevronRight,
  Loader2,
  Map,
  Sparkles,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { ApiError } from "@/services/api"
import { generateSkillGap, type SkillGapContent } from "@/services/skillGap"
import { generateLearningRoadmap } from "@/services/learningRoadmap"
import type { JobMatch } from "@/types"

// ---------------------------------------------------------------------------
// Animation config
// ---------------------------------------------------------------------------

const EASE = [0.22, 1, 0.36, 1] as const

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.09, delayChildren: 0.05 } },
}

const itemVariants = {
  hidden: { opacity: 0, y: 14 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: EASE } },
}

// ---------------------------------------------------------------------------
// Location state
// ---------------------------------------------------------------------------

interface SkillGapState {
  match?: JobMatch
  resumeId?: number
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SectionLabel({ text }: { text: string }) {
  return (
    <p
      className="mb-3"
      style={{
        fontFamily: "var(--cv-font-sans)",
        fontSize: "var(--cv-text-caption)",
        fontWeight: 700,
        color: "#6B7280",
        textTransform: "uppercase",
        letterSpacing: "0.06em",
      }}
    >
      {text}
    </p>
  )
}

function SkillChip({
  label,
  variant,
}: {
  label: string
  variant: "existing" | "missing-tech" | "missing-soft"
}) {
  const styles = {
    existing: { bg: "var(--cv-card-sage)", text: "#14532D" },
    "missing-tech": { bg: "var(--cv-card-amber)", text: "#92400E" },
    "missing-soft": { bg: "var(--cv-card-lavender)", text: "#5B21B6" },
  }[variant]

  return (
    <span
      className="rounded-full px-3 py-1"
      style={{
        background: styles.bg,
        fontFamily: "var(--cv-font-sans)",
        fontSize: "var(--cv-text-caption)",
        fontWeight: 600,
        color: styles.text,
      }}
    >
      {label}
    </span>
  )
}

function ReadinessBar({ score }: { score: number }) {
  const color =
    score >= 70 ? "#22C55E" : score >= 45 ? "#F59E0B" : "#EF4444"

  return (
    <div className="mt-3">
      <div className="flex items-center justify-between mb-1.5">
        <span
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-caption)",
            color: "#6B7280",
          }}
        >
          Job Readiness
        </span>
        <span
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            fontWeight: 700,
            color,
          }}
        >
          {score}/100
        </span>
      </div>
      <div className="h-2.5 w-full rounded-full bg-gray-200 overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ background: color }}
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.8, ease: EASE, delay: 0.3 }}
        />
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function SkillGapPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as SkillGapState | null
  const match = state?.match
  const resumeId = state?.resumeId

  const [gapPhase, setGapPhase] = useState<"loading" | "done" | "error">("loading")
  const [skillGap, setSkillGap] = useState<SkillGapContent | null>(null)
  const [gapError, setGapError] = useState<string | null>(null)

  const [roadmapPhase, setRoadmapPhase] = useState<"idle" | "loading" | "error">("idle")
  const [roadmapError, setRoadmapError] = useState<string | null>(null)

  // Auto-generate skill gap on mount.
  useEffect(() => {
    if (!resumeId) {
      setGapError("No resume ID found. Please restart from the dashboard.")
      setGapPhase("error")
      return
    }

    generateSkillGap(resumeId)
      .then((res) => {
        setSkillGap(res.skill_gap)
        setGapPhase("done")
      })
      .catch((err) => {
        const msg =
          err instanceof ApiError
            ? err.message
            : "Skill gap analysis failed. Please try again."
        setGapError(msg)
        setGapPhase("error")
      })
  }, [resumeId])

  async function handleGenerateRoadmap() {
    if (!resumeId) return
    setRoadmapPhase("loading")
    setRoadmapError(null)

    try {
      const res = await generateLearningRoadmap(resumeId)
      navigate("/learning-roadmap", {
        state: { roadmap: res.roadmap, match, resumeId },
      })
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.message
          : "Roadmap generation failed. Please try again."
      setRoadmapError(msg)
      setRoadmapPhase("error")
    }
  }

  return (
    <div
      className="min-h-screen w-full px-4 py-12 md:px-6"
      style={{ background: "var(--cv-bg)" }}
    >
      <motion.div
        className="mx-auto max-w-2xl"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Career banner */}
        {match && (
          <motion.div
            variants={itemVariants}
            className="mb-6 flex items-center gap-3 rounded-[var(--cv-radius-card)] p-4"
            style={{
              background: "var(--cv-card-sage)",
              boxShadow: "var(--cv-shadow-card)",
            }}
          >
            <CheckCircle2
              size={20}
              strokeWidth={2}
              style={{ color: "#22C55E", flexShrink: 0 }}
              aria-hidden
            />
            <div>
              <p
                style={{
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-caption)",
                  fontWeight: 700,
                  color: "#166534",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                }}
              >
                Career chosen
              </p>
              <p
                style={{
                  fontFamily: "var(--cv-font-serif)",
                  fontSize: "var(--cv-text-h3)",
                  fontWeight: 500,
                  color: "#111827",
                }}
              >
                {match.role_title}
              </p>
            </div>
          </motion.div>
        )}

        {/* Page header */}
        <motion.div variants={itemVariants} className="mb-6 flex items-center gap-3">
          <div
            className="flex size-12 items-center justify-center rounded-full shrink-0"
            style={{ background: "var(--cv-card-sky-icon)" }}
            aria-hidden
          >
            <BarChart2 size={22} strokeWidth={1.6} color="#111827" />
          </div>
          <div>
            <h1
              style={{
                fontFamily: "var(--cv-font-serif)",
                fontSize: "var(--cv-text-h1)",
                fontWeight: 400,
                color: "#111827",
                lineHeight: 1.15,
              }}
            >
              Skill Gap Analysis
            </h1>
            <p
              style={{
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-small)",
                color: "#6B7280",
              }}
            >
              {match
                ? `Comparing your skills against ${match.role_title} requirements`
                : "Comparing your resume against the selected role"}
            </p>
          </div>
        </motion.div>

        {/* Skill gap content */}
        <AnimatePresence mode="wait">
          {gapPhase === "loading" && (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="rounded-[var(--cv-radius-main)] bg-white p-10 text-center"
              style={{ boxShadow: "var(--cv-shadow-main)" }}
            >
              <Loader2
                size={32}
                className="mx-auto mb-4 animate-spin"
                style={{ color: "var(--cv-accent)" }}
                aria-hidden
              />
              <p
                style={{
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-body)",
                  color: "#374151",
                  fontWeight: 500,
                }}
              >
                Analysing your skill gap…
              </p>
              <p
                className="mt-1"
                style={{
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-small)",
                  color: "#9CA3AF",
                }}
              >
                This usually takes 15–40 seconds.
              </p>
            </motion.div>
          )}

          {gapPhase === "error" && (
            <motion.div
              key="gap-error"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="rounded-[var(--cv-radius-main)] bg-white p-8"
              style={{ boxShadow: "var(--cv-shadow-main)" }}
            >
              <div className="flex items-start gap-3 mb-4">
                <AlertCircle
                  size={20}
                  style={{ color: "#EF4444", flexShrink: 0, marginTop: 2 }}
                  aria-hidden
                />
                <p
                  style={{
                    fontFamily: "var(--cv-font-sans)",
                    fontSize: "var(--cv-text-small)",
                    color: "#374151",
                  }}
                >
                  {gapError}
                </p>
              </div>
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate("/dashboard")}
              >
                Go to Dashboard
              </Button>
            </motion.div>
          )}

          {gapPhase === "done" && skillGap && (
            <motion.div
              key="results"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="flex flex-col gap-5"
            >
              {/* Readiness score card */}
              <motion.div
                variants={itemVariants}
                className="rounded-[var(--cv-radius-card)] bg-white p-6"
                style={{ boxShadow: "var(--cv-shadow-card)" }}
              >
                <SectionLabel text="Readiness Score" />
                <ReadinessBar score={skillGap.readiness_score} />
                <p
                  className="mt-4"
                  style={{
                    fontFamily: "var(--cv-font-sans)",
                    fontSize: "var(--cv-text-small)",
                    color: "#374151",
                    lineHeight: 1.7,
                  }}
                >
                  {skillGap.summary}
                </p>
              </motion.div>

              {/* Existing skills */}
              {skillGap.existing_skills.length > 0 && (
                <motion.div
                  variants={itemVariants}
                  className="rounded-[var(--cv-radius-card)] p-5"
                  style={{
                    background: "var(--cv-card-sage)",
                    boxShadow: "var(--cv-shadow-card)",
                  }}
                >
                  <SectionLabel text="Skills You Already Have" />
                  <div className="flex flex-wrap gap-2">
                    {skillGap.existing_skills.map((s, i) => (
                      <SkillChip key={i} label={s} variant="existing" />
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Missing technical skills */}
              {skillGap.missing_technical_skills.length > 0 && (
                <motion.div
                  variants={itemVariants}
                  className="rounded-[var(--cv-radius-card)] p-5"
                  style={{
                    background: "var(--cv-card-amber)",
                    boxShadow: "var(--cv-shadow-card)",
                  }}
                >
                  <SectionLabel text="Missing Technical Skills" />
                  <div className="flex flex-wrap gap-2">
                    {skillGap.missing_technical_skills.map((s, i) => (
                      <SkillChip key={i} label={s} variant="missing-tech" />
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Missing soft skills */}
              {skillGap.missing_soft_skills.length > 0 && (
                <motion.div
                  variants={itemVariants}
                  className="rounded-[var(--cv-radius-card)] p-5"
                  style={{
                    background: "var(--cv-card-lavender)",
                    boxShadow: "var(--cv-shadow-card)",
                  }}
                >
                  <SectionLabel text="Missing Soft Skills" />
                  <div className="flex flex-wrap gap-2">
                    {skillGap.missing_soft_skills.map((s, i) => (
                      <SkillChip key={i} label={s} variant="missing-soft" />
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Recommended next steps */}
              {skillGap.recommended_next_steps.length > 0 && (
                <motion.div
                  variants={itemVariants}
                  className="rounded-[var(--cv-radius-card)] bg-white p-5"
                  style={{ boxShadow: "var(--cv-shadow-card)" }}
                >
                  <SectionLabel text="Recommended Next Steps" />
                  <ol className="flex flex-col gap-3">
                    {skillGap.recommended_next_steps.map((step, i) => (
                      <li key={i} className="flex items-start gap-3">
                        <span
                          className="flex size-6 shrink-0 items-center justify-center rounded-full"
                          style={{ background: "var(--cv-accent-muted)" }}
                          aria-hidden
                        >
                          <span
                            style={{
                              fontFamily: "var(--cv-font-sans)",
                              fontSize: "0.625rem",
                              fontWeight: 700,
                              color: "var(--cv-accent)",
                            }}
                          >
                            {i + 1}
                          </span>
                        </span>
                        <span
                          style={{
                            fontFamily: "var(--cv-font-sans)",
                            fontSize: "var(--cv-text-small)",
                            color: "#374151",
                            lineHeight: 1.6,
                          }}
                        >
                          {step}
                        </span>
                      </li>
                    ))}
                  </ol>
                </motion.div>
              )}

              {/* Generate roadmap CTA */}
              <motion.div
                variants={itemVariants}
                className="rounded-[var(--cv-radius-main)] bg-white p-8 text-center"
                style={{ boxShadow: "var(--cv-shadow-main)" }}
              >
                <div
                  className="mx-auto mb-4 flex size-14 items-center justify-center rounded-full"
                  style={{ background: "var(--cv-accent-muted)" }}
                  aria-hidden
                >
                  <Map
                    size={26}
                    strokeWidth={1.6}
                    style={{ color: "var(--cv-accent)" }}
                  />
                </div>
                <h2
                  style={{
                    fontFamily: "var(--cv-font-serif)",
                    fontSize: "var(--cv-text-h2)",
                    fontWeight: 400,
                    color: "#111827",
                    lineHeight: 1.2,
                  }}
                >
                  Ready for your 3-Month Plan?
                </h2>
                <p
                  className="mx-auto mt-2 max-w-md"
                  style={{
                    fontFamily: "var(--cv-font-sans)",
                    fontSize: "var(--cv-text-small)",
                    color: "#6B7280",
                    lineHeight: 1.7,
                  }}
                >
                  We'll turn this skill gap into a practical, month-by-month
                  learning roadmap — with topics, projects, resources, and
                  milestones tailored to{" "}
                  {match ? match.role_title : "your chosen career"}.
                </p>

                {roadmapError && (
                  <div className="mt-4 flex items-start gap-2 rounded-xl bg-red-50 p-3 text-left">
                    <AlertCircle
                      size={16}
                      style={{ color: "#EF4444", flexShrink: 0, marginTop: 2 }}
                      aria-hidden
                    />
                    <p
                      style={{
                        fontFamily: "var(--cv-font-sans)",
                        fontSize: "var(--cv-text-small)",
                        color: "#7F1D1D",
                      }}
                    >
                      {roadmapError}
                    </p>
                  </div>
                )}

                <div className="mt-6 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
                  <Button
                    type="button"
                    disabled={roadmapPhase === "loading"}
                    onClick={handleGenerateRoadmap}
                    className="gap-2"
                    style={{
                      background: "var(--cv-accent)",
                      color: "#fff",
                      fontFamily: "var(--cv-font-sans)",
                      fontWeight: 600,
                    }}
                  >
                    {roadmapPhase === "loading" ? (
                      <>
                        <Loader2 size={16} className="animate-spin" aria-hidden />
                        Generating roadmap…
                      </>
                    ) : (
                      <>
                        <Sparkles size={16} strokeWidth={2} aria-hidden />
                        Generate My 3-Month Roadmap
                        <ArrowRight size={16} strokeWidth={2} aria-hidden />
                      </>
                    )}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => navigate("/dashboard")}
                    disabled={roadmapPhase === "loading"}
                  >
                    Go to Dashboard
                  </Button>
                </div>

                {roadmapPhase === "loading" && (
                  <p
                    className="mt-3"
                    style={{
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "var(--cv-text-small)",
                      color: "#9CA3AF",
                    }}
                  >
                    Building your personalised roadmap — this may take up to 60
                    seconds.
                  </p>
                )}
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}
