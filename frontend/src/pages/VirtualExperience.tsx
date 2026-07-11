/**
 * VirtualExperiencePage — Forage-inspired virtual work experience.
 *
 * Layout:
 *   Left sidebar (fixed)  |  Main content area (scrollable)
 *
 * Sections:
 *   overview → task-0 → task-1 … → task-N → finish
 *
 * Each task unlocks only after the previous is submitted.
 * Feedback is shown inline after submission, then "Continue →" advances to
 * the next task. After the final task, the finish / congratulations screen
 * is shown with "Choose This Career" and "Explore Another Career" CTAs.
 *
 * Data flow:
 *   CareerMatchesPage navigates here with `VirtualExperienceState` in
 *   location.state: { simulation, match, resumeId, allSimulations }.
 *
 * "Choose This Career" calls PATCH /job-matches/{jobMatchId}/choose then
 * navigates to /skill-gap.
 */

import { useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { AnimatePresence, motion } from "framer-motion"
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Briefcase,
  Clock,
  CheckCircle2,
  RefreshCcw,
  Sparkles,
  Trophy,
  Users,
  Zap,
} from "lucide-react"

import { ExperienceSidebar, type SidebarSection } from "@/components/ExperienceSidebar"
import { FeedbackCard } from "@/components/FeedbackCard"
import { ProgressIndicator } from "@/components/ProgressIndicator"
import { TaskCard } from "@/components/TaskCard"
import { Button } from "@/components/ui/button"
import { chooseJobMatch } from "@/services/jobMatches"
import { ApiError } from "@/services/api"
import type { VirtualExperienceState } from "@/types"

const EASE = [0.22, 1, 0.36, 1] as const

/* ─── Difficulty badge ─────────────────────────────────────────────────── */

const DIFFICULTY_CONFIG: Record<string, { bg: string; text: string }> = {
  Beginner: { bg: "var(--cv-card-sage)", text: "#166534" },
  Intermediate: { bg: "var(--cv-card-amber)", text: "#92400E" },
  Advanced: { bg: "var(--cv-card-lavender)", text: "#5B21B6" },
}

function DifficultyBadge({ difficulty }: { difficulty: string }) {
  const cfg = DIFFICULTY_CONFIG[difficulty] ?? { bg: "#F3F4F6", text: "#6B7280" }
  return (
    <span
      className="rounded-full px-3 py-0.5"
      style={{
        background: cfg.bg,
        fontFamily: "var(--cv-font-sans)",
        fontSize: "var(--cv-text-caption)",
        fontWeight: 600,
        color: cfg.text,
      }}
    >
      {difficulty}
    </span>
  )
}

/* ─── Overview panel ────────────────────────────────────────────────────── */

