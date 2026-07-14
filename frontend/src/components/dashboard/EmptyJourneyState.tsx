/**
 * Clean empty-state panel for unlocked dashboard sections that still need
 * a prior choice (JD, career, etc.). Prefer this over locking the page.
 */

import { motion } from "framer-motion"
import type { ReactNode } from "react"

const EASE = [0.22, 1, 0.36, 1] as const

type EmptyJourneyStateProps = {
  message: string
  children?: ReactNode
}

export function EmptyJourneyState({ message, children }: EmptyJourneyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: EASE }}
      className="cv-card flex flex-col items-center justify-center gap-3 px-6 py-14 text-center"
    >
      <p
        className="max-w-md"
        style={{
          fontFamily: "var(--cv-font-sans)",
          fontSize: "var(--cv-text-body)",
          color: "var(--cv-ink-muted)",
          lineHeight: 1.65,
        }}
      >
        {message}
      </p>
      {children}
    </motion.div>
  )
}
