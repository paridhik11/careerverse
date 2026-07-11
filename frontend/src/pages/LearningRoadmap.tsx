/**
 * LearningRoadmapPage — displays the AI-generated 3-Month Learning Roadmap.
 *
 * Receives the roadmap record + chosen career via location.state from
 * SkillGapPage (the page that triggers roadmap generation).
 *
 * Layout: three month cards stacked vertically, each containing:
 *   - A colored header (Month number + focus)
 *   - Topics
 *   - Projects
 *   - Resources
 *   - Milestones
 *
 * Design follows the CareerVerse Design System:
 *   - Warm off-white canvas (--cv-bg)
 *   - Cards with pastel backgrounds and generous border-radius
 *   - Fraunces for headings, Manrope for body
 *   - Framer Motion entrance animation with stagger
 */

import { useLocation, useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import {
  BookOpen,
  CheckCircle2,
  ChevronRight,
  FolderOpen,
  Map,
  Target,
  Trophy,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import type { JobMatch, LearningRoadmapRecord, MonthPlan } from "@/types"

// ---------------------------------------------------------------------------
// Animation config (matching the CareerVerse design system)
// ---------------------------------------------------------------------------

const EASE = [0.22, 1, 0.36, 1] as const

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.1, delayChildren: 0.05 },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 14 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: EASE },
  },
}

// ---------------------------------------------------------------------------
// Month card palette — one per month, following the design system's
// "one accent color per feature" principle.
// ---------------------------------------------------------------------------

const MONTH_PALETTES = [
  {
    label: "Month 1",
    subtitle: "Foundations",
    cardBg: "var(--cv-card-amber)",
    iconBg: "var(--cv-card-amber-icon)",
    badgeBg: "#FDE68A",
    badgeText: "#92400E",
    accent: "#B45309",
  },
  {
    label: "Month 2",
    subtitle: "Intermediate Competency",
    cardBg: "var(--cv-card-sage)",
    iconBg: "var(--cv-card-sage-icon)",
    badgeBg: "#BBF7D0",
    badgeText: "#14532D",
    accent: "#15803D",
  },
  {
    label: "Month 3",
    subtitle: "Job Readiness",
    cardBg: "var(--cv-card-lavender)",
    iconBg: "var(--cv-card-lavender-icon)",
    badgeBg: "#E9D5FF",
    badgeText: "#581C87",
    accent: "#7C3AED",
  },
] as const

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SectionHeading({
  icon,
  label,
  accent,
}: {
  icon: React.ReactNode
  label: string
  accent: string
}) {
  return (
    <div className="flex items-center gap-2 mb-2">
      <span style={{ color: accent }}>{icon}</span>
      <span
        style={{
          fontFamily: "var(--cv-font-sans)",
          fontSize: "var(--cv-text-caption)",
          fontWeight: 700,
          color: accent,
          textTransform: "uppercase",
          letterSpacing: "0.06em",
        }}
      >
        {label}
      </span>
    </div>
  )
}

function BulletList({ items, accent }: { items: string[]; accent: string }) {
  return (
    <ul className="flex flex-col gap-2">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2.5">
          <ChevronRight
            size={14}
            strokeWidth={2}
            style={{ color: accent, flexShrink: 0, marginTop: 3 }}
            aria-hidden
          />
          <span
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              color: "#374151",
              lineHeight: 1.6,
            }}
          >
            {item}
          </span>
        </li>
      ))}
    </ul>
  )
}

interface MonthCardProps {
  month: MonthPlan
  palette: (typeof MONTH_PALETTES)[number]
}

