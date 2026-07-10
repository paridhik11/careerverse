/**
 * ResumeReportPage — displays the AI-generated resume review report.
 *
 * Data flow:
 *   UploadResumePage navigates here with the report in location.state
 *   (shape: ResumeReportState). If the user refreshes or navigates directly,
 *   location.state is null and we show a "missing" state with a link back.
 *
 * Animation strategy:
 *   A single Framer Motion container variant with `staggerChildren` drives the
 *   cascade. Every direct child section just needs `variants={sectionVariants}`
 *   — no explicit delays needed. This produces a clean, sequential reveal:
 *   Header → Summary → Strengths+Weaknesses → ATS → Suggestions → Directions.
 *
 * Sections:
 *   1. Header — filename, ScoreRings, review date
 *   2. Executive Summary
 *   3. Strengths (sage) + Areas for Improvement (amber) — side-by-side desktop
 *   4. ATS Analysis — sky card with accordion
 *   5. AI Suggestions — numbered list (clean, no badge circles)
 *   6. Suggested Career Directions — indigo chips
 */

import { useLocation, useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import {
  AlertTriangle,
  ArrowLeft,
  BarChart2,
  CheckCircle2,
  FileText,
  Lightbulb,
  Sparkles,
  Target,
} from "lucide-react"

import { ScoreRing } from "@/components/ScoreRing"
import {
  AccordionRoot,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion"
import { Button } from "@/components/ui/button"
import type { ResumeReportState } from "@/types"

/* ─── Animation variants ────────────────────────────────────────────────── */

const EASE = [0.22, 1, 0.36, 1] as const

/**
 * Container: triggers a stagger cascade on all direct `motion` children that
 * carry `variants`. No animation on the container itself — it's transparent.
 */
const containerVariants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.09,
      delayChildren: 0.05,
    },
  },
}

/**
 * Each section slides up 14px and fades in. Duration 400ms with expo-out
 * matches the design system's motion spec.
 */
const sectionVariants = {
  hidden: { opacity: 0, y: 14 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: EASE },
  },
}

/* ─── Section components ────────────────────────────────────────────────── */

interface SectionProps {
  children: React.ReactNode
  className?: string
  style?: React.CSSProperties
}

/** Every report section — picks up stagger timing from the parent container. */
function Section({ children, className = "", style }: SectionProps) {
  return (
    <motion.section
      variants={sectionVariants}
      className={`rounded-[var(--cv-radius-card)] p-6 ${className}`}
      style={{ boxShadow: "var(--cv-shadow-card)", ...style }}
    >
      {children}
    </motion.section>
  )
}

function SectionTitle({ icon: Icon, label }: { icon: React.ElementType; label: string }) {
  return (
    <div className="mb-4 flex items-center gap-2">
      <Icon size={18} strokeWidth={1.8} style={{ color: "currentColor" }} aria-hidden />
      <h2
        style={{
          fontFamily: "var(--cv-font-serif)",
          fontSize: "var(--cv-text-h3)",
          fontWeight: 500,
          color: "#111827",
        }}
      >
        {label}
      </h2>
    </div>
  )
}

/* ─── Helpers ───────────────────────────────────────────────────────────── */

function formatDate(isoString: string): string {
  try {
    return new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    }).format(new Date(isoString))
  } catch {
    return isoString
  }
}

/* ─── Missing-state ─────────────────────────────────────────────────────── */

function MissingReportState() {
  const navigate = useNavigate()
  return (
    <div
      className="flex min-h-screen w-full items-center justify-center px-4 py-10"
      style={{ background: "var(--cv-bg)" }}
    >
      <motion.div
        variants={sectionVariants}
        initial="hidden"
        animate="visible"
        className="w-full max-w-md rounded-[var(--cv-radius-main)] bg-white p-8 text-center"
        style={{ boxShadow: "var(--cv-shadow-main)" }}
      >
        <div
          className="mx-auto mb-4 flex size-14 items-center justify-center rounded-full"
          style={{ background: "var(--cv-card-amber-icon)" }}
          aria-hidden
        >
          <FileText size={24} strokeWidth={1.6} color="#111827" />
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
          Report not found
        </h1>
        <p
          className="mt-3 text-gray-500"
          style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", lineHeight: 1.6 }}
        >
          It looks like you navigated here directly or refreshed the page.
          Reports are generated on the fly — please upload your resume again to
          receive a fresh review.
        </p>
        <Button
          type="button"
          className="mt-6 w-full text-white hover:opacity-90"
          style={{ background: "var(--cv-accent)" }}
          onClick={() => navigate("/resume/upload")}
        >
          Upload Resume
        </Button>
      </motion.div>
    </div>
  )
}

/* ─── Main page ─────────────────────────────────────────────────────────── */

