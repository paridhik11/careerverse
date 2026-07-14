/**
 * ResumeAnalysisSection — ATS-only resume review.
 *
 * Shows: ATS score, strengths, weaknesses, feedback, improvement suggestions.
 * Never shows career recommendations or JD selection.
 */

import {
  AlertTriangle,
  BarChart2,
  CheckCircle2,
  Lightbulb,
  Sparkles,
} from "lucide-react"

import { EmptyJourneyState } from "@/components/dashboard/EmptyJourneyState"
import { LockedSection } from "@/components/dashboard/LockedSection"
import { ScoreRing } from "@/components/ScoreRing"
import {
  AccordionContent,
  AccordionItem,
  AccordionRoot,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { useJourneyProgress } from "@/contexts/JourneyProgressContext"

export function ResumeAnalysisSection() {
  const { unlocks, report, fileName, reviewedAt } = useJourneyProgress()

  const locked = !unlocks.resumeAnalysis

  return (
    <LockedSection
      id="resume-analysis"
      title="Resume Analysis"
      locked={locked}
      lockHint="Upload a resume above to unlock Resume Analysis."
      className="px-6 lg:px-10"
    >
      <div className="mx-auto max-w-3xl">
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
          Resume analysis
        </p>
        <h2
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h1)",
            fontWeight: 400,
            color: "var(--cv-ink)",
          }}
        >
          {fileName ?? "Your AI review"}
        </h2>
        <p
          className="mt-3 mb-8 max-w-xl"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            color: "var(--cv-ink-muted)",
            lineHeight: 1.6,
          }}
        >
          ATS score, strengths, weaknesses, and improvement suggestions for your
          resume — nothing else.
        </p>

        {!locked && !report && (
          <EmptyJourneyState message="Upload a resume to see your ATS score and feedback." />
        )}

        {report && (
          <div className="space-y-5">
            <div className="cv-card flex flex-wrap items-center justify-center gap-10 px-6 py-8">
              <ScoreRing
                score={report.overall_score}
                label="Overall"
                color="var(--cv-accent)"
                size={108}
                strokeWidth={9}
              />
              <ScoreRing
                score={report.ats_score}
                label="ATS"
                color="var(--cv-accent)"
                trackColor="var(--cv-accent-soft)"
                size={108}
                strokeWidth={9}
              />
            </div>

            {reviewedAt && (
              <p
                style={{
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-caption)",
                  color: "var(--cv-ink-muted)",
                  textAlign: "center",
                }}
              >
                Reviewed{" "}
                {new Intl.DateTimeFormat("en-US", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                }).format(new Date(reviewedAt))}
              </p>
            )}

            <div className="cv-card p-6">
              <div className="mb-3 flex items-center gap-2">
                <Sparkles size={18} style={{ color: "var(--cv-accent)" }} />
                <h3
                  style={{
                    fontFamily: "var(--cv-font-serif)",
                    fontSize: "var(--cv-text-h3)",
                    fontWeight: 500,
                    color: "var(--cv-ink)",
                  }}
                >
                  Resume feedback
                </h3>
              </div>
              <p
                style={{
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-body)",
                  color: "var(--cv-ink-muted)",
                  lineHeight: 1.7,
                }}
              >
                {report.summary}
              </p>
            </div>

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
                  Strengths
                </h3>
                <ul className="space-y-2">
                  {report.strengths.map((s, i) => (
                    <li
                      key={i}
                      style={{
                        fontFamily: "var(--cv-font-sans)",
                        fontSize: "var(--cv-text-small)",
                        color: "var(--cv-ink-muted)",
                        lineHeight: 1.55,
                      }}
                    >
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="cv-card p-6">
                <span className="cv-badge mb-3">Weaknesses</span>
                <h3
                  className="mb-3 flex items-center gap-2"
                  style={{
                    fontFamily: "var(--cv-font-serif)",
                    fontSize: "var(--cv-text-h3)",
                    fontWeight: 500,
                    color: "var(--cv-ink)",
                  }}
                >
                  <AlertTriangle size={18} style={{ color: "var(--cv-accent)" }} />
                  Weaknesses
                </h3>
                <ul className="space-y-2">
                  {report.weaknesses.map((s, i) => (
                    <li
                      key={i}
                      style={{
                        fontFamily: "var(--cv-font-sans)",
                        fontSize: "var(--cv-text-small)",
                        color: "var(--cv-ink-muted)",
                        lineHeight: 1.55,
                      }}
                    >
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="cv-card p-6">
              <div className="mb-4 flex items-center gap-2">
                <BarChart2 size={18} style={{ color: "var(--cv-accent)" }} />
                <h3
                  style={{
                    fontFamily: "var(--cv-font-serif)",
                    fontSize: "var(--cv-text-h3)",
                    fontWeight: 500,
                    color: "var(--cv-ink)",
                  }}
                >
                  ATS issues
                </h3>
              </div>
              {report.ats_issues.length === 0 ? (
                <p
                  style={{
                    fontFamily: "var(--cv-font-sans)",
                    fontSize: "var(--cv-text-small)",
                    color: "var(--cv-ink-muted)",
                  }}
                >
                  No ATS issues detected — your resume is well-formatted for
                  applicant tracking systems.
                </p>
              ) : (
                <div
                  className="overflow-hidden rounded-xl"
                  style={{ background: "var(--cv-surface-subtle)" }}
                >
                  <AccordionRoot type="single" collapsible>
                    {report.ats_issues.map((issue, i) => (
                      <AccordionItem key={i} value={`ats-${i}`} className="px-4">
                        <AccordionTrigger>
                          <span className="flex items-center gap-2">
                            <span
                              className="flex size-5 shrink-0 items-center justify-center rounded-full text-xs font-bold"
                              style={{
                                background: "var(--cv-accent-soft)",
                                color: "var(--cv-accent)",
                                fontFamily: "var(--cv-font-sans)",
                              }}
                            >
                              {i + 1}
                            </span>
                            {issue.length > 80 ? `${issue.slice(0, 80)}…` : issue}
                          </span>
                        </AccordionTrigger>
                        <AccordionContent>{issue}</AccordionContent>
                      </AccordionItem>
                    ))}
                  </AccordionRoot>
                </div>
              )}
            </div>

            <div className="cv-card p-6">
              <div className="mb-4 flex items-center gap-2">
                <Lightbulb size={18} style={{ color: "var(--cv-accent)" }} />
                <h3
                  style={{
                    fontFamily: "var(--cv-font-serif)",
                    fontSize: "var(--cv-text-h3)",
                    fontWeight: 500,
                    color: "var(--cv-ink)",
                  }}
                >
                  Resume improvement suggestions
                </h3>
              </div>
              {report.suggestions.length === 0 ? (
                <p
                  style={{
                    fontFamily: "var(--cv-font-sans)",
                    fontSize: "var(--cv-text-small)",
                    color: "var(--cv-ink-muted)",
                  }}
                >
                  No additional suggestions — your resume looks strong overall.
                </p>
              ) : (
                <ol className="space-y-3">
                  {report.suggestions.map((tip, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <span
                        className="flex size-6 shrink-0 items-center justify-center rounded-full"
                        style={{
                          background: "var(--cv-accent-soft)",
                          color: "var(--cv-accent)",
                          fontFamily: "var(--cv-font-sans)",
                          fontSize: "var(--cv-text-caption)",
                          fontWeight: 700,
                        }}
                      >
                        {i + 1}
                      </span>
                      <span
                        style={{
                          fontFamily: "var(--cv-font-sans)",
                          fontSize: "var(--cv-text-small)",
                          color: "var(--cv-ink-muted)",
                          lineHeight: 1.55,
                        }}
                      >
                        {tip}
                      </span>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          </div>
        )}
      </div>
    </LockedSection>
  )
}
