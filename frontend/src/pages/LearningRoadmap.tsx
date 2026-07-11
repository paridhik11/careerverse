/**
 * LearningRoadmapPage — AI-generated 3-Month Learning Roadmap.
 *
 * Data flow:
 *   1. Reads { roadmap, match, resumeId } from React Router location.state
 *      (SkillGapPage calls the API and passes the result here).
 *   2. If no roadmap is in state but a resumeId is available (from state or
 *      localStorage), calls POST /learning-roadmap/{resumeId} directly so the
 *      user can also arrive on this page from the Dashboard.
 *
 * Features
 * --------
 *  ✓ Skeleton loading          ✓ Error recovery with retry
 *  ✓ Three premium pastel cards (amber → sage → lavender)
 *  ✓ Interactive checklists for Topics, Projects, Resources, Milestones
 *  ✓ Per-section circular progress rings
 *  ✓ Overall card progress ring
 *  ✓ Horizontal step-progress bar
 *  ✓ Vertical timeline rail connecting cards
 *  ✓ Framer Motion entrance + stagger animations
 *  ✓ "Open Career Mentor" CTA  ✓  "Go to Dashboard" CTA
 *  ✓ Fully responsive (single-column mobile → 2-col sections on sm+)
 */

import { useEffect, useMemo, useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  AlertCircle,
  BookOpen,
  CheckCircle2,
  CheckSquare,
  FolderOpen,
  LayoutDashboard,
  Loader2,
  Map,
  RefreshCw,
  Square,
  Target,
  Trophy,
  Users,
} from "lucide-react"
import type { LucideProps } from "lucide-react"

import { Button } from "@/components/ui/button"
import { ApiError, RESUME_ID_STORAGE_KEY } from "@/services/api"
import { generateLearningRoadmap } from "@/services/learningRoadmap"
import type { JobMatch, LearningRoadmapRecord, MonthPlan } from "@/types"

// ─── Animation config (DESIGN_SYSTEM.md expo-out easing) ─────────────────────

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
  visible: { transition: { staggerChildren: 0.09, delayChildren: 0.05 } },
}

const cardItem = {
  hidden: { opacity: 0, y: 18 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.42, ease: EASE } },
}

const listItem = {
  hidden: { opacity: 0, x: -10 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.28, ease: EASE } },
}

const listStagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.055, delayChildren: 0 } },
}

// ─── Month palette (one accent per feature, per Design System) ────────────────

const PALETTES = [
  {
    label: "Month 1",
    subtitle: "Foundations",
    cardBg: "var(--cv-card-amber)",
    iconBg: "var(--cv-card-amber-icon)",
    badgeBg: "#FDE68A",
    badgeText: "#92400E",
    accent: "#B45309",
    checkColor: "#D97706",
    railColor: "#F6DC6D",
  },
  {
    label: "Month 2",
    subtitle: "Intermediate Competency",
    cardBg: "var(--cv-card-sage)",
    iconBg: "var(--cv-card-sage-icon)",
    badgeBg: "#BBF7D0",
    badgeText: "#14532D",
    accent: "#15803D",
    checkColor: "#16A34A",
    railColor: "#9DD4A8",
  },
  {
    label: "Month 3",
    subtitle: "Job Readiness",
    cardBg: "var(--cv-card-lavender)",
    iconBg: "var(--cv-card-lavender-icon)",
    badgeBg: "#E9D5FF",
    badgeText: "#581C87",
    accent: "#7C3AED",
    checkColor: "#8B5CF6",
    railColor: "#C5A8EF",
  },
] as const

// ─── Section definitions ──────────────────────────────────────────────────────

type SectionKey = "topics" | "projects" | "resources" | "milestones"

type IconComponent = React.ComponentType<LucideProps>

const SECTIONS: {
  key: SectionKey
  label: string
  Icon: IconComponent
  emptyMsg: string
}[] = [
  { key: "topics",     label: "Topics to Study",  Icon: BookOpen,   emptyMsg: "No topics listed." },
  { key: "projects",   label: "Projects to Build", Icon: FolderOpen, emptyMsg: "No projects listed." },
  { key: "resources",  label: "Resources",         Icon: Target,     emptyMsg: "No resources listed." },
  { key: "milestones", label: "Milestones",        Icon: Trophy,     emptyMsg: "No milestones listed." },
]

// ─── Interactive checklist state ──────────────────────────────────────────────

