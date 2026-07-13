/**
 * FeedbackCard — post-task feedback panel shown immediately after submission.
 *
 * Displays:
 *   ✓  What you did well (positive)
 *   💡 One improvement
 *   📚 Why this matters in the real workplace
 *
 * Also shows the expected solution in a collapsible panel.
 */

import { motion } from "framer-motion"
import { ArrowRight, BookOpen, CheckCircle2, Lightbulb } from "lucide-react"

import { Button } from "@/components/ui/button"
import type { TaskFeedback } from "@/types"

const EASE = [0.22, 1, 0.36, 1] as const

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, delay: i * 0.08, ease: EASE },
  }),
}

interface FeedbackCardProps {
  feedback: TaskFeedback
  expectedSolution: string
  isLastTask: boolean
  onContinue: () => void
}

export function FeedbackCard({
  feedback,
  expectedSolution,
  isLastTask,
  onContinue,
}: FeedbackCardProps) {
  const items = [
    {
      icon: CheckCircle2,
      iconColor: "var(--cv-accent)",
      bg: "var(--cv-card-surface)",
      label: "What you did well",
      content: feedback.positive,
    },
    {
      icon: Lightbulb,
      iconColor: "var(--cv-accent)",
      bg: "var(--cv-card-surface)",
      label: "One improvement",
      content: feedback.improvement,
    },
    {
      icon: BookOpen,
      iconColor: "var(--cv-accent)",
      bg: "var(--cv-card-surface)",
      label: "Why this matters",
      content: feedback.real_world_importance,
    },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: EASE }}
      className="flex flex-col gap-3"
    >
      {/* Feedback items */}
      {items.map((item, i) => {
        const Icon = item.icon
        return (
          <motion.div
            key={i}
            custom={i}
            variants={itemVariants}
            initial="hidden"
            animate="visible"
            className="cv-card p-4"
            style={{ background: item.bg }}
          >
            <div className="flex items-start gap-3">
              <div
                className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full"
                style={{ background: "var(--cv-accent-soft)" }}
              >
                <Icon size={14} strokeWidth={2} style={{ color: item.iconColor }} aria-hidden />
              </div>
              <div className="min-w-0 flex-1">
                <p
                  className="mb-1"
                  style={{
                    fontFamily: "var(--cv-font-sans)",
                    fontSize: "var(--cv-text-caption)",
                    fontWeight: 700,
                    color: "var(--cv-ink-muted)",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  {item.label}
                </p>
                <p
                  style={{
                    fontFamily: "var(--cv-font-sans)",
                    fontSize: "var(--cv-text-small)",
                    color: "var(--cv-ink-muted)",
                    lineHeight: 1.65,
                  }}
                >
                  {item.content}
                </p>
              </div>
            </div>
          </motion.div>
        )
      })}

      {/* Expected solution (collapsible-style reveal) */}
      <motion.details
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3, delay: 0.3 }}
        className="rounded-[var(--cv-radius-card)] bg-[var(--cv-surface-subtle)] px-4 py-3"
        style={{ boxShadow: "var(--cv-shadow-card)" }}
      >
        <summary
          className="cursor-pointer select-none"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            fontWeight: 600,
            color: "var(--cv-ink)",
          }}
        >
          View model answer
        </summary>
        <p
          className="mt-2"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            color: "var(--cv-ink-muted)",
            lineHeight: 1.65,
          }}
        >
          {expectedSolution}
        </p>
      </motion.details>

      {/* Continue / Finish button */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: 0.35, ease: EASE }}
        className="flex justify-end"
      >
        <Button
          type="button"
          onClick={onContinue}
          className="font-semibold text-white hover:opacity-90"
          style={{ background: "var(--cv-accent)" }}
        >
          {isLastTask ? "See results" : "Continue"}
          <ArrowRight size={15} strokeWidth={2} aria-hidden />
        </Button>
      </motion.div>
    </motion.div>
  )
}