function OverviewPanel({
  simulation,
  onStart,
}: {
  simulation: VirtualExperienceState["simulation"]["simulation"]
  onStart: () => void
}) {
  const { overview, what_youll_learn, what_youll_do, job_title, estimated_duration, difficulty } =
    simulation

  return (
    <motion.div
      key="overview"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.4, ease: EASE }}
      className="flex flex-col gap-6"
    >
      {/* Hero */}
      <div
        className="rounded-[var(--cv-radius-main)] p-6"
        style={{ background: "var(--cv-card-lavender)", boxShadow: "var(--cv-shadow-card)" }}
      >
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <div
            className="flex size-11 items-center justify-center rounded-full"
            style={{ background: "var(--cv-card-lavender-icon)" }}
            aria-hidden
          >
            <Sparkles size={20} strokeWidth={1.8} color="#111827" />
          </div>
          <div>
            <p
              style={{
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-caption)",
                fontWeight: 700,
                color: "#6B7280",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
              }}
            >
              Virtual Work Experience
            </p>
            <h1
              style={{
                fontFamily: "var(--cv-font-serif)",
                fontSize: "var(--cv-text-h1)",
                fontWeight: 400,
                color: "#111827",
                lineHeight: 1.15,
              }}
            >
              {job_title}
            </h1>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <span
            className="flex items-center gap-1.5"
            style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "#6B7280" }}
          >
            <Clock size={14} strokeWidth={2} aria-hidden />
            {estimated_duration}
          </span>
          <DifficultyBadge difficulty={difficulty} />
        </div>
      </div>

      {/* Scenario context */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div
          className="rounded-[var(--cv-radius-card)] p-5"
          style={{ background: "var(--cv-card-sage)", boxShadow: "var(--cv-shadow-card)" }}
        >
          <div className="mb-3 flex items-center gap-2">
            <Briefcase size={15} strokeWidth={1.8} style={{ color: "#374151" }} aria-hidden />
            <span
              style={{
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-caption)",
                fontWeight: 700,
                color: "#6B7280",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              The Company
            </span>
          </div>
          <p
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              color: "#374151",
              lineHeight: 1.7,
            }}
          >
            {overview.company_context}
          </p>
        </div>

        <div
          className="rounded-[var(--cv-radius-card)] p-5"
          style={{ background: "var(--cv-card-sky)", boxShadow: "var(--cv-shadow-card)" }}
        >
          <div className="mb-3 flex items-center gap-2">
            <Users size={15} strokeWidth={1.8} style={{ color: "#374151" }} aria-hidden />
            <span
              style={{
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-caption)",
                fontWeight: 700,
                color: "#6B7280",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              The Team
            </span>
          </div>
          <p
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              color: "#374151",
              lineHeight: 1.7,
            }}
          >
            {overview.team_context}
          </p>
        </div>

        <div
          className="rounded-[var(--cv-radius-card)] p-5"
          style={{ background: "var(--cv-card-amber)", boxShadow: "var(--cv-shadow-card)" }}
        >
          <div className="mb-3 flex items-center gap-2">
            <Zap size={15} strokeWidth={1.8} style={{ color: "#374151" }} aria-hidden />
            <span
              style={{
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-caption)",
                fontWeight: 700,
                color: "#6B7280",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Your Role
            </span>
          </div>
          <p
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              color: "#374151",
              lineHeight: 1.7,
            }}
          >
            {overview.your_role}
          </p>
        </div>

        <div
          className="rounded-[var(--cv-radius-card)] p-5"
          style={{ background: "#F9FAFB", boxShadow: "var(--cv-shadow-card)" }}
        >
          <div className="mb-3 flex items-center gap-2">
            <Briefcase size={15} strokeWidth={1.8} style={{ color: "#374151" }} aria-hidden />
            <span
              style={{
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-caption)",
                fontWeight: 700,
                color: "#6B7280",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              The Project
            </span>
          </div>
          <p
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              color: "#374151",
              lineHeight: 1.7,
            }}
          >
            {overview.project_background}
          </p>
        </div>
      </div>

      {/* What you'll learn */}
      <div
        className="rounded-[var(--cv-radius-card)] p-5"
        style={{ background: "white", boxShadow: "var(--cv-shadow-card)" }}
      >
        <h2
          className="mb-4"
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h3)",
            fontWeight: 500,
            color: "#111827",
          }}
        >
          What you'll learn
        </h2>
        <ul className="flex flex-col gap-2.5">
          {what_youll_learn.map((item, i) => (
            <li key={i} className="flex items-start gap-3">
              <CheckCircle2 size={16} strokeWidth={2} style={{ color: "#22C55E", marginTop: "2px", flexShrink: 0 }} aria-hidden />
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
      </div>

      {/* What you'll do */}
      <div
        className="rounded-[var(--cv-radius-card)] p-5"
        style={{ background: "white", boxShadow: "var(--cv-shadow-card)" }}
      >
        <h2
          className="mb-4"
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h3)",
            fontWeight: 500,
            color: "#111827",
          }}
        >
          What you'll do
        </h2>
        <ol className="flex flex-col gap-2.5">
          {what_youll_do.map((item, i) => (
            <li key={i} className="flex items-start gap-3">
              <span
                className="flex size-5 shrink-0 items-center justify-center rounded-full"
                style={{
                  background: "var(--cv-accent-muted)",
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-caption)",
                  fontWeight: 700,
                  color: "var(--cv-accent)",
                  marginTop: "1px",
                }}
              >
                {i + 1}
              </span>
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
        </ol>
      </div>

      {/* Start CTA */}
      <div className="flex justify-center pb-4">
        <Button
          type="button"
          onClick={onStart}
          className="px-8 font-semibold text-white hover:opacity-90"
          style={{ background: "var(--cv-accent)" }}
        >
          Start Experience
          <ArrowRight size={16} strokeWidth={2} aria-hidden />
        </Button>
      </div>
    </motion.div>
  )
}

