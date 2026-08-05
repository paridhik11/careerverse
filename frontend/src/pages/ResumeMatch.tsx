/**
 * ResumeMatchPage — Career Compatibility report (resume vs one selected JD).
 *
 * Data flow:
 *   JobDescriptionUploadPage already calls POST /job-matches/{resumeId}
 *   (generateJobMatches), picks the primary match for the selected JD via
 *   pickPrimaryMatch, then navigates here with ResumeMatchPageState.
 *
 * This page displays that single-JD compatibility result. It does not generate
 * Top 3 Career Explorer rankings — that happens on CareerMatchesPage after
 * the user clicks Continue.
 */

import { useLocation, useNavigate, useParams } from "react-router-dom"
import { motion } from "framer-motion"
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Sparkles,
  XCircle,
} from "lucide-react"

import { ScoreRing } from "@/components/ScoreRing"
import { Button } from "@/components/ui/button"
import type { CareerMatchesState, ResumeMatchPageState } from "@/types"
import { deriveMatchDimensions } from "@/utils/resumeMatch"

const EASE = [0.22, 1, 0.36, 1] as const

function compatibilityLabel(percent: number) {
  if (percent >= 80) return "High Compatibility"
  if (percent >= 60) return "Moderate Compatibility"
  return "Low Compatibility"
}

function MissingState() {
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
          Career compatibility not ready
        </h1>
        <p
          className="mt-3"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            color: "var(--cv-ink-muted)",
            lineHeight: 1.6,
          }}
        >
          Upload a job description first so we can score your resume against that
          role.
        </p>
        <Button
          type="button"
          className="mt-6 w-full text-white hover:opacity-90"
          style={{ background: "var(--cv-accent)" }}
          onClick={() => navigate("/upload-jd")}
        >
          Choose a job description
        </Button>
      </motion.div>
    </div>
  )
}

function DimensionStat({ label, score }: { label: string; score: number }) {
  return (
    <div>
      <p
        style={{
          fontFamily: "var(--cv-font-sans)",
          fontSize: "var(--cv-text-caption)",
          fontWeight: 700,
          letterSpacing: "0.06em",
          textTransform: "uppercase",
          color: "var(--cv-ink-muted)",
        }}
      >
        {label}
      </p>
      <p
        className="mt-1"
        style={{
          fontFamily: "var(--cv-font-serif)",
          fontSize: "var(--cv-text-h2)",
          fontWeight: 400,
          color: "var(--cv-accent)",
          lineHeight: 1.1,
        }}
      >
        {score}%
      </p>
    </div>
  )
}

