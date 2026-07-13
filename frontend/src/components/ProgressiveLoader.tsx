/**
 * ProgressiveLoader — replaces a single blocking spinner with step-by-step
 * stage progress so users know exactly what's happening.
 *
 * Usage:
 *   const stages = useProgressiveLoader([
 *     "Uploading Resume",
 *     "Reviewing Resume",
 *     "Finding Career Matches",
 *   ])
 *   stages.complete(0)  // marks stage 0 done, activates stage 1
 *
 *   <ProgressiveLoader stages={stages.stages} />
 */

import { motion, AnimatePresence } from "framer-motion"
import { CheckCircle2, Loader2 } from "lucide-react"
import { useState, useCallback } from "react"

export type StageStatus = "pending" | "active" | "done" | "error"

export interface LoaderStage {
  label: string
  status: StageStatus
}

interface ProgressiveLoaderProps {
  stages: LoaderStage[]
  className?: string
}

const EASE = [0.22, 1, 0.36, 1] as const

export function ProgressiveLoader({ stages, className = "" }: ProgressiveLoaderProps) {
  return (
    <div
      className={`flex flex-col gap-3 ${className}`}
      role="status"
      aria-label="Loading progress"
    >
      {stages.map((stage, i) => (
        <motion.div
          key={`${stage.label}-${i}`}
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3, delay: i * 0.05, ease: EASE }}
          className="flex items-center gap-3"
        >
          {/* Status icon */}
          <div className="flex-shrink-0 w-6 h-6 flex items-center justify-center">
            <AnimatePresence mode="wait">
              {stage.status === "done" && (
                <motion.div
                  key="done"
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                  transition={{ duration: 0.25, ease: EASE }}
                >
                  <CheckCircle2
                    size={18}
                    strokeWidth={2}
                    style={{ color: "#4ADE80" }}
                    aria-hidden
                  />
                </motion.div>
              )}
              {stage.status === "active" && (
                <motion.div
                  key="active"
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.8, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <Loader2
                    size={16}
                    strokeWidth={2.5}
                    className="animate-spin"
                    style={{ color: "var(--cv-accent)" }}
                    aria-hidden
                  />
                </motion.div>
              )}
              {stage.status === "error" && (
                <motion.div
                  key="error"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <span
                    className="flex size-4 items-center justify-center rounded-full text-xs font-bold"
                    style={{ background: "rgba(239,68,68,0.2)", color: "#F87171" }}
                  >
                    ✕
                  </span>
                </motion.div>
              )}
              {stage.status === "pending" && (
                <motion.div
                  key="pending"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <span
                    className="inline-block size-3 rounded-full"
                    style={{ background: "var(--cv-surface-subtle)" }}
                    aria-hidden
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Label */}
          <motion.span
            animate={{
              color:
                stage.status === "done"
                  ? "var(--cv-ink)"
                  : stage.status === "active"
                    ? "var(--cv-ink)"
                    : "var(--cv-ink-muted)",
              fontWeight: stage.status === "active" ? 600 : 400,
            }}
            transition={{ duration: 0.2 }}
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
            }}
          >
            {stage.status === "done" ? `✓ ${stage.label}` : stage.label}
          </motion.span>
        </motion.div>
      ))}
    </div>
  )
}

/* ─── Hook ───────────────────────────────────────────────────────────────── */

export interface UseProgressiveLoaderReturn {
  stages: LoaderStage[]
  /** Mark stage `index` as done and activate the next stage. */
  complete: (index: number) => void
  /** Mark stage `index` as errored. */
  error: (index: number) => void
  /** Reset all stages to pending. */
  reset: () => void
  /** True when all stages are done. */
  allDone: boolean
}

export function useProgressiveLoader(labels: string[]): UseProgressiveLoaderReturn {
  const initial: LoaderStage[] = labels.map((label, i) => ({
    label,
    status: i === 0 ? "active" : "pending",
  }))

  const [stages, setStages] = useState<LoaderStage[]>(initial)

  const complete = useCallback((index: number) => {
    setStages((prev) =>
      prev.map((stage, i) => {
        if (i === index) return { ...stage, status: "done" }
        if (i === index + 1) return { ...stage, status: "active" }
        return stage
      }),
    )
  }, [])

  const error = useCallback((index: number) => {
    setStages((prev) =>
      prev.map((stage, i) => (i === index ? { ...stage, status: "error" } : stage)),
    )
  }, [])

  const reset = useCallback(() => {
    setStages(
      labels.map((label, i) => ({
        label,
        status: i === 0 ? "active" : "pending",
      })),
    )
  }, [labels])

  const allDone = stages.every((s) => s.status === "done")

  return { stages, complete, error, reset, allDone }
}
