/**
 * CareerCompatibilitySection — compare resume against ONE selected Job Description.
 *
 * Upload your own JD OR choose from sample JDs (alphabetical, 4 per row).
 * Runs compatibility analysis only — never generates Top 3 careers.
 */

import { useCallback, useEffect, useRef, useState, type ChangeEvent, type DragEvent } from "react"
import { AnimatePresence, motion } from "framer-motion"
import {
  CheckCircle2,
  FileText,
  Loader2,
  Sparkles,
  Upload,
  XCircle,
} from "lucide-react"

import { EmptyJourneyState } from "@/components/dashboard/EmptyJourneyState"
import { LockedSection } from "@/components/dashboard/LockedSection"
import { ScoreRing } from "@/components/ScoreRing"
import { Button } from "@/components/ui/button"
import { useJourneyProgress, type JdSourceMode } from "@/contexts/JourneyProgressContext"
import { ApiError } from "@/services/api"
import { uploadJobDescriptions } from "@/services/jobDescriptions"
import { generateJobMatches } from "@/services/jobMatches"
import {
  getSampleJobDescriptions,
  seedSampleJobDescriptions,
  type SampleJobDescription,
} from "@/services/sampleJobDescriptions"
import { pickPrimaryMatch } from "@/utils/resumeMatch"

const EASE = [0.22, 1, 0.36, 1] as const
const ACCEPTED = [".pdf", ".txt"]
const MAX_BYTES = 10 * 1024 * 1024

function isAccepted(file: File) {
  const n = file.name.toLowerCase()
  return ACCEPTED.some((ext) => n.endsWith(ext))
}

function compatibilityLabel(percent: number) {
  if (percent >= 80) return "High Compatibility"
  if (percent >= 60) return "Moderate Compatibility"
  return "Low Compatibility"
}