function MonthCard({ month, palette }: MonthCardProps) {
  const { cardBg, iconBg, badgeBg, badgeText, accent, label, subtitle } = palette

  return (
    <motion.div
      variants={itemVariants}
      className="rounded-[var(--cv-radius-card)] p-6"
      style={{
        background: cardBg,
        boxShadow: "var(--cv-shadow-card)",
      }}
    >
      {/* Month header */}
      <div className="flex items-center gap-4 mb-5">
        <div
          className="flex size-12 items-center justify-center rounded-full shrink-0"
          style={{ background: iconBg }}
          aria-hidden
        >
          <Map size={22} strokeWidth={1.6} color="#111827" />
        </div>
        <div>
          <div className="flex items-center gap-2 mb-0.5">
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
            <span
              className="rounded-full px-2.5 py-0.5"
              style={{
                background: badgeBg,
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-caption)",
                fontWeight: 600,
                color: badgeText,
              }}
            >
              {subtitle}
            </span>
          </div>
          <p
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              color: "#4B5563",
              fontStyle: "italic",
            }}
          >
            {month.focus}
          </p>
        </div>
      </div>

      {/* Content grid */}
      <div className="grid gap-5 sm:grid-cols-2">
        {/* Topics */}
        <div
          className="rounded-[var(--cv-radius-card)] bg-white/60 p-4"
          style={{ backdropFilter: "blur(4px)" }}
        >
          <SectionHeading
            icon={<BookOpen size={14} strokeWidth={2} />}
            label="Topics to Study"
            accent={accent}
          />
          <BulletList items={month.topics} accent={accent} />
        </div>

        {/* Projects */}
        <div
          className="rounded-[var(--cv-radius-card)] bg-white/60 p-4"
          style={{ backdropFilter: "blur(4px)" }}
        >
          <SectionHeading
            icon={<FolderOpen size={14} strokeWidth={2} />}
            label="Projects to Build"
            accent={accent}
          />
          <BulletList items={month.projects} accent={accent} />
        </div>

        {/* Resources */}
        <div
          className="rounded-[var(--cv-radius-card)] bg-white/60 p-4"
          style={{ backdropFilter: "blur(4px)" }}
        >
          <SectionHeading
            icon={<Target size={14} strokeWidth={2} />}
            label="Resources"
            accent={accent}
          />
          <BulletList items={month.resources} accent={accent} />
        </div>

        {/* Milestones */}
        <div
          className="rounded-[var(--cv-radius-card)] bg-white/60 p-4"
          style={{ backdropFilter: "blur(4px)" }}
        >
          <SectionHeading
            icon={<Trophy size={14} strokeWidth={2} />}
            label="Milestones"
            accent={accent}
          />
          <BulletList items={month.milestones} accent={accent} />
        </div>
      </div>
    </motion.div>
  )
}

// ---------------------------------------------------------------------------
// State shape passed via React Router location.state
// ---------------------------------------------------------------------------

interface LearningRoadmapPageState {
  roadmap?: LearningRoadmapRecord
  match?: JobMatch
  resumeId?: number
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function LearningRoadmapPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as LearningRoadmapPageState | null
  const roadmap = state?.roadmap
  const match = state?.match

  const months = roadmap
    ? [roadmap.roadmap.month_1, roadmap.roadmap.month_2, roadmap.roadmap.month_3]
    : []

  return (
    <div
      className="min-h-screen w-full px-4 py-12 md:px-6"
      style={{ background: "var(--cv-bg)" }}
    >
      <motion.div
        className="mx-auto max-w-3xl"
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
                Your target career
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
        <motion.div variants={itemVariants} className="mb-8 text-center">
          <div
            className="mx-auto mb-4 flex size-16 items-center justify-center rounded-full"
            style={{ background: "var(--cv-accent-muted)" }}
            aria-hidden
          >
            <Map size={28} strokeWidth={1.6} style={{ color: "var(--cv-accent)" }} />
          </div>
          <h1
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize: "var(--cv-text-h1)",
              fontWeight: 400,
              color: "#111827",
              lineHeight: 1.15,
            }}
          >
            Your 3-Month Learning Roadmap
          </h1>
          <p
            className="mx-auto mt-3 max-w-lg text-gray-500"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-body)",
              lineHeight: 1.7,
            }}
          >
            {match
              ? `A personalised plan to bridge your skill gap and become job-ready for ${match.role_title} in 90 days.`
              : "A personalised 90-day plan grounded in your Skill Gap Analysis."}
          </p>
        </motion.div>

        {/* Three month cards */}
        {months.length > 0 ? (
          <div className="flex flex-col gap-5">
            {months.map((month, i) => (
              <MonthCard key={i} month={month} palette={MONTH_PALETTES[i]} />
            ))}
          </div>
        ) : (
          /* Fallback: no roadmap in state — shouldn't happen in normal flow */
          <motion.div
            variants={itemVariants}
            className="rounded-[var(--cv-radius-main)] bg-white p-10 text-center"
            style={{ boxShadow: "var(--cv-shadow-main)" }}
          >
            <p
              style={{
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-body)",
                color: "#6B7280",
              }}
            >
              No roadmap data found. Please complete the Skill Gap Analysis first.
            </p>
          </motion.div>
        )}

        {/* Navigation footer */}
        <motion.div
          variants={itemVariants}
          className="mt-8 flex justify-center gap-3"
        >
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate("/dashboard")}
          >
            Go to Dashboard
          </Button>
        </motion.div>
      </motion.div>
    </div>
  )
}