/* ─── Congratulations panel ──────────────────────────────────────────────── */

function CongratulationsPanel({
  jobTitle,
  onChoose,
  onExploreAnother,
  isChoosing,
  chooseError,
}: {
  jobTitle: string
  onChoose: () => void
  onExploreAnother: () => void
  isChoosing: boolean
  chooseError: string | null
}) {
  return (
    <motion.div
      key="finish"
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.97 }}
      transition={{ duration: 0.45, ease: EASE }}
      className="flex flex-col items-center gap-6 py-8 text-center"
    >
      {/* Trophy */}
      <motion.div
        initial={{ scale: 0.5, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.1, ease: EASE }}
        className="flex size-20 items-center justify-center rounded-full"
        style={{ background: "var(--cv-card-amber-icon)" }}
      >
        <Trophy size={36} strokeWidth={1.6} color="#111827" aria-hidden />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.2, ease: EASE }}
      >
        <h1
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h1)",
            fontWeight: 400,
            color: "#111827",
            lineHeight: 1.15,
          }}
        >
          Congratulations! 🎉
        </h1>
        <p
          className="mx-auto mt-3 max-w-md text-gray-500"
          style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-body)", lineHeight: 1.7 }}
        >
          You have completed the{" "}
          <strong style={{ color: "#111827" }}>{jobTitle}</strong>{" "}
          Virtual Work Experience.
        </p>
      </motion.div>

      {/* Error */}
      {chooseError && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex w-full max-w-sm items-start gap-3 rounded-[var(--cv-radius-card)] p-4"
          style={{ background: "#FEF2F2" }}
        >
          <AlertCircle size={16} strokeWidth={2} color="#DC2626" className="mt-0.5 shrink-0" aria-hidden />
          <p style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "#991B1B" }}>
            {chooseError}
          </p>
        </motion.div>
      )}

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.35, ease: EASE }}
        className="flex flex-col items-center gap-3 sm:flex-row"
      >
        <Button
          type="button"
          onClick={onChoose}
          disabled={isChoosing}
          className="px-8 font-semibold text-white hover:opacity-90 disabled:opacity-60"
          style={{ background: "var(--cv-accent)" }}
        >
          {isChoosing ? (
            <>
              <span className="relative flex size-3.5 shrink-0">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-white/60" />
                <span className="relative inline-flex size-3.5 rounded-full bg-white" />
              </span>
              Choosing…
            </>
          ) : (
            <>
              <CheckCircle2 size={16} strokeWidth={2} aria-hidden />
              Choose This Career
            </>
          )}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={onExploreAnother}
          disabled={isChoosing}
        >
          <RefreshCcw size={15} strokeWidth={2} aria-hidden />
          Explore Another Career
        </Button>
      </motion.div>
    </motion.div>
  )
}

/* ─── Missing state ──────────────────────────────────────────────────────── */

