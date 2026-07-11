/**
 * SkillGapPage — premium redesign of the Skill Gap Analysis screen.
 *
 * Receives the chosen career via location.state from VirtualExperiencePage:
 *   { match: JobMatch, resumeId: number }
 *
 * Flow:
 *   1. On mount, call POST /skill-gap/{resumeId} to generate the analysis.
 *   2. Display career title, circular readiness score, summary,
 *      existing / missing skills, and recommended next steps.
 *   3. "View My Learning Roadmap" — calls POST /learning-roadmap/{resumeId},
 *      then navigates to /learning-roadmap with the result.
 */

import { useEffect, useRef, useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { motion, AnimatePresence, useInView } from "framer-motion"
import {
  AlertCircle,
  ArrowRight,
  BarChart2,
  CheckCircle2,
  Map,
  Sparkles,
  TrendingUp,
  Zap,
  Heart,
  Loader2,
  RefreshCw,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { ApiError } from "@/services/api"
import { generateSkillGap, type SkillGapContent } from "@/services/skillGap"
import { generateLearningRoadmap } from "@/services/learningRoadmap"
import type { JobMatch } from "@/types"

// ---------------------------------------------------------------------------
// Animation presets (DESIGN_SYSTEM.md expo-out easing)
// ---------------------------------------------------------------------------

const EASE = [0.22, 1, 0.36, 1] as const

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: (delay = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: EASE, delay },
  }),
}

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
}

const item = {
  hidden: { opacity: 0, y: 14 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.38, ease: EASE } },
}

// ---------------------------------------------------------------------------
// Location state
// ---------------------------------------------------------------------------

interface SkillGapState {
  match?: JobMatch
  resumeId?: number
}

// ---------------------------------------------------------------------------
// Score helpers
// ---------------------------------------------------------------------------

function scoreColor(score: number) {
  if (score >= 70) return { stroke: "#22C55E", text: "#15803D", bg: "#F0FDF4", label: "Strong" }
  if (score >= 45) return { stroke: "#F59E0B", text: "#B45309", bg: "#FFFBEB", label: "Developing" }
  return { stroke: "#EF4444", text: "#DC2626", bg: "#FEF2F2", label: "Early stage" }
}

// ---------------------------------------------------------------------------
// Circular Progress Ring
// ---------------------------------------------------------------------------

function CircularScore({ score }: { score: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: "-60px" })
  const { stroke, text, bg, label } = scoreColor(score)

  const RADIUS = 52
  const CIRCUMFERENCE = 2 * Math.PI * RADIUS
  const offset = CIRCUMFERENCE - (score / 100) * CIRCUMFERENCE

  return (
    <div ref={ref} className="flex flex-col items-center gap-3">
      <div className="relative" style={{ width: 148, height: 148 }}>
        <svg
          width="148"
          height="148"
          viewBox="0 0 148 148"
          style={{ transform: "rotate(-90deg)" }}
          aria-hidden
        >
          {/* Track */}
          <circle
            cx="74"
            cy="74"
            r={RADIUS}
            fill="none"
            stroke="#E5E7EB"
            strokeWidth="11"
          />
          {/* Progress arc */}
          <motion.circle
            cx="74"
            cy="74"
            r={RADIUS}
            fill="none"
            stroke={stroke}
            strokeWidth="11"
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            initial={{ strokeDashoffset: CIRCUMFERENCE }}
            animate={inView ? { strokeDashoffset: offset } : { strokeDashoffset: CIRCUMFERENCE }}
            transition={{ duration: 1.4, ease: EASE, delay: 0.15 }}
          />
        </svg>

        {/* Center label */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-center"
          style={{ pointerEvents: "none" }}
        >
          <motion.span
            initial={{ opacity: 0, scale: 0.7 }}
            animate={inView ? { opacity: 1, scale: 1 } : {}}
            transition={{ duration: 0.5, ease: EASE, delay: 0.4 }}
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize: "2.125rem",
              fontWeight: 400,
              color: text,
              lineHeight: 1,
            }}
          >
            {score}
          </motion.span>
          <span
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "0.6875rem",
              fontWeight: 500,
              color: "#9CA3AF",
              lineHeight: 1,
              marginTop: 2,
            }}
          >
            / 100
          </span>
        </div>
      </div>

      {/* Badge */}
      <span
        className="rounded-full px-3 py-1"
        style={{
          background: bg,
          fontFamily: "var(--cv-font-sans)",
          fontSize: "var(--cv-text-caption)",
          fontWeight: 700,
          color: text,
          letterSpacing: "0.04em",
        }}
      >
        {label}
      </span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Skeleton loaders
