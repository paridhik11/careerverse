/**
 * CareerCard — premium card displaying one Top-3 career match.
 *
 * Receives a `JobMatch` and an optional `onExplore` callback.
 * Animates into view via Framer Motion stagger (parent must supply variants).
 */

import { motion } from "framer-motion"
import { ArrowRight, Sparkles, TrendingUp } from "lucide-react"

import { Button } from "@/components/ui/button"
import type { JobMatch } from "@/types"

/* ─── Confidence badge styles ────────────────────────────────────────────── */

const CONFIDENCE_CONFIG = {
  High: {
    bg: "var(--cv-card-sage)",
    text: "#166534",
    dot: "#22C55E",
  },
  Medium: {
    bg: "#FEF3C7",
    text: "#92400E",
    dot: "#F59E0B",
  },
  Low: {
    bg: "#F3F4F6",
    text: "#6B7280",
    dot: "#9CA3AF",
  },
} as const

/* ─── Rank accent colors (one per card position) ────────────────────────── */

const RANK_PALETTE = [
  { card: "var(--cv-card-sage)", icon: "var(--cv-card-sage-icon)" },
  { card: "var(--cv-card-sky)", icon: "var(--cv-card-sky-icon)" },
  { card: "var(--cv-card-lavender)", icon: "var(--cv-card-lavender-icon)" },
] as const

const EASE = [0.22, 1, 0.36, 1] as const

/* ─── Framer Motion variants — used by parent stagger container ──────────── */

export const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (rank: number) => ({
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      delay: (rank - 1) * 0.1,
      ease: EASE,
    },
  }),
}

/* ─── Props ─────────────────────────────────────────────────────────────── */

interface CareerCardProps {
  match: JobMatch
  onExplore: (match: JobMatch) => void
  isExploring?: boolean
}

/* ─── Component ─────────────────────────────────────────────────────────── */

export function CareerCard({ match, onExplore, isExploring = false }: CareerCardProps) {
  const palette = RANK_PALETTE[(match.rank - 1) % RANK_PALETTE.length]
  const confidence = CONFIDENCE_CONFIG[match.confidence_score]
  const skillsToShow = match.missing_skills.slice(0, 5)

  return (
    <motion.div
      custom={match.rank}
      variants={cardVariants}
      whileHover={{
        y: -3,
        boxShadow: "0 4px 16px 0 rgb(0 0 0 / 0.10)",
        transition: { duration: 0.2 },
      }}
      className="rounded-[var(--cv-radius-card)] p-6"
      style={{
        background: palette.card,
        boxShadow: "var(--cv-shadow-card)",
      }}
    >
      {/* ── Header row ── */}
      <div className="mb-5 flex items-start justify-between gap-4">
        {/* Rank + title */}
        <div className="flex items-start gap-4">
          <div
            className="flex size-12 shrink-0 items-center justify-center rounded-full"
            style={{ background: palette.icon }}
            aria-hidden
          >
            <span
              style={{
                fontFamily: "var(--cv-font-serif)",
                fontSize: "var(--cv-text-h3)",
                fontWeight: 600,
                color: "#111827",
                lineHeight: 1,
              }}
            >
              {match.rank}
            </span>
          </div>
          <div>
            <h2
              style={{
                fontFamily: "var(--cv-font-serif)",
                fontSize: "var(--cv-text-h2)",
                fontWeight: 400,
                color: "#111827",
                lineHeight: 1.15,
              }}
            >
              {match.role_title}
            </h2>
            {/* Confidence badge */}
            <span
              className="mt-1.5 inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5"
              style={{
                background: confidence.bg,
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-caption)",
                fontWeight: 600,
                color: confidence.text,
              }}
            >
              <span
                className="inline-block size-1.5 rounded-full"
                style={{ background: confidence.dot }}
                aria-hidden
              />
              {match.confidence_score} confidence
            </span>
          </div>
        </div>

        {/* Match percentage */}
        <div className="shrink-0 text-right">
          <div
            className="flex items-baseline gap-0.5"
            style={{ color: "var(--cv-accent)" }}
          >
            <span
              style={{
                fontFamily: "var(--cv-font-serif)",
                fontSize: "2.5rem",
                fontWeight: 300,
                lineHeight: 1,
              }}
            >
              {match.match_percent}
            </span>
            <span
              style={{
                fontFamily: "var(--cv-font-serif)",
                fontSize: "var(--cv-text-h3)",
                fontWeight: 400,
              }}
            >
              %
            </span>
          </div>
          <p
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-caption)",
              color: "#9CA3AF",
              marginTop: "2px",
            }}
          >
            match
          </p>
        </div>
      </div>

      {/* ── Career overview ── */}
      <div className="mb-4 rounded-[var(--cv-radius-card)] bg-white/50 p-4">
        <div className="mb-1.5 flex items-center gap-1.5">
          <TrendingUp size={13} strokeWidth={2} style={{ color: "#6B7280" }} aria-hidden />
          <span
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-caption)",
              fontWeight: 700,
              color: "#6B7280",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}
          >
            Career Overview
          </span>
        </div>
        <p
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            color: "#374151",
            lineHeight: 1.65,
          }}
        >
          {match.career_overview}
        </p>
      </div>

      {/* ── Why it matches ── */}
      <div className="mb-4">
        <p
          className="mb-1.5"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-caption)",
            fontWeight: 700,
            color: "#6B7280",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
          }}
        >
          Why it matches
        </p>
        <p
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            color: "#374151",
            lineHeight: 1.65,
          }}
        >
          {match.reasoning}
        </p>
      </div>

      {/* ── Missing skills ── */}
      {skillsToShow.length > 0 && (
        <div className="mb-5">
          <p
            className="mb-2"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-caption)",
              fontWeight: 700,
              color: "#6B7280",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}
          >
            Skills to develop
          </p>
          <div className="flex flex-wrap gap-1.5">
            {skillsToShow.map((skill, i) => (
              <span
                key={i}
                className="rounded-full px-3 py-1"
                style={{
                  background: "rgba(255,255,255,0.7)",
                  border: "1px solid rgba(0,0,0,0.08)",
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-caption)",
                  fontWeight: 500,
                  color: "#374151",
                }}
              >
                {skill}
              </span>
            ))}
            {match.missing_skills.length > 5 && (
              <span
                className="rounded-full px-3 py-1"
                style={{
                  background: "rgba(107,127,255,0.12)",
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-caption)",
                  fontWeight: 500,
                  color: "var(--cv-accent)",
                }}
              >
                +{match.missing_skills.length - 5} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* ── CTA button ── */}
      <Button
        type="button"
        onClick={() => onExplore(match)}
        disabled={isExploring}
        className="w-full font-semibold text-white hover:opacity-90 disabled:opacity-60"
        style={{ background: "var(--cv-accent)" }}
      >
        {isExploring ? (
          <>
            <span className="relative flex size-3.5 shrink-0">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-white/60" />
              <span className="relative inline-flex size-3.5 rounded-full bg-white" />
            </span>
            Generating Experience…
          </>
        ) : (
          <>
            <Sparkles size={15} strokeWidth={2} aria-hidden />
            Explore Experience
            <ArrowRight size={15} strokeWidth={2} aria-hidden />
          </>
        )}
      </Button>
    </motion.div>
  )
}
