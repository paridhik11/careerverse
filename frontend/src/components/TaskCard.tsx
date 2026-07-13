/**
 * TaskCard — renders a single VWE task with its context, resources, activity
 * input, and submit button.
 *
 * Activity rendering varies by type:
 *   multiple_choice — radio buttons
 *   short_answer    — single textarea
 *   prioritize      — numbered textarea with list hint
 *   bug_analysis    — textarea with diagnostic prompt
 *   email           — textarea styled as email compose
 *   report          — textarea with report prompt
 *
 * After the user types/selects and clicks Submit, the parent receives the
 * answer string and can display the FeedbackCard.
 */

import { useState } from "react"
import { motion } from "framer-motion"
import { BookOpen, ChevronDown, ChevronUp, Clock, FileText, Target, Zap } from "lucide-react"

import { Button } from "@/components/ui/button"
import type { SimulationTask } from "@/types"

const EASE = [0.22, 1, 0.36, 1] as const

/* ─── Difficulty badge config ─────────────────────────────────────────── */

const DIFFICULTY_CONFIG: Record<string, { bg: string; text: string }> = {
  Easy: { bg: "var(--cv-accent-muted)", text: "var(--cv-accent)" },
  Intermediate: { bg: "var(--cv-accent-muted)", text: "var(--cv-accent)" },
  Hard: { bg: "var(--cv-accent-muted)", text: "var(--cv-accent)" },
  Advanced: { bg: "var(--cv-accent-muted)", text: "var(--cv-accent)" },
}

function DifficultyBadge({ difficulty }: { difficulty: string }) {
  const cfg = DIFFICULTY_CONFIG[difficulty] ?? { bg: "var(--cv-surface-subtle)", text: "var(--cv-ink-muted)" }
  return (
    <span
      className="rounded-full px-2.5 py-0.5"
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

/* ─── Resource panel ─────────────────────────────────────────────────── */

function ResourcePanel({ type, content }: { type: string; content: string }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div
      className="rounded-[var(--cv-radius-card)] overflow-hidden"
      style={{ background: "var(--cv-card-surface)", boxShadow: "var(--cv-shadow-card)" }}
    >
      <button
        type="button"
        onClick={() => setIsOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3"
      >
        <div className="flex items-center gap-2">
          <FileText size={14} strokeWidth={1.8} style={{ color: "var(--cv-accent-2)" }} aria-hidden />
          <span
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              fontWeight: 600,
              color: "var(--cv-accent-2)",
            }}
          >
            {type}
          </span>
        </div>
        {isOpen ? (
          <ChevronUp size={16} strokeWidth={2} style={{ color: "var(--cv-ink-muted)" }} aria-hidden />
        ) : (
          <ChevronDown size={16} strokeWidth={2} style={{ color: "var(--cv-ink-muted)" }} aria-hidden />
        )}
      </button>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.25, ease: EASE }}
          className="border-t px-4 pb-4 pt-3"
          style={{ borderColor: "var(--cv-border)" }}
        >
          <p
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              color: "var(--cv-ink-muted)",
              lineHeight: 1.7,
              whiteSpace: "pre-wrap",
            }}
          >
            {content}
          </p>
        </motion.div>
      )}
    </div>
  )
}

/* ─── Activity input ─────────────────────────────────────────────────── */

interface ActivityInputProps {
  task: SimulationTask
  value: string
  onChange: (val: string) => void
  isSubmitted: boolean
}

function ActivityInput({ task, value, onChange, isSubmitted }: ActivityInputProps) {
  const { activity } = task

  if (activity.type === "multiple_choice" && activity.options.length > 0) {
    return (
      <div className="flex flex-col gap-2">
        {activity.options.map((option, i) => {
          const isSelected = value === option
          return (
            <label
              key={i}
              className="flex cursor-pointer items-start gap-3 rounded-[var(--cv-radius-card)] p-4 transition-colors duration-150"
              style={{
                background: isSelected ? "var(--cv-accent-muted)" : "var(--cv-surface-subtle)",
                border: isSelected
                  ? "2px solid var(--cv-accent)"
                  : "2px solid transparent",
                cursor: isSubmitted ? "default" : "pointer",
              }}
            >
              <input
                type="radio"
                name={`task-${task.task_number}`}
                value={option}
                checked={isSelected}
                onChange={() => !isSubmitted && onChange(option)}
                disabled={isSubmitted}
                className="mt-0.5 accent-[var(--cv-accent)]"
              />
              <span
                style={{
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-small)",
                  color: isSelected ? "var(--cv-ink)" : "var(--cv-ink-muted)",
                  fontWeight: isSelected ? 600 : 400,
                  lineHeight: 1.5,
                }}
              >
                {option}
              </span>
            </label>
          )
        })}
      </div>
    )
  }

  const placeholders: Record<string, string> = {
    short_answer: "Type your answer here…",
    prioritize: "List your priorities in order, one per line…",
    bug_analysis: "Describe your diagnosis and the steps to fix it…",
    email: "Write your email here…",
    report: "Write your report here…",
  }

  const minRows: Record<string, number> = {
    short_answer: 4,
    prioritize: 5,
    bug_analysis: 6,
    email: 7,
    report: 7,
  }

  return (
    <textarea
      value={value}
      onChange={(e) => !isSubmitted && onChange(e.target.value)}
      disabled={isSubmitted}
      placeholder={placeholders[activity.type] ?? "Write your response…"}
      rows={minRows[activity.type] ?? 5}
      className="w-full resize-y rounded-[var(--cv-radius-card)] border-0 bg-[var(--cv-surface-subtle)] px-4 py-3 outline-none ring-1 ring-[var(--cv-border)] transition-shadow duration-150 focus:ring-2 focus:ring-[var(--cv-accent)] disabled:resize-none disabled:opacity-70"
      style={{
        fontFamily: "var(--cv-font-sans)",
        fontSize: "var(--cv-text-small)",
        color: "var(--cv-ink)",
        lineHeight: 1.6,
      }}
    />
  )
}