// ---------------------------------------------------------------------------

function Pulse({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <div
      className={`animate-pulse rounded-xl bg-gray-200 ${className ?? ""}`}
      style={style}
      aria-hidden
    />
  )
}

function SkeletonPage() {
  return (
    <motion.div
      key="skeleton"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col gap-6"
    >
      {/* Hero skeleton */}
      <div
        className="rounded-[var(--cv-radius-main)] bg-white p-8"
        style={{ boxShadow: "var(--cv-shadow-main)" }}
      >
        <div className="flex flex-col md:flex-row gap-8 items-start">
          {/* Circle skeleton */}
          <div className="flex flex-col items-center gap-3 mx-auto md:mx-0">
            <Pulse style={{ width: 148, height: 148, borderRadius: "50%" }} />
            <Pulse style={{ width: 80, height: 24 }} />
          </div>
          {/* Right side skeleton */}
          <div className="flex-1 space-y-3 w-full">
            <Pulse style={{ width: "55%", height: 14 }} />
            <Pulse style={{ width: "70%", height: 32 }} />
            <Pulse style={{ width: "100%", height: 80 }} />
          </div>
        </div>
      </div>

      {/* Skills grid skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="rounded-[var(--cv-radius-card)] p-5 space-y-3"
            style={{ background: "#F9FAFB", boxShadow: "var(--cv-shadow-card)" }}
          >
            <Pulse style={{ width: "60%", height: 12 }} />
            <div className="flex flex-wrap gap-2">
              {[90, 70, 110, 80].map((w, j) => (
                <Pulse key={j} style={{ width: w, height: 26, borderRadius: 9999 }} />
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Steps skeleton */}
      <div
        className="rounded-[var(--cv-radius-card)] bg-white p-6 space-y-4"
        style={{ boxShadow: "var(--cv-shadow-card)" }}
      >
        <Pulse style={{ width: "40%", height: 14 }} />
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex items-start gap-3">
            <Pulse style={{ width: 28, height: 28, borderRadius: "50%", flexShrink: 0 }} />
            <div className="flex-1 space-y-2 pt-1">
              <Pulse style={{ width: "85%", height: 12 }} />
              <Pulse style={{ width: "60%", height: 12 }} />
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  )
}

// ---------------------------------------------------------------------------
// Section label
// ---------------------------------------------------------------------------

function SectionLabel({ text }: { text: string }) {
  return (
    <p
      className="mb-4"
      style={{
        fontFamily: "var(--cv-font-sans)",
        fontSize: "var(--cv-text-caption)",
        fontWeight: 700,
        color: "#6B7280",
        textTransform: "uppercase",
        letterSpacing: "0.07em",
      }}
    >
      {text}
    </p>
  )
}

// ---------------------------------------------------------------------------
// Skill chip
// ---------------------------------------------------------------------------

type ChipVariant = "existing" | "missing-tech" | "missing-soft"

const CHIP_STYLES: Record<ChipVariant, { bg: string; text: string; border: string }> = {
  existing: {
    bg: "var(--cv-card-sage)",
    text: "#14532D",
    border: "var(--cv-card-sage-icon)",
  },
  "missing-tech": {
    bg: "var(--cv-card-amber)",
    text: "#92400E",
    border: "#F6DC6D",
  },
  "missing-soft": {
    bg: "var(--cv-card-sky)",
    text: "#1E40AF",
    border: "var(--cv-card-sky-icon)",
  },
}

