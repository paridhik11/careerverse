import { type LucideIcon } from "lucide-react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

/* ─── Types ──────────────────────────────────────────────────────────────── */

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
}

/* ─── Token maps ─────────────────────────────────────────────────────────── */

const cardBg: Record<ColorVariant, string> = {
  amber:    "bg-[#FEF2BF]",
  sage:     "bg-[#D4EDD8]",
  sky:      "bg-[#D5E8F8]",
  lavender: "bg-[#E7DDF8]",
}

const iconBg: Record<ColorVariant, string> = {
  amber:    "bg-[#F6DC6D]",
  sage:     "bg-[#9DD4A8]",
  sky:      "bg-[#93C6ED]",
  lavender: "bg-[#C5A8EF]",
}

const iconColor: Record<ColorVariant, string> = {
  amber:    "text-amber-800",
  sage:     "text-green-800",
  sky:      "text-sky-800",
  lavender: "text-purple-800",
}

const chipStyles: Record<StatusVariant, { dot: string; chip: string }> = {
  ready: {
    dot:  "bg-[#6B7FFF]",
    chip: "bg-[#6B7FFF26] text-[#4A5FD4]",
  },
  progress: {
    dot:  "bg-amber-400",
    chip: "bg-amber-100 text-amber-700",
  },
  locked: {
    dot:  "bg-gray-400",
    chip: "bg-gray-100 text-gray-500",
  },
}

/* ─── Component ──────────────────────────────────────────────────────────── */

export function JourneyCard({
  title,
  description,
  colorVariant,
  icon: Icon,
  statusLabel,
  statusVariant = "ready",
  className,
}: JourneyCardProps) {
  const { dot, chip } = chipStyles[statusVariant]

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className={cn(
        "relative flex items-start gap-4 rounded-[1.25rem] p-5",
        "shadow-[0_2px_8px_0_rgb(0_0_0/0.06)]",
        "transition-shadow duration-200 hover:shadow-[0_4px_16px_0_rgb(0_0_0/0.10)]",
        cardBg[colorVariant],
        className,
      )}
    >
      {/* Icon circle */}
      <div
        className={cn(
          "flex h-11 w-11 shrink-0 items-center justify-center rounded-full",
          iconBg[colorVariant],
        )}
      >
        <Icon className={cn("h-5 w-5", iconColor[colorVariant])} strokeWidth={1.8} />
      </div>

      {/* Text */}
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <span
          className="leading-snug text-gray-900"
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h3)",
            fontWeight: 500,
          }}
        >
          {title}
        </span>
        <span
          className="text-gray-600"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            lineHeight: 1.5,
          }}
        >
          {description}
        </span>
      </div>

      {/* Status chip */}
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