type MonthChecked = Record<SectionKey, Set<number>>
type CheckedState = Record<number, MonthChecked>

function makeEmptyMonth(): MonthChecked {
  return { topics: new Set(), projects: new Set(), resources: new Set(), milestones: new Set() }
}

function buildChecked(months: MonthPlan[]): CheckedState {
  const s: CheckedState = {}
  months.forEach((_, i) => { s[i] = makeEmptyMonth() })
  return s
}

// ─── Sub-component: mini circular progress ring ───────────────────────────────

function CircleRing({
  pct,
  accent,
  size,
  strokeWidth,
  fontSize,
}: {
  pct: number
  accent: string
  size: number
  strokeWidth: number
  fontSize: string
}) {
  const R = (size - strokeWidth * 2) / 2
  const C = 2 * Math.PI * R
  const center = size / 2

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        style={{ transform: "rotate(-90deg)" }}
        aria-hidden
      >
        <circle cx={center} cy={center} r={R} fill="none" stroke="#E5E7EB" strokeWidth={strokeWidth} />
        <motion.circle
          cx={center}
          cy={center}
          r={R}
          fill="none"
          stroke={accent}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={C}
          initial={{ strokeDashoffset: C }}
          animate={{ strokeDashoffset: C - (pct / 100) * C }}
          transition={{ duration: 1.1, ease: EASE, delay: 0.2 }}
        />
      </svg>
      <span
        className="absolute inset-0 flex items-center justify-center"
        style={{
          fontFamily: "var(--cv-font-sans)",
          fontSize,
          fontWeight: 700,
          color: accent,
        }}
      >
        {pct}%
      </span>
    </div>
  )
}

// ─── Sub-component: checklist item ────────────────────────────────────────────

function ChecklistItem({
  text,
  checked,
  onToggle,
  accent,
  checkColor,
}: {
  text: string
  checked: boolean
  onToggle: () => void
  accent: string
  checkColor: string
}) {
  return (
    <motion.li variants={listItem} className="flex items-start gap-2.5">
      <button
        type="button"
        onClick={onToggle}
        className="mt-0.5 shrink-0 transition-transform active:scale-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 rounded"
        style={{ lineHeight: 0, focusRingColor: accent } as React.CSSProperties}
        aria-label={checked ? "Mark incomplete" : "Mark complete"}
      >
        {checked ? (
          <CheckSquare size={16} strokeWidth={2} style={{ color: checkColor }} />
        ) : (
          <Square size={16} strokeWidth={1.8} style={{ color: "#D1D5DB" }} />
        )}
      </button>
      <span
        style={{
          fontFamily: "var(--cv-font-sans)",
          fontSize: "var(--cv-text-small)",
          color: checked ? "#9CA3AF" : "#374151",
          lineHeight: 1.6,
          textDecoration: checked ? "line-through" : "none",
          transition: "color 0.18s, text-decoration 0.18s",
        }}
      >
        {text}
      </span>
    </motion.li>
  )
}

// ─── Sub-component: section panel ────────────────────────────────────────────

