import { type LucideIcon } from "lucide-react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

/* ─── Types ──────────────────────────────────────────────────────────────── */

/** @deprecated Color variants no longer tint the card — kept for call-site compat. */
export type ColorVariant = "amber" | "sage" | "sky" | "lavender"
export type StatusVariant = "ready" | "progress" | "locked"

export interface JourneyCardProps {
  title: string
  description: string
  colorVariant: ColorVariant
  icon: LucideIcon
  statusLabel: string
  statusVariant?: StatusVariant
  className?: string
  /** Optional small category label overlaid as a badge. */
  category?: string
}

const chipStyles: Record<StatusVariant, { dot: string; chip: string }> = {
  ready: {
    dot: "bg-[var(--cv-accent)]",
    chip: "bg-[var(--cv-accent-muted)] text-[var(--cv-accent)]",
  },
  progress: {
    dot: "bg-[var(--cv-accent)]",
    chip: "bg-[var(--cv-accent-muted)] text-[var(--cv-accent)]",
  },
  locked: {
    dot: "bg-[var(--cv-ink-muted)]",
    chip: "bg-[var(--cv-surface-subtle)] text-[var(--cv-ink-muted)]",
  },
}

/* ─── Component ──────────────────────────────────────────────────────────── */

export function JourneyCard({
  title,
  description,
  icon: Icon,
  statusLabel,
  statusVariant = "ready",
  className,
  category,
}: JourneyCardProps) {
  const { dot, chip } = chipStyles[statusVariant]

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className={cn(
        "cv-card relative flex items-start gap-4 p-6",
        "transition-shadow duration-200 hover:shadow-[var(--cv-shadow-main)]",
        className,
      )}
    >
      <div className="cv-icon-circle">
        <Icon className="h-5 w-5" strokeWidth={1.8} style={{ color: "var(--cv-accent)" }} />
      </div>

      <div className="flex min-w-0 flex-1 flex-col gap-1.5">
        {category && <span className="cv-badge w-fit">{category}</span>}
        <span
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h3)",
            fontWeight: 500,
            color: "var(--cv-ink)",
            lineHeight: 1.3,
          }}
        >
          {title}
        </span>
        <span
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            lineHeight: 1.5,
            color: "var(--cv-ink-muted)",
          }}
        >
          {description}
        </span>
      </div>

      <div
        className={cn(
          "flex shrink-0 items-center gap-1.5 self-center rounded-full px-3 py-1",
          chip,
        )}
        style={{
          fontFamily: "var(--cv-font-sans)",
          fontSize: "var(--cv-text-caption)",
          fontWeight: 500,
        }}
      >
        <span className={cn("h-1.5 w-1.5 rounded-full", dot)} />
        {statusLabel}
      </div>
    </motion.div>
  )
}