function MissingSimulationState() {
  const navigate = useNavigate()
  return (
    <div
      className="flex min-h-screen w-full items-center justify-center px-4 py-10"
      style={{ background: "var(--cv-bg)" }}
    >
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: EASE }}
        className="w-full max-w-md rounded-[var(--cv-radius-main)] bg-white p-8 text-center"
        style={{ boxShadow: "var(--cv-shadow-main)" }}
      >
        <div
          className="mx-auto mb-4 flex size-14 items-center justify-center rounded-full"
          style={{ background: "var(--cv-card-lavender-icon)" }}
          aria-hidden
        >
          <Sparkles size={24} strokeWidth={1.6} color="#111827" />
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
          Experience not found
        </h1>
        <p
          className="mt-3 text-gray-500"
          style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", lineHeight: 1.6 }}
        >
          Please navigate here via the Career Matches page. The simulation data
          is session-specific and cannot be accessed directly.
        </p>
        <Button
          type="button"
          className="mt-6 w-full text-white hover:opacity-90"
          style={{ background: "var(--cv-accent)" }}
          onClick={() => navigate("/resume/upload")}
        >
          Start over
        </Button>
      </motion.div>
    </div>
  )
}

/* ─── Main page ─────────────────────────────────────────────────────────── */

interface TaskState {
  answer: string
  isSubmitted: boolean
}