function SkillChip({ label, variant }: { label: string; variant: ChipVariant }) {
  const s = CHIP_STYLES[variant]
  return (
    <span
      className="rounded-full px-3 py-1.5"
      style={{
        background: s.bg,
        border: `1.5px solid ${s.border}`,
        fontFamily: "var(--cv-font-sans)",
        fontSize: "var(--cv-text-caption)",
        fontWeight: 600,
        color: s.text,
        display: "inline-block",
      }}
    >
      {label}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Skills card
// ---------------------------------------------------------------------------

interface SkillsCardProps {
  label: string
  skills: string[]
  variant: ChipVariant
  icon: React.ReactNode
  cardBg: string
  emptyMsg: string
}

function SkillsCard({ label, skills, variant, icon, cardBg, emptyMsg }: SkillsCardProps) {
  return (
    <motion.div
      variants={item}
      className="rounded-[var(--cv-radius-card)] p-5 flex flex-col gap-3"
      style={{ background: cardBg, boxShadow: "var(--cv-shadow-card)" }}
    >
      <div className="flex items-center gap-2 mb-1">
        {icon}
        <SectionLabel text={label} />
      </div>
      {skills.length === 0 ? (
        <p
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            color: "#9CA3AF",
            fontStyle: "italic",
          }}
        >
          {emptyMsg}
        </p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {skills.map((s, i) => (
            <SkillChip key={i} label={s} variant={variant} />
          ))}
        </div>
      )}
    </motion.div>
  )
}

// ---------------------------------------------------------------------------
// Timeline step
// ---------------------------------------------------------------------------

function TimelineStep({
  index,
  text,
  total,
}: {
  index: number
  text: string
  total: number
}) {
  const isLast = index === total - 1

  return (
    <motion.li variants={item} className="flex items-start gap-4">
      <div className="flex flex-col items-center">
        {/* Number bubble */}
        <div
          className="flex size-8 shrink-0 items-center justify-center rounded-full z-10"
          style={{ background: "var(--cv-accent)", boxShadow: "0 0 0 3px var(--cv-accent-muted)" }}
        >
          <span
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "0.6875rem",
              fontWeight: 700,
              color: "#fff",
            }}
          >
            {index + 1}
          </span>
        </div>
        {/* Connector line */}
        {!isLast && (
          <div
            className="flex-1 mt-1"
            style={{ width: 2, background: "var(--cv-accent-muted)", minHeight: 24 }}
          />
        )}
      </div>

      <div className="pb-5 pt-0.5 flex-1">
        <p
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            color: "#1F2937",
            lineHeight: 1.65,
          }}
        >
          {text}
        </p>
      </div>
    </motion.li>
  )
}

// ---------------------------------------------------------------------------
// Error card
// ---------------------------------------------------------------------------