export function ResumeMatchPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { resumeId: resumeIdParam } = useParams<{ resumeId: string }>()
  const state = location.state as ResumeMatchPageState | null

  if (!state?.primaryMatch || !state.matches?.length) {
    return <MissingState />
  }

  const resumeId = state.resumeId || Number(resumeIdParam)
  if (!Number.isFinite(resumeId) || resumeId <= 0) {
    return <MissingState />
  }

  const { primaryMatch, matches, selectedJdTitle, report } = state
  const roleLabel = selectedJdTitle || primaryMatch.role_title
  const dimensions = deriveMatchDimensions(primaryMatch, report ?? null)
  const strengthText =
    primaryMatch.career_overview?.trim() || primaryMatch.reasoning

  function handleContinue() {
    const nextState: CareerMatchesState = {
      matches,
      resumeId,
      selectedJdTitle: roleLabel,
      primaryMatch,
    }
    navigate(`/career-matches/${resumeId}`, { state: nextState })
  }

  return (
    <div
      className="min-h-screen w-full px-4 py-8 md:px-6"
      style={{ background: "var(--cv-bg)" }}
    >
      <motion.div
        className="mx-auto max-w-3xl space-y-5"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: EASE }}
      >
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="mb-2 flex items-center gap-1.5 rounded-full px-3 py-1.5 transition-colors duration-150 hover:bg-white/5"
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

        <div>
          <p
            className="mb-2"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-caption)",
              fontWeight: 700,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "var(--cv-accent)",
            }}
          >
            Career compatibility
          </p>
          <h1
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize: "var(--cv-text-h1)",
              fontWeight: 400,
              color: "var(--cv-ink)",
              lineHeight: 1.15,
            }}
          >
            How suitable is your resume for {roleLabel}?
          </h1>
          <p
            className="mt-3 max-w-xl"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              color: "var(--cv-ink-muted)",
              lineHeight: 1.6,
            }}
          >
            Your resume was evaluated against this one job description. Career
            Explorer rankings come next — they are separate from this score.
          </p>
        </div>

        {/* Compatibility score */}
        <div className="cv-card px-6 py-8 text-center">
          <p
            className="mb-1"
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize: "var(--cv-text-h2)",
              fontWeight: 400,
              color: "var(--cv-ink)",
            }}
          >
            {roleLabel}
          </p>
          <p
            className="mb-6"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-caption)",
              fontWeight: 700,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "var(--cv-ink-muted)",
            }}
          >
            Resume Compatibility
          </p>
          <div className="flex flex-wrap items-center justify-center gap-8">
            <div className="flex flex-col items-center gap-3">
              <ScoreRing
                score={primaryMatch.match_percent}
                label="Compatibility %"
                color="var(--cv-accent)"
                size={120}
                strokeWidth={10}
              />
              <p
                style={{
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-body)",
                  fontWeight: 600,
                  color: "var(--cv-accent)",
                }}
              >
                {compatibilityLabel(primaryMatch.match_percent)}
              </p>
            </div>
            {report && (
              <ScoreRing
                score={report.ats_score}
                label="ATS Compatibility"
                color="var(--cv-accent)"
                trackColor="var(--cv-accent-soft)"
                size={112}
                strokeWidth={9}
              />
            )}
          </div>
        </div>

        {/* Dimension breakdown */}
        <div className="cv-card grid gap-6 px-6 py-6 sm:grid-cols-3">
          <DimensionStat
            label="Technical Skill Match"
            score={dimensions.technicalSkillMatch}
          />
          <DimensionStat
            label="Experience Match"
            score={dimensions.experienceMatch}
          />
          {dimensions.educationMatch != null ? (
            <DimensionStat
              label="Education Match"
              score={dimensions.educationMatch}
            />
          ) : (
            <div>
              <p
                style={{
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-caption)",
                  fontWeight: 700,
                  letterSpacing: "0.06em",
                  textTransform: "uppercase",
                  color: "var(--cv-ink-muted)",
                }}
              >
                Education Match
              </p>
              <p
                className="mt-2"
                style={{
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-small)",
                  color: "var(--cv-ink-muted)",
                }}
              >
                Not available
              </p>
            </div>
          )}
        </div>

        {/* Strengths + Missing skills */}
        <div className="grid gap-5 md:grid-cols-2">
          <div className="cv-card p-6">
            <span className="cv-badge mb-3">Strengths</span>
            <h3
              className="mb-3 flex items-center gap-2"
              style={{
                fontFamily: "var(--cv-font-serif)",
                fontSize: "var(--cv-text-h3)",
                fontWeight: 500,
                color: "var(--cv-ink)",
              }}
            >
              <CheckCircle2 size={18} style={{ color: "var(--cv-accent)" }} />
              Strengths for this JD
            </h3>
            <p
              style={{
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-small)",
                color: "var(--cv-ink-muted)",
                lineHeight: 1.6,
              }}
            >
              {strengthText}
            </p>
          </div>

          <div className="cv-card p-6">
            <span className="cv-badge mb-3">Gaps</span>
            <h3
              className="mb-3 flex items-center gap-2"
              style={{
                fontFamily: "var(--cv-font-serif)",
                fontSize: "var(--cv-text-h3)",
                fontWeight: 500,
                color: "var(--cv-ink)",
              }}
            >
              <XCircle size={18} style={{ color: "var(--cv-accent)" }} />
              Missing Skills
            </h3>
            {primaryMatch.missing_skills.length > 0 ? (
              <ul className="space-y-2">
                {primaryMatch.missing_skills.map((skill, i) => (
                  <li
                    key={i}
                    style={{
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "var(--cv-text-small)",
                      color: "var(--cv-ink-muted)",
                    }}
                  >
                    {skill}
                  </li>
                ))}
              </ul>
            ) : (
              <p
                style={{
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-small)",
                  color: "var(--cv-ink-muted)",
                }}
              >
                No critical skill gaps identified for this role.
              </p>
            )}
          </div>
        </div>

        {/* Match summary */}
        <div className="cv-card p-6">
          <span className="cv-badge mb-3">Summary</span>
          <h3
            className="mb-3"
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize: "var(--cv-text-h3)",
              fontWeight: 500,
              color: "var(--cv-ink)",
            }}
          >
            Suitability Summary
          </h3>
          <p
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-body)",
              color: "var(--cv-ink-muted)",
              lineHeight: 1.7,
            }}
          >
            {primaryMatch.reasoning}
          </p>
          {report?.summary && (
            <p
              className="mt-4"
              style={{
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-small)",
                color: "var(--cv-ink-muted)",
                lineHeight: 1.65,
              }}
            >
              {report.summary}
            </p>
          )}
        </div>

        <div className="pb-8 pt-2 text-center">
          <Button
            type="button"
            size="lg"
            onClick={handleContinue}
            className="w-full rounded-full text-white hover:opacity-90 sm:w-auto sm:px-10"
            style={{ background: "var(--cv-accent)" }}
          >
            Continue
            <ArrowRight size={16} aria-hidden />
          </Button>
          <p
            className="mt-3"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-caption)",
              color: "var(--cv-ink-muted)",
            }}
          >
            Next: explore top careers ranked from your resume profile
          </p>
        </div>
      </motion.div>
    </div>
  )
}
