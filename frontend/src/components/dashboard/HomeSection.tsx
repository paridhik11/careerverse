import { motion, useReducedMotion } from "framer-motion"
import { ArrowDown } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useJourneyProgress } from "@/contexts/JourneyProgressContext"

const EASE = [0.22, 1, 0.36, 1] as const

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.12, delayChildren: 0.08 } },
}

const fadeUp = {
  hidden: { opacity: 0, y: 18 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.45, ease: EASE } },
}

/**
 * Hero section with Framer Motion staggered fade-in and drifting purple glow blobs.
 * Respects prefers-reduced-motion (blobs freeze via CSS; motion reduced here).
 */
export function HomeSection() {
  const reduceMotion = useReducedMotion()
  const { scrollToSection } = useJourneyProgress()

  return (
    <section
      id="home"
      className="relative isolate min-h-[calc(100vh-var(--cv-navbar-height))] overflow-hidden px-6 py-20 md:py-28"
    >
      {/* Glow blobs near viewport edges */}
      <div className="cv-glow-blob cv-glow-blob--a -left-24 -top-16 size-[28rem]" aria-hidden />
      <div className="cv-glow-blob cv-glow-blob--b -right-20 top-1/4 size-[24rem]" aria-hidden />
      <div className="cv-glow-blob cv-glow-blob--c bottom-0 left-1/3 size-[20rem]" aria-hidden />

      <motion.div
        className="relative mx-auto max-w-3xl"
        variants={stagger}
        initial="hidden"
        animate="visible"
      >
        <motion.p
          variants={fadeUp}
          className="mb-4"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-caption)",
            fontWeight: 700,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            color: "var(--cv-accent)",
          }}
        >
          CareerVerse AI
        </motion.p>

        <motion.h1
          variants={fadeUp}
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-display)",
            fontWeight: 500,
            color: "var(--cv-ink)",
            lineHeight: 1.08,
            letterSpacing: "-0.02em",
          }}
        >
          Experience the role before choosing your future.
        </motion.h1>

        <motion.p
          variants={fadeUp}
          className="mt-6 max-w-xl"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-body)",
            color: "var(--cv-ink-muted)",
            lineHeight: 1.7,
          }}
        >
          Upload your resume, match against real job descriptions, try a virtual
          workday, and leave with a clear 3-month plan — all in one scroll.
        </motion.p>

        <motion.div variants={fadeUp} className="mt-10 flex flex-wrap gap-3">
          <Button
            type="button"
            size="lg"
            className="rounded-full px-8 text-white hover:opacity-90"
            style={{ background: "var(--cv-accent)" }}
            onClick={() => scrollToSection("resume")}
          >
            Start with your resume
            <ArrowDown size={16} strokeWidth={2} aria-hidden />
          </Button>
          <Button
            type="button"
            size="lg"
            variant="outline"
            className="rounded-full border-[var(--cv-border)] bg-white/5 px-8"
            style={{ color: "var(--cv-ink)" }}
            onClick={() => scrollToSection("resume")}
          >
            See how it works
          </Button>
        </motion.div>

        {!reduceMotion && (
          <motion.div
            className="mt-16 flex justify-center"
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
            aria-hidden
          >
            <ArrowDown size={20} strokeWidth={1.6} style={{ color: "var(--cv-ink-muted)" }} />
          </motion.div>
        )}
      </motion.div>
    </section>
  )
}