function ErrorCard({
  message,
  onRetry,
}: {
  message: string
  onRetry?: () => void
}) {
  const navigate = useNavigate()
  return (
    <motion.div
      key="error"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.35, ease: EASE }}
      className="rounded-[var(--cv-radius-main)] bg-white p-10"
      style={{ boxShadow: "var(--cv-shadow-main)" }}
    >
      <div className="mx-auto mb-5 flex size-14 items-center justify-center rounded-full bg-red-50">
        <AlertCircle size={26} style={{ color: "#EF4444" }} aria-hidden />
      </div>
      <h2
        className="mb-2 text-center"
        style={{
          fontFamily: "var(--cv-font-serif)",
          fontSize: "var(--cv-text-h3)",
          fontWeight: 500,
          color: "#111827",
        }}
      >
        Analysis failed
      </h2>
      <p
        className="mb-6 text-center mx-auto max-w-sm"
        style={{
          fontFamily: "var(--cv-font-sans)",
          fontSize: "var(--cv-text-small)",
          color: "#6B7280",
          lineHeight: 1.6,
        }}
      >
        {message}
      </p>
      <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
        {onRetry && (
          <Button
            type="button"
            onClick={onRetry}
            className="gap-2"
            style={{
              background: "var(--cv-accent)",
              color: "#fff",
              fontFamily: "var(--cv-font-sans)",
              fontWeight: 600,
            }}
          >
            <RefreshCw size={15} strokeWidth={2} aria-hidden />
            Try again
          </Button>
        )}
        <Button
          type="button"
          variant="outline"
          onClick={() => navigate("/dashboard")}
        >
          Go to Dashboard
        </Button>
      </div>
    </motion.div>
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

  const [phase, setPhase] = useState<"loading" | "done" | "error">("loading")
  const [skillGap, setSkillGap] = useState<SkillGapContent | null>(null)
  const [gapError, setGapError] = useState<string | null>(null)

  const [roadmapPhase, setRoadmapPhase] = useState<"idle" | "loading" | "error">("idle")
  const [roadmapError, setRoadmapError] = useState<string | null>(null)

  function runAnalysis() {
    if (!resumeId) {
      setGapError("No resume ID found. Please restart from the dashboard.")
      setPhase("error")
      return
    }
    setPhase("loading")
    setGapError(null)
    generateSkillGap(resumeId)
      .then((res) => {
        setSkillGap(res.skill_gap)
        setPhase("done")
      })
      .catch((err) => {
        const msg =
          err instanceof ApiError
            ? err.message
            : "Skill gap analysis failed. Please try again."
        setGapError(msg)
        setPhase("error")
      })
  }

  // Run on mount.
  useEffect(() => { runAnalysis() }, [resumeId]) // eslint-disable-line react-hooks/exhaustive-deps

  async function handleViewRoadmap() {
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
      className="min-h-screen w-full px-4 py-10 md:px-8 lg:px-10"
      style={{ background: "var(--cv-bg)" }}
    >
      <div className="mx-auto max-w-4xl">

        {/* ── Page header ─────────────────────────────────────────────── */}
        <motion.div
          custom={0}
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          className="mb-8 flex items-center gap-4"
        >
          <div
            className="flex size-12 shrink-0 items-center justify-center rounded-full"
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
                marginTop: 2,
              }}
            >
              {match
                ? `Comparing your profile against ${match.role_title} requirements`
                : "Comparing your resume against the selected role"}
            </p>
          </div>
        </motion.div>

        {/* ── Content (animated state machine) ────────────────────────── */}
        <AnimatePresence mode="wait">

          {/* Loading */}
          {phase === "loading" && <SkeletonPage key="skeleton" />}

          {/* Error */}
          {phase === "error" && (
            <ErrorCard
              key="error"
              message={gapError ?? "Something went wrong."}
              onRetry={resumeId ? runAnalysis : undefined}
            />
          )}

          {/* Results */}
          {phase === "done" && skillGap && (
            <motion.div
              key="results"
              variants={stagger}
              initial="hidden"
              animate="visible"
              className="flex flex-col gap-6"
            >

              {/* ── Hero card: score + career + summary ─────────────────── */}
              <motion.div
                variants={item}
                className="rounded-[var(--cv-radius-main)] bg-white overflow-hidden"
                style={{ boxShadow: "var(--cv-shadow-main)" }}
              >
                {/* Career title strip */}
                {match && (
                  <div
                    className="flex items-center gap-3 px-7 py-4 border-b"
                    style={{
                      background: "var(--cv-card-sky)",
                      borderColor: "var(--cv-card-sky-icon)",
                    }}
                  >
                    <CheckCircle2
                      size={18}
                      strokeWidth={2.5}
                      style={{ color: "#2563EB", flexShrink: 0 }}
                      aria-hidden
                    />
                    <div className="min-w-0">
                      <p
                        style={{
                          fontFamily: "var(--cv-font-sans)",
                          fontSize: "var(--cv-text-caption)",
                          fontWeight: 700,
                          color: "#1D4ED8",
                          textTransform: "uppercase",
                          letterSpacing: "0.06em",
                        }}
                      >
                        Target career
                      </p>
                      <h2
                        className="truncate"
                        style={{
                          fontFamily: "var(--cv-font-serif)",
                          fontSize: "var(--cv-text-h3)",
                          fontWeight: 500,
                          color: "#111827",
                        }}
                      >
                        {match.role_title}
                      </h2>
                    </div>
                    {/* Match % badge */}
                    <span
                      className="ml-auto shrink-0 rounded-full px-3 py-1"
                      style={{
                        background: "white",
                        border: "1.5px solid var(--cv-card-sky-icon)",
                        fontFamily: "var(--cv-font-sans)",
                        fontSize: "var(--cv-text-caption)",
                        fontWeight: 700,
                        color: "#1D4ED8",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {match.match_percent}% match
                    </span>
                  </div>
                )}

                {/* Score + summary body */}
                <div className="flex flex-col md:flex-row gap-8 items-start p-8">
                  {/* Left: circular score */}
                  <div className="mx-auto md:mx-0 shrink-0">
                    <CircularScore score={skillGap.readiness_score} />
                    <p
                      className="mt-3 text-center"
                      style={{
                        fontFamily: "var(--cv-font-sans)",
                        fontSize: "var(--cv-text-caption)",
                        color: "#9CA3AF",
                        maxWidth: 148,
                      }}
                    >
                      Job Readiness Score
                    </p>
                  </div>

                  {/* Right: summary */}
                  <div className="flex-1">
                    <div className="mb-3 flex items-center gap-2">
                      <TrendingUp
                        size={16}
                        strokeWidth={2}
                        style={{ color: "var(--cv-accent)", flexShrink: 0 }}
                        aria-hidden
                      />
                      <span
                        style={{
                          fontFamily: "var(--cv-font-sans)",
                          fontSize: "var(--cv-text-caption)",
                          fontWeight: 700,
                          color: "#6B7280",
                          textTransform: "uppercase",
                          letterSpacing: "0.07em",
                        }}
                      >
                        Analysis Summary
                      </span>
                    </div>
                    <p
                      style={{
                        fontFamily: "var(--cv-font-sans)",
                        fontSize: "var(--cv-text-body)",
                        color: "#1F2937",
                        lineHeight: 1.75,
                      }}
                    >
                      {skillGap.summary}
                    </p>

                    {/* Quick stats row */}
                    <div className="mt-5 grid grid-cols-3 gap-3">
                      {[
                        {
                          count: skillGap.existing_skills.length,
                          label: "Skills matched",
                          color: "#16A34A",
                          bg: "var(--cv-card-sage)",
                        },
                        {
                          count: skillGap.missing_technical_skills.length,
                          label: "Tech gaps",
                          color: "#B45309",
                          bg: "var(--cv-card-amber)",
                        },
                        {
                          count: skillGap.missing_soft_skills.length,
                          label: "Soft gaps",
                          color: "#1D4ED8",
                          bg: "var(--cv-card-sky)",
                        },
                      ].map(({ count, label, color, bg }) => (
                        <div
                          key={label}
                          className="rounded-xl p-3 text-center"
                          style={{ background: bg }}
                        >
                          <p
                            style={{
                              fontFamily: "var(--cv-font-serif)",
                              fontSize: "1.5rem",
                              fontWeight: 400,
                              color,
                              lineHeight: 1,
                            }}
                          >
                            {count}
                          </p>
                          <p
                            style={{
                              fontFamily: "var(--cv-font-sans)",
                              fontSize: "0.6875rem",
                              fontWeight: 500,
                              color,
                              marginTop: 2,
                              opacity: 0.8,
                            }}
                          >
                            {label}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* ── Skills grid ─────────────────────────────────────────── */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <SkillsCard
                  label="Skills you have"
                  skills={skillGap.existing_skills}
                  variant="existing"
                  cardBg="var(--cv-card-sage)"
                  emptyMsg="No matching skills found."
                  icon={
                    <CheckCircle2
                      size={15}
                      strokeWidth={2.5}
                      style={{ color: "#16A34A", flexShrink: 0, marginBottom: 2 }}
                      aria-hidden
                    />
                  }
                />

                <SkillsCard
                  label="Missing technical"
                  skills={skillGap.missing_technical_skills}
                  variant="missing-tech"
                  cardBg="var(--cv-card-amber)"
                  emptyMsg="No technical gaps — great!"
                  icon={
                    <Zap
                      size={15}
                      strokeWidth={2.5}
                      style={{ color: "#B45309", flexShrink: 0, marginBottom: 2 }}
                      aria-hidden
                    />
                  }
                />

                <SkillsCard
                  label="Missing soft skills"
                  skills={skillGap.missing_soft_skills}
                  variant="missing-soft"
                  cardBg="var(--cv-card-sky)"
                  emptyMsg="No soft skill gaps — great!"
                  icon={
                    <Heart
                      size={15}
                      strokeWidth={2.5}
                      style={{ color: "#1D4ED8", flexShrink: 0, marginBottom: 2 }}
                      aria-hidden
                    />
                  }
                />
              </div>

              {/* ── Recommended next steps timeline ─────────────────────── */}
              {skillGap.recommended_next_steps.length > 0 && (
                <motion.div
                  variants={item}
                  className="rounded-[var(--cv-radius-card)] bg-white p-7"
                  style={{ boxShadow: "var(--cv-shadow-card)" }}
                >
                  <div className="mb-5 flex items-center gap-2">
                    <div
                      className="flex size-8 items-center justify-center rounded-full"
                      style={{ background: "var(--cv-accent-muted)" }}
                      aria-hidden
                    >
                      <Sparkles
                        size={15}
                        strokeWidth={2}
                        style={{ color: "var(--cv-accent)" }}
                      />
                    </div>
                    <div>
                      <SectionLabel text="Recommended next steps" />
                    </div>
                  </div>

                  <motion.ol
                    variants={stagger}
                    initial="hidden"
                    animate="visible"
                    className="flex flex-col"
                  >
                    {skillGap.recommended_next_steps.map((step, i) => (
                      <TimelineStep
                        key={i}
                        index={i}
                        text={step}
                        total={skillGap.recommended_next_steps.length}
                      />
                    ))}
                  </motion.ol>
                </motion.div>
              )}

              {/* ── CTA card ────────────────────────────────────────────── */}
              <motion.div
                variants={item}
                className="rounded-[var(--cv-radius-main)] bg-white p-10 text-center"
                style={{ boxShadow: "var(--cv-shadow-main)" }}
              >
                <div
                  className="mx-auto mb-5 flex size-16 items-center justify-center rounded-full"
                  style={{ background: "var(--cv-accent-muted)" }}
                  aria-hidden
                >
                  <Map
                    size={28}
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
                  Turn gaps into a game plan
                </h2>

                <p
                  className="mx-auto mt-3 max-w-md"
                  style={{
                    fontFamily: "var(--cv-font-sans)",
                    fontSize: "var(--cv-text-small)",
                    color: "#6B7280",
                    lineHeight: 1.7,
                  }}
                >
                  Your personalised 3-Month Learning Roadmap will turn every
                  missing skill above into a concrete month-by-month plan —
                  with topics, projects, resources, and milestones tailored
                  to{" "}
                  <span style={{ fontWeight: 600, color: "#374151" }}>
                    {match ? match.role_title : "your chosen career"}
                  </span>
                  .
                </p>

                {roadmapError && (
                  <div className="mx-auto mt-5 flex max-w-sm items-start gap-2 rounded-xl bg-red-50 p-4 text-left">
                    <AlertCircle
                      size={16}
                      style={{ color: "#EF4444", flexShrink: 0, marginTop: 1 }}
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

                <div className="mt-7 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
                  <Button
                    type="button"
                    disabled={roadmapPhase === "loading"}
                    onClick={handleViewRoadmap}
                    className="gap-2 px-6"
                    style={{
                      background: "var(--cv-accent)",
                      color: "#fff",
                      fontFamily: "var(--cv-font-sans)",
                      fontWeight: 600,
                      fontSize: "var(--cv-text-small)",
                    }}
                  >
                    {roadmapPhase === "loading" ? (
                      <>
                        <Loader2 size={16} className="animate-spin" aria-hidden />
                        Building your roadmap…
                      </>
                    ) : (
                      <>
                        <Map size={16} strokeWidth={2} aria-hidden />
                        View My Learning Roadmap
                        <ArrowRight size={16} strokeWidth={2} aria-hidden />
                      </>
                    )}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => navigate("/dashboard")}
                    disabled={roadmapPhase === "loading"}
                    style={{
                      fontFamily: "var(--cv-font-sans)",
                      fontWeight: 500,
                    }}
                  >
                    Back to Dashboard
                  </Button>
                </div>

                {roadmapPhase === "loading" && (
                  <p
                    className="mt-3"
                    style={{
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "var(--cv-text-caption)",
                      color: "#9CA3AF",
                    }}
                  >
                    This usually takes 30–60 seconds — hang tight.
                  </p>
                )}
              </motion.div>

            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
