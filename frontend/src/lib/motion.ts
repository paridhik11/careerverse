/**
 * Framer Motion presets for consistent animations across the app.
 * Easing matches DESIGN_SYSTEM.md expo-out: cubic-bezier(0.22, 1, 0.36, 1).
 */

export const EASE = [0.22, 1, 0.36, 1] as const

export const fadeInUp = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, ease: EASE },
} as const

export const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  transition: { duration: 0.3, ease: EASE },
} as const

/** Scroll-triggered section / card reveal — pair with whileInView. */
export const scrollReveal = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-80px" },
  transition: { duration: 0.45, ease: EASE },
} as const
