/**
 * CareerMatchesPage — displays the Top 3 career matches as premium animated cards.
 *
 * Rankings are the Career Recommendation Agent's natural order from the resume
 * skill profile. The JD selected for the Resume Match Report is not injected
 * into Rank 1 and is not required to appear in this list.
 *
 * Cards are informational only. Start Experience / Choose Career live on the
 * dashboard Virtual Experience section.
 *
 * Data flow:
 *   JobDescriptionUploadPage / ResumeMatchPage navigates here with
 *   `CareerMatchesState` in location.state: { matches, resumeId, ... }.
 */

import { useLocation, useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { ArrowLeft, Sparkles } from "lucide-react"

import { CareerCard } from "@/components/CareerCard"
import { Button } from "@/components/ui/button"
import type { CareerMatchesState } from "@/types"
import { getCareerRecommendationMatches } from "@/utils/resumeMatch"

const EASE = [0.22, 1, 0.36, 1] as const

/* ─── Missing state ─────────────────────────────────────────────────────── */

function MissingMatchesState() {
  const navigate = useNavigate()
  return (
    <div
      className="flex min-h-screen w-full items-center justify-center px-4 py-10"
      style={{ background: "var(--cv-bg)" }}
    >
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: EASE }}
        className="w-full max-w-md rounded-[var(--cv-radius-main)] bg-[var(--cv-card-surface)] p-8 text-center"
        style={{ boxShadow: "var(--cv-shadow-main)" }}
      >
        <div
          className="mx-auto mb-4 flex size-14 items-center justify-center rounded-full"
          style={{ background: "var(--cv-accent-soft)" }}
          aria-hidden
        >
          <Sparkles size={24} strokeWidth={1.6} color="var(--cv-accent)" />
        </div>
        <h1
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h2)",
            fontWeight: 400,
            color: "var(--cv-ink)",
            lineHeight: 1.2,
          }}
        >
          No careers to explore yet
        </h1>
        <p
          className="mt-3"
          style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", lineHeight: 1.6, color: "var(--cv-ink-muted)" }}
        >
          Select a job description to discover the careers that best fit your resume.
        </p>
        <Button
          type="button"
          className="mt-6 w-full text-white hover:opacity-90"
          style={{ background: "var(--cv-accent)" }}
          onClick={() => navigate("/resume/upload")}
        >
          Start over
        </Button>
      </motion.div>
    </div>
  )
}

/* ─── Main page ─────────────────────────────────────────────────────────── */

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.1, delayChildren: 0.1 },
  },
}

export function CareerMatchesPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as CareerMatchesState | null

  if (!state?.matches || state.matches.length === 0) {
    return <MissingMatchesState />
  }

  const { matches } = state
  const displayMatches = getCareerRecommendationMatches(matches)

  return (
    <div
      className="relative min-h-screen w-full px-4 py-8 md:px-6"
      style={{ background: "var(--cv-bg)" }}
    >
      <motion.div
        className="mx-auto max-w-3xl"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Back navigation */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: EASE }}
          className="mb-6"
        >
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="flex items-center gap-1.5 rounded-full px-3 py-1.5 transition-colors duration-150 hover:bg-white/5"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              fontWeight: 500,
              color: "var(--cv-ink-muted)",
            }}
          >
            <ArrowLeft size={15} strokeWidth={2} aria-hidden />
            Back
          </button>
        </motion.div>

        {/* Page header */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: EASE }}
          className="mb-8 text-center"
        >
          <div
            className="mx-auto mb-4 flex size-12 items-center justify-center rounded-full"
            style={{ background: "var(--cv-accent-soft)" }}
            aria-hidden
          >
            <Sparkles size={22} strokeWidth={1.8} color="var(--cv-accent)" />
          </div>
          <h1
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize: "var(--cv-text-h1)",
              fontWeight: 400,
              color: "var(--cv-ink)",
              lineHeight: 1.15,
            }}
          >
            Top careers for your profile
          </h1>
          <p
            className="mx-auto mt-3 max-w-2xl"
            style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", lineHeight: 1.7, color: "var(--cv-ink-muted)" }}
          >
            Ranked from your resume and overall skill profile — not from the job description
            you evaluated earlier. Review your matches, then try a day in the role from Virtual Experience.
          </p>
        </motion.div>

        {/* Career cards */}
        <motion.div
          variants={containerVariants}
          className="flex flex-col gap-5"
        >
          {displayMatches.map((match) => (
            <CareerCard
              key={match.id}
              match={match}
              displayRank={match.displayRank}
            />
          ))}
        </motion.div>

        {/* Footer action */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.5, ease: EASE }}
          className="mt-8 pb-4 text-center"
        >
          <p
            className="mb-3"
            style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "var(--cv-ink-muted)" }}
          >
            Not happy with these matches?
          </p>
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate("/resume/upload")}
          >
            Analyze a different resume
          </Button>
        </motion.div>
      </motion.div>
    </div>
  )
}