export function CareerCompatibilitySection() {
  const {
    unlocks,
    resumeId,
    primaryMatch,
    selectedJdTitle,
    jdSourceMode,
    setJdSourceMode,
    setCompatibilityReady,
  } = useJourneyProgress()

  const locked = !unlocks.careerCompatibility

  const [samples, setSamples] = useState<SampleJobDescription[]>([])
  const [selectedSampleId, setSelectedSampleId] = useState<string | null>(null)
  const [jdFile, setJdFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [statusMsg, setStatusMsg] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if ((jdSourceMode === "sample" || jdSourceMode === "own") && samples.length === 0) {
      getSampleJobDescriptions()
        .then((list) =>
          setSamples(
            [...list].sort((a, b) =>
              a.role_title.localeCompare(b.role_title, undefined, { sensitivity: "base" }),
            ),
          ),
        )
        .catch(() => {
          if (jdSourceMode === "sample") {
            setError("Could not load sample job descriptions.")
          }
        })
    }
  }, [jdSourceMode, samples.length])

  const setOwnFile = useCallback((file: File | null) => {
    setError(null)
    if (!file) {
      setJdFile(null)
      return
    }
    if (!isAccepted(file)) {
      setError("Only PDF and TXT files are accepted.")
      return
    }
    if (file.size > MAX_BYTES) {
      setError("File must be 10 MB or smaller.")
      return
    }
    setJdFile(file)
  }, [])

  function selectMode(mode: Exclude<JdSourceMode, null>) {
    setJdSourceMode(mode)
    setError(null)
    setStatusMsg(null)
  }

  function selectSample(id: string) {
    setSelectedSampleId((prev) => (prev === id ? null : id))
  }

  async function runCompatibility() {
    if (!resumeId) return
    setBusy(true)
    setError(null)
    setStatusMsg(null)

    try {
      let preferredJobDescriptionIds: number[] = []
      let title = "Selected role"

      if (jdSourceMode === "own") {
        if (!jdFile) {
          setError("Add one job description file.")
          setBusy(false)
          return
        }
        setStatusMsg("Uploading your job description…")
        const uploaded = await uploadJobDescriptions([jdFile])
        preferredJobDescriptionIds = uploaded.uploaded
          .map((item) => Number(item.id))
          .filter((id) => Number.isFinite(id))
        title =
          uploaded.uploaded[0]?.role_title?.trim() ||
          jdFile.name.replace(/\.(pdf|txt)$/i, "") ||
          "Selected role"

        // Seed sample catalog so the existing match agent has enough JD context.
        // Only the selected own JD is shown as the compatibility result.
        let catalog = samples
        if (catalog.length === 0) {
          try {
            catalog = await getSampleJobDescriptions()
            setSamples(
              [...catalog].sort((a, b) =>
                a.role_title.localeCompare(b.role_title, undefined, {
                  sensitivity: "base",
                }),
              ),
            )
          } catch {
            // Own JD alone may still produce a score.
          }
        }
        if (catalog.length > 0) {
          setStatusMsg("Preparing job description context…")
          await seedSampleJobDescriptions(catalog.map((s) => s.id))
        }
      } else if (jdSourceMode === "sample") {
        if (!selectedSampleId) {
          setError("Pick a sample job description.")
          setBusy(false)
          return
        }
        const selected = samples.find((s) => s.id === selectedSampleId)
        if (!selected) {
          setError("Selected sample could not be found.")
          setBusy(false)
          return
        }
        title = selected.role_title
        setStatusMsg(`Evaluating your resume against ${selected.role_title}…`)
        // Seed full catalog for RAG; only the selected JD is used for the report.
        const sampleIds = samples.map((s) => s.id)
        const seeded = await seedSampleJobDescriptions(sampleIds)
        const selectedIndex = sampleIds.indexOf(selectedSampleId)
        const selectedSeed =
          selectedIndex >= 0 ? seeded.uploaded[selectedIndex] : undefined
        if (selectedSeed) {
          const idNum = Number(selectedSeed.id)
          if (Number.isFinite(idNum)) preferredJobDescriptionIds = [idNum]
          if (selectedSeed.role_title?.trim()) {
            title = selectedSeed.role_title.trim()
          }
        }
      } else {
        setError("Choose a job description source first.")
        setBusy(false)
        return
      }

      setStatusMsg("Comparing your resume to this role…")
      const response = await generateJobMatches(resumeId)
      const match = pickPrimaryMatch(response.matches, {
        preferredJobDescriptionIds,
        preferredRoleTitle: title,
      })

      setCompatibilityReady({
        selectedJdTitle: title,
        primaryMatch: match,
      })
      setStatusMsg("Compatibility analysis ready.")
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Something went wrong. Please try again.",
      )
    } finally {
      setBusy(false)
    }
  }

  const roleLabel = selectedJdTitle ?? primaryMatch?.role_title ?? "this role"

  return (
    <LockedSection
      id="career-compatibility"
      title="Career Compatibility"
      locked={locked}
      lockHint="Upload a resume above to unlock Career Compatibility."
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
          Career compatibility
        </p>
        <h2
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h1)",
            fontWeight: 400,
            color: "var(--cv-ink)",
          }}
        >
          How suitable is my resume for this job?
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
          Compare your resume against one job description. This does not generate
          career recommendations.
        </p>

        {!locked && (
          <div className="cv-card mb-6 p-6 sm:p-8">
            <div className="mb-5 flex items-center gap-2">
              <Sparkles size={18} style={{ color: "var(--cv-accent)" }} />
              <h3
                style={{
                  fontFamily: "var(--cv-font-serif)",
                  fontSize: "var(--cv-text-h3)",
                  fontWeight: 500,
                  color: "var(--cv-ink)",
                }}
              >
                Choose a job description
              </h3>
            </div>

            <div
              className="mb-6 flex rounded-full p-1"
              style={{ background: "var(--cv-surface-subtle)" }}
              role="tablist"
              aria-label="Job description source"
            >
              {(
                [
                  { mode: "own" as const, label: "Upload your own JD" },
                  { mode: "sample" as const, label: "Choose from sample Job Descriptions" },
                ] as const
              ).map(({ mode, label }) => {
                const active = jdSourceMode === mode
                return (
                  <button
                    key={mode}
                    type="button"
                    role="tab"
                    aria-selected={active}
                    onClick={() => selectMode(mode)}
                    className="flex-1 rounded-full px-3 py-2.5 transition-colors"
                    style={{
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "var(--cv-text-caption)",
                      fontWeight: 600,
                      background: active ? "var(--cv-accent)" : "transparent",
                      color: active ? "#fff" : "var(--cv-ink-muted)",
                    }}
                  >
                    {label}
                  </button>
                )
              })}
            </div>

            <AnimatePresence mode="wait">
              {jdSourceMode === "own" && (
                <motion.div
                  key="own"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3, ease: EASE }}
                  className="flex flex-col gap-4"
                >
                  <div
                    role="button"
                    tabIndex={0}
                    onClick={() => inputRef.current?.click()}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault()
                        inputRef.current?.click()
                      }
                    }}
                    onDragOver={(e: DragEvent) => {
                      e.preventDefault()
                      setIsDragging(true)
                    }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={(e: DragEvent) => {
                      e.preventDefault()
                      setIsDragging(false)
                      const file = e.dataTransfer.files?.[0] ?? null
                      setOwnFile(file)
                    }}
                    className="flex cursor-pointer flex-col items-center gap-2 rounded-[var(--cv-radius-card)] px-4 py-8 text-center"
                    style={{
                      background: isDragging ? "var(--cv-accent-soft)" : "var(--cv-bg)",
                      border: "1px dashed var(--cv-border)",
                    }}
                  >
                    <div className="cv-icon-circle">
                      <Upload size={22} style={{ color: "var(--cv-accent)" }} />
                    </div>
                    <p
                      style={{
                        fontFamily: "var(--cv-font-sans)",
                        fontWeight: 600,
                        fontSize: "var(--cv-text-small)",
                        color: "var(--cv-ink)",
                      }}
                    >
                      Drop one JD PDF or TXT file
                    </p>
                  </div>
                  <input
                    ref={inputRef}
                    type="file"
                    accept=".pdf,.txt,application/pdf,text/plain"
                    className="sr-only"
                    onChange={(e: ChangeEvent<HTMLInputElement>) => {
                      setOwnFile(e.target.files?.[0] ?? null)
                      e.target.value = ""
                    }}
                  />
                  {jdFile && (
                    <div
                      className="flex items-center gap-2 text-sm"
                      style={{ fontFamily: "var(--cv-font-sans)" }}
                    >
                      <FileText size={16} /> {jdFile.name}
                    </div>
                  )}
                </motion.div>
              )}

              {jdSourceMode === "sample" && (
                <motion.div
                  key="sample"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3, ease: EASE }}
                  className="grid grid-cols-1 gap-3 min-[420px]:grid-cols-2 md:grid-cols-3 xl:grid-cols-4"
                >
                  {samples.map((sample) => {
                    const selected = selectedSampleId === sample.id
                    return (
                      <button
                        key={sample.id}
                        type="button"
                        onClick={() => selectSample(sample.id)}
                        className="cv-card relative overflow-hidden p-5 text-left transition-shadow"
                        style={{
                          outline: selected ? "2px solid var(--cv-accent)" : undefined,
                          background: selected
                            ? "var(--cv-accent-soft)"
                            : "var(--cv-card-surface)",
                        }}
                      >
                        <span className="cv-badge mb-2">{sample.category}</span>
                        <p
                          style={{
                            fontFamily: "var(--cv-font-serif)",
                            fontSize: "var(--cv-text-h3)",
                            fontWeight: 500,
                            color: "var(--cv-ink)",
                          }}
                        >
                          {sample.role_title}
                        </p>
                        <p
                          className="mt-1"
                          style={{
                            fontFamily: "var(--cv-font-sans)",
                            fontSize: "var(--cv-text-caption)",
                            color: "var(--cv-ink-muted)",
                            lineHeight: 1.5,
                          }}
                        >
                          {sample.summary}
                        </p>
                      </button>
                    )
                  })}
                </motion.div>
              )}
            </AnimatePresence>

            {error && (
              <p
                className="mt-4"
                style={{
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-small)",
                  color: "#FCA5A5",
                }}
              >
                {error}
              </p>
            )}
            {statusMsg && (
              <p
                className="mt-4"
                style={{
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-small)",
                  color: "var(--cv-accent)",
                }}
              >
                {statusMsg}
              </p>
            )}

            {jdSourceMode && (
              <Button
                type="button"
                disabled={busy}
                onClick={runCompatibility}
                className="mt-6 w-full rounded-full text-white sm:w-auto sm:px-8"
                style={{ background: "var(--cv-accent)" }}
              >
                {busy ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Sparkles size={16} />
                )}
                Analyze Compatibility
              </Button>
            )}
          </div>
        )}

        {!locked && !primaryMatch && !jdSourceMode && (
          <EmptyJourneyState message="Upload your own JD or choose a sample to see how suitable your resume is for that job." />
        )}

        {primaryMatch && (
          <div className="space-y-5">
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
                  {primaryMatch.career_overview || primaryMatch.reasoning}
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
            </div>
          </div>
        )}
      </div>
    </LockedSection>
  )
}
