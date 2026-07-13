import type { ReactNode } from "react"
import { motion, useReducedMotion, type Variants } from "framer-motion"

const EASE = [0.22, 1, 0.36, 1] as const

const cardVariants: Variants = {
  hidden: { opacity: 0, y: 16, scale: 0.98 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.45, ease: EASE },
  },
}

const fieldStagger: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.08, delayChildren: 0.15 },
  },
}

const fieldItem: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: EASE } },
}

/**
 * Shared visual shell for the Login and Signup pages: centered floating card
 * on the app's dark canvas background, branded header, and a footer slot for
 * the "switch between login/signup" link. Card fades + scales in on mount;
 * its contents stagger in right after. Both fall back to a plain opacity
 * fade under prefers-reduced-motion.
 */
export function AuthCard({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string
  subtitle: string
  children: ReactNode
  footer: ReactNode
}) {
  const reduced = useReducedMotion()

  return (
    <div
      className="relative flex min-h-screen w-full items-center justify-center overflow-hidden px-4 py-10"
      style={{ background: "var(--cv-bg)" }}
    >
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
        <div
          className="cv-landing-orb cv-landing-orb--a -left-32 -top-24 size-[24rem]"
          style={reduced ? { animation: "none" } : undefined}
        />
        <div
          className="cv-landing-orb cv-landing-orb--b -right-24 bottom-[-10%] size-[22rem]"
          style={reduced ? { animation: "none" } : undefined}
        />
      </div>

      <motion.div
        initial={reduced ? { opacity: 0 } : "hidden"}
        animate={reduced ? { opacity: 1 } : "visible"}
        variants={reduced ? undefined : cardVariants}
        transition={reduced ? { duration: 0.4, ease: EASE } : undefined}
        className="cv-card relative z-[1] w-full max-w-sm p-8"
      >
        <motion.div
          variants={reduced ? undefined : fieldStagger}
          initial={reduced ? undefined : "hidden"}
          animate={reduced ? undefined : "visible"}
        >
          <motion.div variants={reduced ? undefined : fieldItem} className="mb-6 text-center">
            <span
              style={{
                fontFamily: "var(--cv-font-serif)",
                fontSize: "1.25rem",
                fontWeight: 500,
                color: "var(--cv-ink)",
              }}
            >
              CareerVerse
            </span>
            <span
              className="ml-1 align-super text-[10px] font-semibold tracking-wider"
              style={{ color: "var(--cv-accent-2)", fontFamily: "var(--cv-font-sans)" }}
            >
              AI
            </span>
          </motion.div>

          <motion.h1
            variants={reduced ? undefined : fieldItem}
            className="mb-1 text-center"
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize: "var(--cv-text-h2)",
              fontWeight: 400,
              color: "var(--cv-ink)",
            }}
          >
            {title}
          </motion.h1>
          <motion.p
            variants={reduced ? undefined : fieldItem}
            className="mb-6 text-center"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              color: "var(--cv-ink-muted)",
            }}
          >
            {subtitle}
          </motion.p>

          <motion.div variants={reduced ? undefined : fieldItem}>{children}</motion.div>

          <motion.p
            variants={reduced ? undefined : fieldItem}
            className="mt-6 text-center"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              color: "var(--cv-ink-muted)",
            }}
          >
            {footer}
          </motion.p>
        </motion.div>
      </motion.div>
    </div>
  )
}
