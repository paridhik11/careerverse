/**
 * ProgressIndicator — horizontal step tracker for the Virtual Work Experience.
 *
 * Shows which task the user is on and their overall completion percentage.
 * Each step is either completed (filled), active (pulsing), or pending (empty).
 */

import { motion } from "framer-motion"

const EASE = [0.22, 1, 0.36, 1] as const

interface ProgressIndicatorProps {
  totalTasks: number
  /** 0-based index of the current active task (-1 = on overview, totalTasks = finished) */
  currentTaskIndex: number
  /** 0-based indices of completed tasks */
  completedTasks: number[]
}

export function ProgressIndicator({
  totalTasks,
  currentTaskIndex,
  completedTasks,
}: ProgressIndicatorProps) {
  const completedCount = completedTasks.length
  const percent = Math.round((completedCount / totalTasks) * 100)

  return (
    <div className="flex flex-col gap-2">
      {/* Step dots */}
      <div className="flex items-center gap-1.5">
        {Array.from({ length: totalTasks }, (_, i) => {
          const isDone = completedTasks.includes(i)
          const isActive = i === currentTaskIndex

          return (
            <div key={i} className="flex items-center gap-1.5">
              <div
                className="flex size-6 items-center justify-center rounded-full transition-all duration-300"
                style={{
                  background: isDone
                    ? "var(--cv-card-sage-icon)"
                    : isActive
                      ? "var(--cv-accent)"
                      : "#E5E7EB",
                }}
                aria-label={`Task ${i + 1}: ${isDone ? "completed" : isActive ? "active" : "pending"}`}
              >
                {isDone ? (
                  <svg viewBox="0 0 12 12" fill="none" className="size-3" aria-hidden>
                    <path
                      d="M2 6l3 3 5-5"
                      stroke="#166534"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                ) : (
                  <span
                    style={{
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "0.625rem",
                      fontWeight: 700,
                      color: isActive ? "#fff" : "#9CA3AF",
                    }}
                  >
                    {i + 1}
                  </span>
                )}
              </div>
              {i < totalTasks - 1 && (
                <div
                  className="h-px flex-1 transition-colors duration-300"
                  style={{
                    width: "1.5rem",
                    background: isDone ? "var(--cv-card-sage-icon)" : "#E5E7EB",
                  }}
                  aria-hidden
                />
              )}
            </div>
          )
        })}
      </div>

      {/* Progress bar */}
      <div className="h-1 overflow-hidden rounded-full bg-gray-100">
        <motion.div
          className="h-full rounded-full"
          style={{ background: "var(--cv-accent)" }}
          initial={{ width: "0%" }}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.6, ease: EASE }}
          aria-hidden
        />
      </div>

      <p
        style={{
          fontFamily: "var(--cv-font-sans)",
          fontSize: "var(--cv-text-caption)",
          color: "#9CA3AF",
          fontWeight: 500,
        }}
      >
        {completedCount} of {totalTasks} tasks completed · {percent}%
      </p>
    </div>
  )
}