function SectionPanel({
  label,
  Icon,
  items,
  checked,
  onToggle,
  accent,
  checkColor,
  emptyMsg,
}: {
  label: string
  Icon: IconComponent
  items: string[]
  checked: Set<number>
  onToggle: (i: number) => void
  accent: string
  checkColor: string
  emptyMsg: string
}) {
  const pct =
    items.length === 0 ? 0 : Math.round((checked.size / items.length) * 100)

  return (
    <div
      className="rounded-[var(--cv-radius-card)] bg-white/65 p-4 flex flex-col gap-3"
      style={{ backdropFilter: "blur(4px)" }}
    >
      {/* Header row: label + mini progress ring */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <Icon size={13} strokeWidth={2} style={{ color: accent }} aria-hidden />
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
        {items.length > 0 && (
          <CircleRing pct={pct} accent={accent} size={36} strokeWidth={3.5} fontSize="0.5rem" />
        )}
      </div>

      {/* Checklist */}
      {items.length === 0 ? (
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
        <motion.ul
          variants={listStagger}
          initial="hidden"
          animate="visible"
          className="flex flex-col gap-2"
        >
          {items.map((item, i) => (
            <ChecklistItem
              key={i}
              text={item}
              checked={checked.has(i)}
              onToggle={() => onToggle(i)}
              accent={accent}
              checkColor={checkColor}
            />
          ))}
        </motion.ul>
      )}
    </div>
  )
}

// ─── Sub-component: month card ────────────────────────────────────────────────

interface MonthCardProps {
  month: MonthPlan
  palette: (typeof PALETTES)[number]
  monthIdx: number
  checked: MonthChecked
  onToggle: (section: SectionKey, i: number) => void
  isLast: boolean
}

function MonthCard({ month, palette, monthIdx, checked, onToggle, isLast }: MonthCardProps) {
  const { cardBg, iconBg, badgeBg, badgeText, accent, checkColor, label, subtitle, railColor } =
    palette

  // Aggregate progress across all four sections
  const totalItems = SECTIONS.reduce((acc, s) => acc + (month[s.key]?.length ?? 0), 0)
  const totalChecked = SECTIONS.reduce((acc, s) => acc + checked[s.key].size, 0)
  const overallPct = totalItems === 0 ? 0 : Math.round((totalChecked / totalItems) * 100)

  return (
    <div className="relative flex gap-4 md:gap-6">
      {/* ── Timeline rail ──────────────────────────────────────────────── */}
      <div className="flex flex-col items-center shrink-0 pt-1">
        {/* Month number bubble */}
        <motion.div
          variants={cardItem}
          className="relative z-10 flex size-10 shrink-0 items-center justify-center rounded-full border-4 border-white shadow"
          style={{ background: iconBg }}
        >
          <span
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize: "1.0625rem",
              fontWeight: 500,
              color: "#111827",
              lineHeight: 1,
            }}
          >
            {monthIdx + 1}
          </span>
        </motion.div>

        {/* Connector line */}
        {!isLast && (
          <div
            className="flex-1 mt-1.5 rounded-full"
            style={{ width: 3, background: railColor, minHeight: 40 }}
            aria-hidden
          />
        )}
      </div>

      {/* ── Card ────────────────────────────────────────────────────────── */}
      <motion.div
        variants={cardItem}
        className="flex-1 rounded-[var(--cv-radius-card)] p-5 md:p-6 mb-8"
        style={{ background: cardBg, boxShadow: "var(--cv-shadow-card)" }}
      >
        {/* Card header: month label + focus + overall ring */}
        <div className="flex items-start justify-between gap-3 mb-5 flex-wrap">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
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
                className="rounded-full px-2.5 py-0.5 shrink-0"
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
                lineHeight: 1.5,
              }}
            >
              {month.focus}
            </p>
          </div>

          {/* Overall progress ring */}
          <div className="flex flex-col items-center gap-1 shrink-0">
            <CircleRing pct={overallPct} accent={accent} size={52} strokeWidth={5} fontSize="0.6rem" />
            <span
              style={{
                fontFamily: "var(--cv-font-sans)",
                fontSize: "0.6rem",
                fontWeight: 500,
                color: "#9CA3AF",
              }}
            >
              overall
            </span>
          </div>
        </div>

        {/* 2-column section grid */}
        <div className="grid gap-4 sm:grid-cols-2">
          {SECTIONS.map((s) => (
            <SectionPanel
              key={s.key}
              label={s.label}
              Icon={s.Icon}
              items={month[s.key] ?? []}
              checked={checked[s.key]}
              onToggle={(i) => onToggle(s.key, i)}
              accent={accent}
              checkColor={checkColor}
              emptyMsg={s.emptyMsg}
            />
          ))}
        </div>
      </motion.div>
    </div>
  )
}

// ─── Sub-component: horizontal step progress bar ──────────────────────────────

