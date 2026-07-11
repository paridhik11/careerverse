/**
 * SkillGapPage — placeholder for the next milestone.
 *
 * Receives the chosen career via location.state from VirtualExperiencePage.
 * Displays the chosen career name and a "coming soon" message while the
 * Skill Gap Agent milestone is in development.
 */

import { useLocation, useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { BarChart2, CheckCircle2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import type { JobMatch } from "@/types"

const EASE = [0.22, 1, 0.36, 1] as const

const sectionVariants = {
  hidden: { opacity: 0, y: 14 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: EASE },
  },
}

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.1, delayChildren: 0.05 },
  },
}

interface SkillGapState {
  match?: JobMatch
  resumeId?: number
}

export function SkillGapPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as SkillGapState | null
  const match = state?.match

  return (
    <div
      className="min-h-screen w-full px-4 py-12 md:px-6"
      style={{ background: "var(--cv-bg)" }}
    >
      <motion.div
        className="mx-auto max-w-2xl"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Chosen career confirmation */}
        {match && (
          <motion.div
            variants={sectionVariants}
            className="mb-6 flex items-center gap-3 rounded-[var(--cv-radius-card)] p-4"
            style={{ background: "var(--cv-card-sage)", boxShadow: "var(--cv-shadow-card)" }}
          >
            <CheckCircle2 size={20} strokeWidth={2} style={{ color: "#22C55E", flexShrink: 0 }} aria-hidden />
            <div>
              <p
                style={{
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-caption)",
                  fontWeight: 700,
                  color: "#166534",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                }}
              >
                Career chosen
              </p>
              <p
                style={{
                  fontFamily: "var(--cv-font-serif)",
                  fontSize: "var(--cv-text-h3)",
                  fontWeight: 500,
                  color: "#111827",
                }}
              >
                {match.role_title}
              </p>
            </div>
          </motion.div>
        )}

        {/* Main card */}
        <motion.div
          variants={sectionVariants}
          className="rounded-[var(--cv-radius-main)] bg-white p-8 text-center"
          style={{ boxShadow: "var(--cv-shadow-main)" }}
        >
          <div
            className="mx-auto mb-5 flex size-16 items-center justify-center rounded-full"
            style={{ background: "var(--cv-card-sky-icon)" }}
            aria-hidden
          >
            <BarChart2 size={28} strokeWidth={1.6} color="#111827" />
          </div>

          <h1
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize: "var(--cv-text-h1)",
              fontWeight: 400,
              color: "#111827",
              lineHeight: 1.15,
            }}
          >
            Skill Gap Analysis
          </h1>

          <p
            className="mx-auto mt-3 max-w-md text-gray-500"
            style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-body)", lineHeight: 1.7 }}
          >
            {match
              ? `We'll analyze the gap between your current skills and what ${match.role_title} requires — then build a personalized 3-month roadmap to close it.`
              : "Your personalized skill gap analysis and 3-month learning roadmap are being prepared."}
          </p>

          <div
            className="mx-auto mt-6 w-fit rounded-full px-4 py-2"
            style={{
              background: "var(--cv-card-sky)",
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              fontWeight: 600,
              color: "#0369A1",
            }}
          >
            Coming in the next milestone
          </div>

          {/* What's coming */}
          <div
            className="mt-8 rounded-[var(--cv-radius-card)] p-5 text-left"
            style={{ background: "var(--cv-bg)" }}
          >
            <p
              className="mb-3"
              style={{
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-caption)",
                fontWeight: 700,
                color: "#6B7280",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
              }}
            >
              What's next
            </p>
            <ul className="flex flex-col gap-2.5">
              {[
                "Technical skills gap analysis vs. your chosen role",
                "Soft skills assessment based on simulation performance",
                "Personalized 3-month learning roadmap",
                "Curated resources for each missing skill",
                "Interview preparation for your target role",
              ].map((item, i) => (
                <li key={i} className="flex items-center gap-2.5">
                  <span
                    className="flex size-5 shrink-0 items-center justify-center rounded-full"
                    style={{ background: "var(--cv-accent-muted)" }}
                    aria-hidden
                  >
                    <span
                      style={{
                        fontFamily: "var(--cv-font-sans)",
                        fontSize: "0.625rem",
                        fontWeight: 700,
                        color: "var(--cv-accent)",
                      }}
                    >
                      {i + 1}
                    </span>
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "var(--cv-text-small)",
                      color: "#374151",
                    }}
                  >
                    {item}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          <Button
            type="button"
            variant="outline"
            className="mt-6"
            onClick={() => navigate("/dashboard")}
          >
            Go to Dashboard
          </Button>
        </motion.div>
      </motion.div>
    </div>
  )
}