export function ResumeReportPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as ResumeReportState | null

  if (!state?.report) {
    return <MissingReportState />
  }

  const { report, fileName, reviewedAt } = state
  const {
    overall_score,
    ats_score,
    summary,
    strengths,
    weaknesses,
    ats_issues,
    suggestions,
    recommended_roles,
  } = report

  return (
    <div
      className="min-h-screen w-full px-4 py-8 md:px-6"
      style={{ background: "var(--cv-bg)" }}
    >
      {/*
        Container drives the stagger. `initial="hidden"` + `animate="visible"`
        here propagates automatically to every child that carries `variants`.
      */}
      <motion.div
        className="mx-auto max-w-3xl space-y-5"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >

        {/* ── Back navigation ─────────────────────────────────────────── */}
        <motion.div variants={sectionVariants}>
          <button
            type="button"
            onClick={() => navigate("/resume/upload")}
            className="flex items-center gap-1.5 rounded-full px-3 py-1.5 transition-colors duration-150 hover:bg-black/5"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              fontWeight: 500,
              color: "#6B7280",
            }}
          >
            <ArrowLeft size={15} strokeWidth={2} aria-hidden />
            Upload a different resume
          </button>
        </motion.div>

        {/* ── 1. Header card ───────────────────────────────────────────── */}
        <Section
          className="bg-white"
          style={{ borderRadius: "var(--cv-radius-main)", boxShadow: "var(--cv-shadow-main)" }}
        >
          {/* Title row + date */}
          <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="mb-1 flex items-center gap-2">
                <div
                  className="flex size-8 items-center justify-center rounded-full"
                  style={{ background: "var(--cv-card-amber-icon)" }}
                  aria-hidden
                >
                  <FileText size={16} strokeWidth={1.8} color="#111827" />
                </div>
                <span
                  style={{
                    fontFamily: "var(--cv-font-sans)",
                    fontSize: "var(--cv-text-caption)",
                    fontWeight: 600,
                    color: "#9CA3AF",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  Resume Review
                </span>
              </div>
              <h1
                className="mt-1 text-gray-900"
                style={{
                  fontFamily: "var(--cv-font-serif)",
                  fontSize: "var(--cv-text-h2)",
                  fontWeight: 400,
                  lineHeight: 1.2,
                }}
              >
                {fileName}
              </h1>
            </div>

            <span
              className="rounded-full px-3 py-1"
              style={{
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-caption)",
                fontWeight: 500,
                background: "#F3F4F6",
                color: "#6B7280",
                whiteSpace: "nowrap",
              }}
            >
              {formatDate(reviewedAt)}
            </span>
          </div>

          {/* Score rings */}
          <div
            className="flex flex-wrap items-center justify-center gap-10 rounded-[var(--cv-radius-card)] px-6 py-6"
            style={{ background: "var(--cv-bg)" }}
          >
            <ScoreRing score={overall_score} label="Overall" color="#6B7FFF" size={108} strokeWidth={9} />
            <div className="hidden h-16 w-px sm:block" style={{ background: "#E5E7EB" }} aria-hidden />
            <ScoreRing score={ats_score} label="ATS" color="#F59E0B" trackColor="#FEF3C7" size={108} strokeWidth={9} />
          </div>

          {/* Legend */}
          <div className="mt-4 flex flex-wrap justify-center gap-4">
            {[
              { color: "#6B7FFF", label: "Overall quality score" },
              { color: "#F59E0B", label: "ATS compatibility score" },
            ].map(({ color, label }) => (
              <div key={label} className="flex items-center gap-1.5">
                <span className="inline-block size-2.5 rounded-full" style={{ background: color }} aria-hidden />
                <span style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-caption)", color: "#9CA3AF" }}>
                  {label}
                </span>
              </div>
            ))}
          </div>
        </Section>

        {/* ── 2. Executive Summary ──────────────────────────────────────── */}
        <Section style={{ background: "var(--cv-card-amber)" }}>
          <SectionTitle icon={Sparkles} label="Executive Summary" />
          <p
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-body)",
              color: "#374151",
              lineHeight: 1.7,
            }}
          >
            {summary}
          </p>
        </Section>

        {/* ── 3 & 4. Strengths + Weaknesses — side-by-side on md+ ─────── */}
        {/*
          The grid wrapper itself is a motion element so it participates in the
          stagger. Both columns inside are plain (non-motion) Sections that
          inherit the grid's animation via the wrapper.
        */}
        <motion.div variants={sectionVariants} className="grid grid-cols-1 gap-5 md:grid-cols-2">
          {/* Strengths */}
          <div
            className="rounded-[var(--cv-radius-card)] p-6"
            style={{ background: "var(--cv-card-sage)", boxShadow: "var(--cv-shadow-card)" }}
          >
            <SectionTitle icon={CheckCircle2} label="Strengths" />
            <ul className="space-y-3">
              {strengths.map((item, i) => (
                <li key={i} className="flex items-start gap-2.5">
                  <CheckCircle2
                    size={16}
                    strokeWidth={2}
                    className="mt-0.5 shrink-0"
                    style={{ color: "#166534" }}
                    aria-hidden
                  />
                  <span
                    style={{
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "var(--cv-text-small)",
                      color: "#1F2937",
                      lineHeight: 1.5,
                    }}
                  >
                    {item}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          {/* Areas for Improvement */}
          <div
            className="rounded-[var(--cv-radius-card)] p-6"
            style={{ background: "var(--cv-card-amber)", boxShadow: "var(--cv-shadow-card)" }}
          >
            <SectionTitle icon={AlertTriangle} label="Areas for Improvement" />
            <ul className="space-y-3">
              {weaknesses.map((item, i) => (
                <li key={i} className="flex items-start gap-2.5">
                  <AlertTriangle
                    size={16}
                    strokeWidth={2}
                    className="mt-0.5 shrink-0"
                    style={{ color: "#D97706" }}
                    aria-hidden
                  />
                  <span
                    style={{
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "var(--cv-text-small)",
                      color: "#1F2937",
                      lineHeight: 1.5,
                    }}
                  >
                    {item}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </motion.div>

        {/* ── 5. ATS Analysis ──────────────────────────────────────────── */}
        <Section style={{ background: "var(--cv-card-sky)" }}>
          <SectionTitle icon={BarChart2} label="ATS Analysis" />
          {ats_issues.length === 0 ? (
            <div className="flex items-center gap-2 rounded-xl bg-white/50 px-4 py-3">
              <CheckCircle2 size={16} strokeWidth={2} style={{ color: "#166534" }} aria-hidden />
              <span
                style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "#374151" }}
              >
                No ATS issues detected — your resume is well-formatted for applicant tracking systems.
              </span>
            </div>
          ) : (
            <div className="overflow-hidden rounded-xl bg-white/60">
              <AccordionRoot type="single" collapsible>
                {ats_issues.map((issue, i) => (
                  <AccordionItem key={i} value={`ats-${i}`} className="px-4">
                    <AccordionTrigger>
                      <span className="flex items-center gap-2">
                        <span
                          className="flex size-5 shrink-0 items-center justify-center rounded-full text-xs font-bold"
                          style={{
                            background: "var(--cv-card-sky-icon)",
                            color: "#075985",
                            fontFamily: "var(--cv-font-sans)",
                          }}
                        >
                          {i + 1}
                        </span>
                        {issue.length > 80 ? issue.slice(0, 80) + "…" : issue}
                      </span>
                    </AccordionTrigger>
                    <AccordionContent>{issue}</AccordionContent>
                  </AccordionItem>
                ))}
              </AccordionRoot>
            </div>
          )}
        </Section>

        {/* ── 6. AI Suggestions — clean numbered list ───────────────────── */}
        {suggestions.length > 0 && (
          <Section style={{ background: "var(--cv-card-lavender)" }}>
            <SectionTitle icon={Lightbulb} label="AI Suggestions" />
            <ol className="divide-y divide-black/[0.06]">
              {suggestions.map((suggestion, i) => (
                <li key={i} className="flex gap-5 py-4 first:pt-0 last:pb-0">
                  {/* Number — Fraunces serif, accent color, large enough to anchor the line */}
                  <span
                    className="shrink-0"
                    style={{
                      fontFamily: "var(--cv-font-serif)",
                      fontSize: "var(--cv-text-h3)",
                      fontWeight: 500,
                      color: "var(--cv-accent)",
                      lineHeight: 1.3,
                      minWidth: "1.5rem",
                    }}
                  >
                    {i + 1}.
                  </span>
                  <p
                    style={{
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "var(--cv-text-small)",
                      color: "#1F2937",
                      lineHeight: 1.65,
                    }}
                  >
                    {suggestion}
                  </p>
                </li>
              ))}
            </ol>
          </Section>
        )}

        {/* ── 7. Suggested Career Directions ───────────────────────────── */}
        {recommended_roles.length > 0 && (
          <Section className="bg-white">
            <SectionTitle icon={Target} label="Suggested Career Directions" />
            <p
              className="mb-4 text-gray-400"
              style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", lineHeight: 1.5 }}
            >
              Preliminary directions based on your resume only — not the RAG-powered career recommendations.
            </p>
            <div className="flex flex-wrap gap-2">
              {recommended_roles.map((role, i) => (
                <span
                  key={i}
                  className="inline-flex items-center rounded-full px-4 py-1.5"
                  style={{
                    background: "var(--cv-accent-muted)",
                    color: "#4A5FD4",
                    fontFamily: "var(--cv-font-sans)",
                    fontSize: "var(--cv-text-small)",
                    fontWeight: 600,
                  }}
                >
                  {role}
                </span>
              ))}
            </div>
          </Section>
        )}

        {/* ── Footer CTA ────────────────────────────────────────────────── */}
        <motion.div variants={sectionVariants} className="pb-4 text-center">
          <p
            className="mb-3 text-gray-400"
            style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)" }}
          >
            Ready to find your best-fit career?
          </p>
          <Button
            type="button"
            className="text-white hover:opacity-90"
            style={{ background: "var(--cv-accent)" }}
            onClick={() => navigate("/resume/upload")}
          >
            Analyze another resume
          </Button>
        </motion.div>

      </motion.div>
    </div>
  )
}