function StepProgressBar({
  months,
  checked,
}: {
  months: MonthPlan[]
  checked: CheckedState
}) {
  return (
    <div className="flex items-start gap-0 mb-8">
      {months.map((m, mi) => {
        const totalItems = SECTIONS.reduce((a, s) => a + (m[s.key]?.length ?? 0), 0)
        const totalChecked = SECTIONS.reduce((a, s) => a + (checked[mi]?.[s.key]?.size ?? 0), 0)
        const pct = totalItems === 0 ? 0 : Math.round((totalChecked / totalItems) * 100)
        const pal = PALETTES[mi]
        const isDone = pct === 100
        const isActive = pct > 0 && !isDone

        return (
          <div key={mi} className="flex items-center flex-1">
            <div className="flex flex-col items-center gap-1.5">
              {/* Step bubble */}
              <div
                className="flex size-9 items-center justify-center rounded-full border-2 transition-all duration-300"
                style={{
                  background: isDone ? pal.accent : isActive ? pal.iconBg : "white",
                  borderColor: pct > 0 ? pal.accent : "#E5E7EB",
                }}
              >
                {isDone ? (
                  <CheckCircle2 size={16} strokeWidth={2.5} color="white" aria-hidden />
                ) : (
                  <span
                    style={{
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "0.6875rem",
                      fontWeight: 700,
                      color: pct > 0 ? pal.accent : "#9CA3AF",
                    }}
                  >
                    {mi + 1}
                  </span>
                )}
              </div>
              {/* Label */}
              <span
                style={{
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "0.625rem",
                  fontWeight: 600,
                  color: pct > 0 ? pal.accent : "#9CA3AF",
                  whiteSpace: "nowrap",
                }}
              >
                {pal.label}
              </span>
            </div>

            {/* Connector bar */}
            {mi < months.length - 1 && (
              <div
                className="flex-1 mx-2 h-0.5 rounded-full -mt-4 transition-all duration-500"
                style={{ background: pct === 100 ? pal.accent : "#E5E7EB" }}
                aria-hidden
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

// ─── Sub-component: skeleton ──────────────────────────────────────────────────

function Pulse({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <div
      className={`animate-pulse rounded-xl bg-gray-200 ${className ?? ""}`}
      style={style}
      aria-hidden
    />
  )
}

function SkeletonMonthCard({ paletteIdx }: { paletteIdx: number }) {
  const bg = ["#FFFBEB", "#F0FDF4", "#F5F3FF"][paletteIdx]
  return (
    <div
      className="rounded-[var(--cv-radius-card)] p-5 md:p-6"
      style={{ background: bg, boxShadow: "var(--cv-shadow-card)" }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div className="space-y-2">
          <Pulse style={{ width: 110, height: 20, borderRadius: 8 }} />
          <Pulse style={{ width: 190, height: 13, borderRadius: 8 }} />
        </div>
        <Pulse style={{ width: 52, height: 52, borderRadius: "50%" }} />
      </div>
      {/* Grid */}
      <div className="grid gap-4 sm:grid-cols-2">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="rounded-[var(--cv-radius-card)] bg-white/60 p-4 space-y-2.5">
            <Pulse style={{ width: "55%", height: 11, borderRadius: 6 }} />
            {[85, 130, 72, 100].map((w, j) => (
              <div key={j} className="flex items-center gap-2">
                <Pulse style={{ width: 16, height: 16, borderRadius: 3, flexShrink: 0 }} />
                <Pulse style={{ width: w, height: 12, borderRadius: 6 }} />
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

function SkeletonPage() {
  return (
    <motion.div
      key="skeleton"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col gap-0"
    >
      {/* Step bar skeleton */}
      <div className="flex items-center gap-0 mb-8">
        {[0, 1, 2].map((i) => (
          <div key={i} className="flex items-center flex-1">
            <div className="flex flex-col items-center gap-1.5">
              <Pulse style={{ width: 36, height: 36, borderRadius: "50%" }} />
              <Pulse style={{ width: 46, height: 10, borderRadius: 6 }} />
            </div>
            {i < 2 && <Pulse className="flex-1 mx-2 -mt-4" style={{ height: 3 }} />}
          </div>
        ))}
      </div>

      {/* Month card skeletons with timeline */}
      {[0, 1, 2].map((i) => (
        <div key={i} className="flex gap-4 md:gap-6">
          <div className="flex flex-col items-center shrink-0 pt-1">
            <Pulse style={{ width: 40, height: 40, borderRadius: "50%" }} />
            {i < 2 && (
              <div
                className="flex-1 mt-1.5 rounded-full bg-gray-200"
                style={{ width: 3, minHeight: 40 }}
              />
            )}
          </div>
          <div className="flex-1 mb-8">
            <SkeletonMonthCard paletteIdx={i} />
          </div>
        </div>
      ))}

      {/* Button skeleton */}
      <div className="mt-2 flex gap-3 justify-center flex-wrap">
        <Pulse style={{ width: 180, height: 40, borderRadius: 8 }} />
        <Pulse style={{ width: 160, height: 40, borderRadius: 8 }} />
      </div>
    </motion.div>
  )
}

// ─── Sub-component: error card ────────────────────────────────────────────────

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
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.35, ease: EASE }}
      className="rounded-[var(--cv-radius-main)] bg-white p-10 text-center"
      style={{ boxShadow: "var(--cv-shadow-main)" }}
    >
      <div className="mx-auto mb-5 flex size-14 items-center justify-center rounded-full bg-red-50">
        <AlertCircle size={26} style={{ color: "#EF4444" }} aria-hidden />
      </div>
      <h2
        className="mb-2"
        style={{
          fontFamily: "var(--cv-font-serif)",
          fontSize: "var(--cv-text-h3)",
          fontWeight: 500,
          color: "#111827",
        }}
      >
        Roadmap generation failed
      </h2>
      <p
        className="mb-6 mx-auto max-w-sm"
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
        <Button type="button" variant="outline" onClick={() => navigate("/dashboard")}>
          <LayoutDashboard size={15} strokeWidth={1.8} aria-hidden />
          Go to Dashboard
        </Button>
      </div>
    </motion.div>
  )
}

// ─── Location state shape ─────────────────────────────────────────────────────

interface LearningRoadmapPageState {
  roadmap?: LearningRoadmapRecord
  match?: JobMatch
  resumeId?: number
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export function LearningRoadmapPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as LearningRoadmapPageState | null

  const roadmapFromState = state?.roadmap
  const match = state?.match

  // Resolve resumeId: prefer state, fall back to localStorage
  const resumeId = useMemo<number | null>(() => {
    if (state?.resumeId) return state.resumeId
    const stored = localStorage.getItem(RESUME_ID_STORAGE_KEY)
    const parsed = stored ? parseInt(stored, 10) : NaN
    return isNaN(parsed) ? null : parsed
  }, [state?.resumeId])

  const [phase, setPhase] = useState<"loading" | "done" | "error">(
    roadmapFromState ? "done" : "loading",
  )
  const [roadmap, setRoadmap] = useState<LearningRoadmapRecord | null>(
    roadmapFromState ?? null,
  )
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const months = useMemo<MonthPlan[]>(
    () =>
      roadmap
        ? [roadmap.roadmap.month_1, roadmap.roadmap.month_2, roadmap.roadmap.month_3]
        : [],
    [roadmap],
  )

  // Interactive checklist checked state
  const [checked, setChecked] = useState<CheckedState>(() =>
    months.length > 0 ? buildChecked(months) : {},
  )

  // Reinitialise checklist when months arrive (after API fetch)
  useEffect(() => {
    if (months.length > 0) {
      setChecked(buildChecked(months))
    }
  }, [months.length]) // eslint-disable-line react-hooks/exhaustive-deps

  function fetchRoadmap() {
    if (!resumeId) {
      setErrorMsg("No resume ID found. Please start from the Dashboard.")
      setPhase("error")
      return
    }
    setPhase("loading")
    setErrorMsg(null)
    generateLearningRoadmap(resumeId)
      .then((res) => {
        setRoadmap(res.roadmap)
        setPhase("done")
      })
      .catch((err) => {
        setErrorMsg(
          err instanceof ApiError
            ? err.message
            : "Roadmap generation failed. Please try again.",
        )
        setPhase("error")
      })
  }

  // Fetch on mount only when no roadmap came from state
  useEffect(() => {
    if (!roadmapFromState) fetchRoadmap()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function toggleChecked(monthIdx: number, section: SectionKey, itemIdx: number) {
    setChecked((prev) => {
      const monthCopy = { ...prev[monthIdx] }
      const s = new Set(monthCopy[section])
      s.has(itemIdx) ? s.delete(itemIdx) : s.add(itemIdx)
      monthCopy[section] = s
      return { ...prev, [monthIdx]: monthCopy }
    })
  }

  function openCareerMentor() {
    const fab = document.querySelector<HTMLButtonElement>('[aria-label="Open Career Mentor"]')
    fab?.click()
  }

  const showLoading = phase === "loading"
  const showError   = phase === "error"
  const showResults = phase === "done" && months.length > 0

  return (
    <div
      className="min-h-screen w-full px-4 py-10 md:px-8 lg:px-12"
      style={{ background: "var(--cv-bg)" }}
    >
      <div className="mx-auto max-w-3xl">

        {/* ── Page header ──────────────────────────────────────────────── */}
        <motion.div
          custom={0}
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          className="mb-8"
        >
          {/* Career banner (when match is available) */}
          {match && (
            <motion.div
              custom={0.05}
              variants={fadeUp}
              className="mb-5 flex items-center gap-3 rounded-[var(--cv-radius-card)] p-4 flex-wrap"
              style={{
                background: "var(--cv-card-sage)",
                boxShadow: "var(--cv-shadow-card)",
              }}
            >
              <CheckCircle2
                size={18}
                strokeWidth={2.5}
                style={{ color: "#22C55E", flexShrink: 0 }}
                aria-hidden
              />
              <div className="min-w-0 flex-1">
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
              <span
                className="shrink-0 rounded-full px-3 py-1"
                style={{
                  background: "white",
                  border: "1.5px solid var(--cv-card-sage-icon)",
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-caption)",
                  fontWeight: 700,
                  color: "#15803D",
                  whiteSpace: "nowrap",
                }}
              >
                {match.match_percent}% match
              </span>
            </motion.div>
          )}

          {/* Page title row */}
          <div className="flex items-center gap-4">
            <div
              className="flex size-12 shrink-0 items-center justify-center rounded-full"
              style={{ background: "var(--cv-accent-muted)" }}
              aria-hidden
            >
              {showLoading ? (
                <Loader2
                  size={22}
                  strokeWidth={1.8}
                  className="animate-spin"
                  style={{ color: "var(--cv-accent)" }}
                />
              ) : (
                <Map size={22} strokeWidth={1.6} style={{ color: "var(--cv-accent)" }} />
              )}
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
                Your 3-Month Learning Roadmap
              </h1>
              <p
                style={{
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-small)",
                  color: "#6B7280",
                  marginTop: 2,
                }}
              >
                {showLoading
                  ? "Generating your personalised plan — this usually takes 30–60 seconds…"
                  : match
                  ? `Personalised plan to become job-ready for ${match.role_title} in 90 days`
                  : "A personalised 90-day plan grounded in your Skill Gap Analysis"}
              </p>
            </div>
          </div>
        </motion.div>

        {/* ── Content (animated state machine) ────────────────────────── */}
        <AnimatePresence mode="wait">

          {/* Loading skeleton */}
          {showLoading && <SkeletonPage key="skeleton" />}

          {/* Error */}
          {showError && (
            <ErrorCard
              key="error"
              message={errorMsg ?? "Something went wrong."}
              onRetry={resumeId ? fetchRoadmap : undefined}
            />
          )}

          {/* Results */}
          {showResults && (
            <motion.div
              key="results"
              variants={stagger}
              initial="hidden"
              animate="visible"
              className="flex flex-col"
            >
              {/* Horizontal step progress bar */}
              <motion.div variants={cardItem}>
                <StepProgressBar months={months} checked={checked} />
              </motion.div>

              {/* Month cards with vertical timeline */}
              {months.map((month, mi) => (
                <MonthCard
                  key={mi}
                  month={month}
                  palette={PALETTES[mi]}
                  monthIdx={mi}
                  checked={
                    checked[mi] ?? makeEmptyMonth()
                  }
                  onToggle={(section, i) => toggleChecked(mi, section, i)}
                  isLast={mi === months.length - 1}
                />
              ))}

              {/* ── CTA footer ─────────────────────────────────────────── */}
              <motion.div
                variants={cardItem}
                className="mt-2 flex flex-col items-center gap-3 sm:flex-row sm:justify-center"
              >
                <Button
                  type="button"
                  size="lg"
                  onClick={openCareerMentor}
                  className="gap-2 w-full sm:w-auto"
                  style={{
                    background: "var(--cv-accent)",
                    color: "#fff",
                    fontFamily: "var(--cv-font-sans)",
                    fontWeight: 600,
                    fontSize: "var(--cv-text-small)",
                  }}
                >
                  <Users size={17} strokeWidth={2} aria-hidden />
                  Open Career Mentor
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="lg"
                  onClick={() => navigate("/dashboard")}
                  className="gap-2 w-full sm:w-auto"
                  style={{
                    fontFamily: "var(--cv-font-sans)",
                    fontWeight: 500,
                    fontSize: "var(--cv-text-small)",
                  }}
                >
                  <LayoutDashboard size={17} strokeWidth={1.8} aria-hidden />
                  Go to Dashboard
                </Button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