export function VirtualExperiencePage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as VirtualExperienceState | null

  const simulationRecord = state?.simulation
  const tasks = simulationRecord?.simulation?.tasks ?? []
  const totalTasks = tasks.length

  const [activeSection, setActiveSection] = useState<SidebarSection>("overview")
  const [taskStates, setTaskStates] = useState<TaskState[]>(() =>
    tasks.map(() => ({ answer: "", isSubmitted: false }))
  )
  const [showFeedback, setShowFeedback] = useState<boolean[]>(() =>
    tasks.map(() => false)
  )
  const [isChoosing, setIsChoosing] = useState(false)
  const [chooseError, setChooseError] = useState<string | null>(null)

  if (!simulationRecord) {
    return <MissingSimulationState />
  }

  const { match, resumeId } = state!
  const { simulation } = simulationRecord

  const completedTaskIndices = taskStates
    .map((ts, i) => (ts.isSubmitted ? i : -1))
    .filter((i) => i >= 0)

  /* ── Handlers ─────────────────────────────────────────────────────── */

  function handleStart() {
    setActiveSection(0)
  }

  function handleTaskSubmit(taskIndex: number, answer: string) {
    setTaskStates((prev) => {
      const next = [...prev]
      next[taskIndex] = { answer, isSubmitted: true }
      return next
    })
    setShowFeedback((prev) => {
      const next = [...prev]
      next[taskIndex] = true
      return next
    })
  }

  function handleContinue(taskIndex: number) {
    const isLastTask = taskIndex === totalTasks - 1
    if (isLastTask) {
      setActiveSection("finish")
    } else {
      setActiveSection(taskIndex + 1)
    }
  }

  async function handleChooseCareer() {
    setIsChoosing(true)
    setChooseError(null)
    try {
      await chooseJobMatch(match.id)
      navigate("/skill-gap", { state: { match, resumeId } })
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : error instanceof Error
            ? error.message
            : "Failed to choose this career. Please try again."
      setChooseError(message)
    } finally {
      setIsChoosing(false)
    }
  }

  function handleExploreAnother() {
    // Go back to the Career Matches page (preserves location.state for that history entry)
    navigate(-1)
  }

  /* ── Current task index (when in a task section) ─────────────────── */
  const currentTaskIndex = typeof activeSection === "number" ? activeSection : -1

  /* ── Main content ──────────────────────────────────────────────────── */

  function renderMainContent() {
    if (activeSection === "overview") {
      return (
        <OverviewPanel
          simulation={simulation}
          onStart={handleStart}
        />
      )
    }

    if (activeSection === "finish") {
      return (
        <CongratulationsPanel
          jobTitle={simulation.job_title}
          onChoose={handleChooseCareer}
          onExploreAnother={handleExploreAnother}
          isChoosing={isChoosing}
          chooseError={chooseError}
        />
      )
    }

    if (typeof activeSection === "number") {
      const taskIdx = activeSection
      const task = tasks[taskIdx]
      const taskState = taskStates[taskIdx]
      const isFeedbackVisible = showFeedback[taskIdx]
      const isLastTask = taskIdx === totalTasks - 1

      if (!task) return null

      return (
        <motion.div
          key={`task-${taskIdx}`}
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -12 }}
          transition={{ duration: 0.35, ease: EASE }}
          className="flex flex-col gap-6"
        >
          <TaskCard
            task={task}
            taskIndex={taskIdx}
            isSubmitted={taskState.isSubmitted}
            onSubmit={(answer) => handleTaskSubmit(taskIdx, answer)}
          />

          {isFeedbackVisible && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: EASE }}
            >
              <div className="my-2 h-px bg-gray-100" aria-hidden />
              <FeedbackCard
                feedback={task.feedback}
                expectedSolution={task.expected_solution}
                isLastTask={isLastTask}
                onContinue={() => handleContinue(taskIdx)}
              />
            </motion.div>
          )}
        </motion.div>
      )
    }

    return null
  }

  return (
    <div
      className="min-h-screen w-full px-4 py-6 md:px-6"
      style={{ background: "var(--cv-bg)" }}
    >
      {/* Back navigation */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: EASE }}
        className="mb-4"
      >
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 rounded-full px-3 py-1.5 transition-colors duration-150 hover:bg-black/5"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            fontWeight: 500,
            color: "#6B7280",
          }}
        >
          <ArrowLeft size={15} strokeWidth={2} aria-hidden />
          Back to Career Matches
        </button>
      </motion.div>

      {/* Main layout: sidebar + content */}
      <div className="mx-auto flex max-w-5xl items-start gap-5">
        {/* Sidebar */}
        <div className="hidden sticky top-6 md:block">
          <ExperienceSidebar
            jobTitle={simulation.job_title}
            totalTasks={totalTasks}
            activeSection={activeSection}
            completedTasks={completedTaskIndices}
            onNavigate={setActiveSection}
          />
        </div>

        {/* Main content area */}
        <div className="min-w-0 flex-1">
          {/* Progress indicator (above content on mobile, inside content on desktop) */}
          {activeSection !== "overview" && activeSection !== "finish" && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, ease: EASE }}
              className="mb-5 rounded-[var(--cv-radius-card)] bg-white p-4"
              style={{ boxShadow: "var(--cv-shadow-card)" }}
            >
              <ProgressIndicator
                totalTasks={totalTasks}
                currentTaskIndex={currentTaskIndex}
                completedTasks={completedTaskIndices}
              />
            </motion.div>
          )}

          <div
            className="rounded-[var(--cv-radius-main)] bg-white p-6 md:p-8"
            style={{ boxShadow: "var(--cv-shadow-main)" }}
          >
            <AnimatePresence mode="wait">
              {renderMainContent()}
            </AnimatePresence>
          </div>

          {/* Mobile sidebar nav (task buttons at bottom) */}
          <div className="mt-4 flex items-center justify-center gap-2 md:hidden">
            {tasks.map((_, i) => {
              const isDone = completedTaskIndices.includes(i)
              const isActive = activeSection === i
              const isPrevDone = i === 0 || completedTaskIndices.includes(i - 1)
              const isLocked = !isPrevDone && !isDone

              return (
                <button
                  key={i}
                  type="button"
                  disabled={isLocked}
                  onClick={() => !isLocked && setActiveSection(i)}
                  className="flex size-8 items-center justify-center rounded-full transition-all duration-200"
                  style={{
                    background: isDone
                      ? "var(--cv-card-sage-icon)"
                      : isActive
                        ? "var(--cv-accent)"
                        : "#E5E7EB",
                    cursor: isLocked ? "default" : "pointer",
                  }}
                  aria-label={`Task ${i + 1}`}
                >
                  <span
                    style={{
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "0.7rem",
                      fontWeight: 700,
                      color: isDone ? "#166534" : isActive ? "#fff" : "#9CA3AF",
                    }}
                  >
                    {i + 1}
                  </span>
                </button>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