/* ─── Main component ─────────────────────────────────────────────────── */

interface TaskCardProps {
  task: SimulationTask
  taskIndex: number
  isSubmitted: boolean
  onSubmit: (answer: string) => void
}

export function TaskCard({ task, taskIndex: _taskIndex, isSubmitted, onSubmit }: TaskCardProps) {
  const [answer, setAnswer] = useState("")

  const canSubmit = answer.trim().length > 0 && !isSubmitted

  return (
    <motion.div
      key={task.task_number}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: EASE }}
      className="flex flex-col gap-5"
    >
      {/* Task header */}
      <div>
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <span
            className="rounded-full px-3 py-0.5"
            style={{
              background: "var(--cv-accent-muted)",
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-caption)",
              fontWeight: 700,
              color: "var(--cv-accent)",
            }}
          >
            Task {task.task_number}
          </span>
          <DifficultyBadge difficulty={task.difficulty} />
          <span
            className="flex items-center gap-1"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-caption)",
              color: "var(--cv-ink-muted)",
            }}
          >
            <Clock size={12} strokeWidth={2} aria-hidden />
            {task.estimated_time}
          </span>
        </div>
        <h2
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h2)",
            fontWeight: 400,
            color: "var(--cv-ink)",
            lineHeight: 1.2,
          }}
        >
          {task.title}
        </h2>
      </div>

      {/* Objective */}
      <div
        className="flex items-start gap-3 rounded-[var(--cv-radius-card)] p-4"
        style={{ background: "var(--cv-card-surface)", boxShadow: "var(--cv-shadow-card)" }}
      >
        <Target size={16} strokeWidth={2} style={{ color: "#FBBF24", marginTop: "2px", flexShrink: 0 }} aria-hidden />
        <div>
          <p
            className="mb-0.5"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-caption)",
              fontWeight: 700,
              color: "#FBBF24",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            Objective
          </p>
          <p
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              color: "var(--cv-ink)",
              lineHeight: 1.6,
            }}
          >
            {task.objective}
          </p>
        </div>
      </div>

      {/* Context */}
      <div>
        <div className="mb-2 flex items-center gap-1.5">
          <Zap size={14} strokeWidth={2} style={{ color: "var(--cv-ink-muted)" }} aria-hidden />
          <p
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-caption)",
              fontWeight: 700,
              color: "var(--cv-ink-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}
          >
            Context
          </p>
        </div>
        <p
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            color: "var(--cv-ink)",
            lineHeight: 1.7,
          }}
        >
          {task.context}
        </p>
      </div>

      {/* Resources */}
      {task.resources.length > 0 && (
        <div>
          <div className="mb-2 flex items-center gap-1.5">
            <BookOpen size={14} strokeWidth={2} style={{ color: "var(--cv-ink-muted)" }} aria-hidden />
            <p
              style={{
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-caption)",
                fontWeight: 700,
                color: "var(--cv-ink-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
              }}
            >
              Resources
            </p>
          </div>
          <div className="flex flex-col gap-2">
            {task.resources.map((resource, i) => (
              <ResourcePanel key={i} type={resource.type} content={resource.content} />
            ))}
          </div>
        </div>
      )}

      {/* Activity */}
      <div>
        <p
          className="mb-3"
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h3)",
            fontWeight: 500,
            color: "var(--cv-ink)",
            lineHeight: 1.3,
          }}
        >
          {task.activity.question}
        </p>
        <ActivityInput
          task={task}
          value={answer}
          onChange={setAnswer}
          isSubmitted={isSubmitted}
        />
      </div>

      {/* Submit */}
      {!isSubmitted && (
        <div className="flex justify-end">
          <Button
            type="button"
            disabled={!canSubmit}
            onClick={() => onSubmit(answer)}
            className="font-semibold text-white hover:opacity-90 disabled:opacity-40"
            style={{ background: "var(--cv-accent)" }}
          >
            Submit Answer
          </Button>
        </div>
      )}
    </motion.div>
  )
}
