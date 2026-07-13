import { Lock } from "lucide-react"
import { motion } from "framer-motion"
import type { ReactNode } from "react"

const EASE = [0.22, 1, 0.36, 1] as const

type LockedSectionProps = {
  id: string
  title: string
  locked: boolean
  lockHint?: string
  children: ReactNode
  className?: string
}

/**
 * Dims and overlays a lock when the section's prerequisite isn't met.
 * Unlocked sections still fade in via whileInView.
 */
export function LockedSection({
  id,
  title,
  locked,
  lockHint = "Complete the previous step to unlock",
  children,
  className = "",
}: LockedSectionProps) {
  return (
    <section
      id={id}
      aria-label={title}
      aria-disabled={locked}
      className={`relative scroll-mt-[calc(var(--cv-navbar-height)+1.5rem)] py-16 md:py-24 ${className}`}
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.45, ease: EASE }}
        className={locked ? "pointer-events-none select-none" : undefined}
        style={locked ? { filter: "grayscale(0.85)", opacity: 0.45 } : undefined}
      >
        {children}
      </motion.div>

      {locked && (
        <div
          className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 rounded-[var(--cv-radius-main)]"
          style={{ background: "rgba(11,10,20,0.75)", backdropFilter: "blur(2px)" }}
        >
          <div className="cv-icon-circle size-14">
            <Lock size={22} strokeWidth={1.8} style={{ color: "var(--cv-accent)" }} aria-hidden />
          </div>
          <p
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize: "var(--cv-text-h3)",
              fontWeight: 500,
              color: "var(--cv-ink)",
            }}
          >
            {title} locked
          </p>
          <p
            className="max-w-xs text-center"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              color: "var(--cv-ink-muted)",
            }}
          >
            {lockHint}
          </p>
        </div>
      )}
    </section>
  )
}
