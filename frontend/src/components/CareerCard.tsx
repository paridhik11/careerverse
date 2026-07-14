/**
 * CareerCard — Top-3 career match on a white floating Emergent-style card.
 * Information only — action CTAs live on Virtual Experience small cards.
 */

import { motion } from "framer-motion"
import { TrendingUp } from "lucide-react"

import type { JobMatch } from "@/types"

const CONFIDENCE_CONFIG = {
  High: { text: "var(--cv-accent)", dot: "var(--cv-accent)" },
  Medium: { text: "var(--cv-ink-muted)", dot: "#9CA3AF" },
  Low: { text: "var(--cv-ink-muted)", dot: "#9CA3AF" },
} as const

const EASE = [0.22, 1, 0.36, 1] as const

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

interface CareerCardProps {
  match: JobMatch
  /** Display rank after client-side dedupe/re-rank (defaults to API rank). */
  displayRank?: 1 | 2 | 3
}

export function CareerCard({
  match,
  displayRank,
}: CareerCardProps) {
  const confidence = CONFIDENCE_CONFIG[match.confidence_score]
  const skillsToShow = match.missing_skills.slice(0, 5)
  const rank = displayRank ?? match.rank

  return (
    <motion.div
      custom={rank}
      variants={cardVariants}
      whileHover={{
        y: -3,
        boxShadow: "var(--cv-shadow-main)",
        transition: { duration: 0.2 },
      }}
      className="cv-card p-6"
    >
      <div className="mb-5 flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="cv-icon-circle size-12" aria-hidden>
            <span
              style={{
                fontFamily: "var(--cv-font-serif)",
                fontSize: "var(--cv-text-h3)",
                fontWeight: 600,
                color: "var(--cv-accent)",
                lineHeight: 1,
              }}
            >
              {rank}
            </span>
          </div>
          <div>
            <span className="cv-badge mb-2">Rank {rank}</span>
            <h2
              style={{
                fontFamily: "var(--cv-font-serif)",
                fontSize: "var(--cv-text-h2)",
                fontWeight: 400,
                color: "var(--cv-ink)",
                lineHeight: 1.15,
              }}
            >
              {match.role_title}
            </h2>
            <span
              className="mt-1.5 inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5"
              style={{
                background: "var(--cv-accent-muted)",
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

        <div className="shrink-0 text-right">
          <div className="flex items-baseline gap-0.5" style={{ color: "var(--cv-accent)" }}>
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
            <span style={{ fontFamily: "var(--cv-font-serif)", fontSize: "var(--cv-text-h3)" }}>%</span>
          </div>
          <p
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-caption)",
              color: "var(--cv-ink-muted)",
              marginTop: "2px",
            }}
          >
            match
          </p>
        </div>
      </div>

      <div
        className="mb-4 rounded-[1.25rem] p-4"
        style={{ background: "var(--cv-bg)", border: "1px solid var(--cv-border)" }}
      >
        <div className="mb-1.5 flex items-center gap-1.5">
          <TrendingUp size={13} strokeWidth={2} style={{ color: "var(--cv-ink-muted)" }} aria-hidden />
          <span
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-caption)",
              fontWeight: 700,
              color: "var(--cv-ink-muted)",
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
            color: "var(--cv-ink-muted)",
            lineHeight: 1.65,
          }}
        >
          {match.career_overview}
        </p>
      </div>

      <div className={skillsToShow.length > 0 ? "mb-4" : undefined}>
        <p
          className="mb-1.5"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-caption)",
            fontWeight: 700,
            color: "var(--cv-ink-muted)",
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
            color: "var(--cv-ink-muted)",
            lineHeight: 1.65,
          }}
        >
          {match.reasoning}
        </p>
      </div>

      {skillsToShow.length > 0 && (
        <div>
          <p
            className="mb-2"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-caption)",
              fontWeight: 700,
              color: "var(--cv-ink-muted)",
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
                  background: "var(--cv-bg)",
                  border: "1px solid var(--cv-border)",
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-caption)",
                  fontWeight: 500,
                  color: "var(--cv-ink)",
                }}
              >
                {skill}
              </span>
            ))}
            {match.missing_skills.length > 5 && (
              <span className="cv-badge">+{match.missing_skills.length - 5} more</span>
            )}
          </div>
        </div>
      )}
    </motion.div>
  )
}
