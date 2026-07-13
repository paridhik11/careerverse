/**
 * ResumeReportSection — AI score, strengths, gaps + inline JD choice.
 *
 * Segmented control at the bottom:
 *   "Upload your own job description" | "Use sample job descriptions"
 * Own → inline JD dropzone → upload → generate matches → unlock Career Match
 * Sample → picker of seeded fixture JDs → seed + match → unlock Career Match
 */

import { useCallback, useEffect, useRef, useState, type ChangeEvent, type DragEvent } from "react"
import { AnimatePresence, motion } from "framer-motion"
import {
  AlertTriangle,
  CheckCircle2,
  FileText,
  Loader2,
  Sparkles,
  Upload,
} from "lucide-react"

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

const EASE = [0.22, 1, 0.36, 1] as const
const ACCEPTED = [".pdf", ".txt"]
const MAX_BYTES = 10 * 1024 * 1024
const MAX_FILES = 5

function isAccepted(file: File) {
  const n = file.name.toLowerCase()
  return ACCEPTED.some((ext) => n.endsWith(ext))
}

export function ResumeReportSection() {
  const {
    unlocks,
    report,
    fileName,
    resumeId,
    jdSourceMode,
    setJdSourceMode,
    setMatchesReady,
    scrollToSection,
  } = useJourneyProgress()

  const locked = !unlocks.resumeReport

  const [samples, setSamples] = useState<SampleJobDescription[]>([])
  const [selectedSampleIds, setSelectedSampleIds] = useState<string[]>([])
  const [jdFiles, setJdFiles] = useState<File[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [statusMsg, setStatusMsg] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (jdSourceMode === "sample" && samples.length === 0) {
      getSampleJobDescriptions()
        .then(setSamples)
        .catch(() => setError("Could not load sample job descriptions."))
    }
  }, [jdSourceMode, samples.length])

  const addFiles = useCallback((incoming: File[]) => {
    setError(null)
    setJdFiles((prev) => {
      const next = [...prev]
      for (const file of incoming) {
        if (!isAccepted(file)) {
          setError("Only PDF and TXT files are accepted.")
          continue
        }
        if (file.size > MAX_BYTES) {
          setError("Each file must be 10 MB or smaller.")
          continue
        }
        if (!next.some((f) => f.name === file.name && f.size === file.size)) {
          next.push(file)
        }
      }
      return next.slice(0, MAX_FILES)
    })
  }, [])

  function selectMode(mode: Exclude<JdSourceMode, null>) {
    setJdSourceMode(mode)
    setError(null)
    setStatusMsg(null)
  }

  function toggleSample(id: string) {
    setSelectedSampleIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id].slice(0, 4),
    )
  }

  async function confirmJdAndMatch() {
    if (!resumeId) return
    setBusy(true)
    setError(null)
    setStatusMsg(null)

    try {
      if (jdSourceMode === "own") {
        if (jdFiles.length === 0) {
          setError("Add at least one job description file.")
          setBusy(false)
          return
        }
        setStatusMsg("Uploading job descriptions…")
        await uploadJobDescriptions(jdFiles)
      } else if (jdSourceMode === "sample") {
        if (selectedSampleIds.length === 0) {
          setError("Pick at least one sample job description.")
          setBusy(false)
          return
        }
        setStatusMsg("Seeding sample job descriptions…")
        await seedSampleJobDescriptions(selectedSampleIds)
      } else {
        setError("Choose a job description source first.")
        setBusy(false)
        return
      }

      setStatusMsg("Finding your top career matches…")
      const response = await generateJobMatches(resumeId)
      setMatchesReady(response.matches)
      setStatusMsg("Career Match unlocked.")
      setTimeout(() => scrollToSection("career-match"), 350)
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

  return (
    <LockedSection
      id="resume-report"
      title="Resume Report"
      locked={locked}
      lockHint="Upload and analyze a resume above to unlock this report."
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
          Resume report
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

        {report && (
          <div className="mt-8 space-y-5">
            <div className="cv-card flex flex-wrap items-center justify-center gap-10 px-6 py-8">
              <ScoreRing score={report.overall_score} label="Overall" color="var(--cv-accent)" size={108} strokeWidth={9} />
              <ScoreRing score={report.ats_score} label="ATS" color="var(--cv-accent)" trackColor="var(--cv-accent-soft)" size={108} strokeWidth={9} />
            </div>

            <p
              className="cv-card p-6"
              style={{
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-body)",
                color: "var(--cv-ink-muted)",
                lineHeight: 1.7,
              }}
            >
              {report.summary}
            </p>

            <div className="grid gap-5 md:grid-cols-2">
              <div className="cv-card p-6">
                <span className="cv-badge mb-3">Strengths</span>
                <h3 className="mb-3 flex items-center gap-2" style={{ fontFamily: "var(--cv-font-serif)", fontSize: "var(--cv-text-h3)", fontWeight: 500, color: "var(--cv-ink)" }}>
                  <CheckCircle2 size={18} style={{ color: "var(--cv-accent)" }} /> Strengths
                </h3>
                <ul className="space-y-2">
                  {report.strengths.map((s, i) => (
                    <li key={i} style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "var(--cv-ink-muted)" }}>
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="cv-card p-6">
                <span className="cv-badge mb-3">Gaps</span>
                <h3 className="mb-3 flex items-center gap-2" style={{ fontFamily: "var(--cv-font-serif)", fontSize: "var(--cv-text-h3)", fontWeight: 500, color: "var(--cv-ink)" }}>
                  <AlertTriangle size={18} style={{ color: "var(--cv-accent)" }} /> Gaps
                </h3>
                <ul className="space-y-2">
                  {report.weaknesses.map((s, i) => (
                    <li key={i} style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "var(--cv-ink-muted)" }}>
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* ── Inline JD choice — unlocks Career Match ── */}
            <div className="cv-card p-6 sm:p-8">
              <div className="mb-5 flex items-center gap-2">
                <Sparkles size={18} style={{ color: "var(--cv-accent)" }} />
                <h3 style={{ fontFamily: "var(--cv-font-serif)", fontSize: "var(--cv-text-h3)", fontWeight: 500, color: "var(--cv-ink)" }}>
                  Choose job descriptions
                </h3>
              </div>
              <p className="mb-5" style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "var(--cv-ink-muted)", lineHeight: 1.6 }}>
                Career Match stays locked until you pick a JD source here — upload your own, or use our seeded samples.
              </p>

              {/* Segmented control */}
              <div
                className="mb-6 flex rounded-full p-1"
                style={{ background: "var(--cv-surface-subtle)" }}
                role="tablist"
                aria-label="Job description source"
              >
                {(
                  [
                    { mode: "own" as const, label: "Upload your own job description" },
                    { mode: "sample" as const, label: "Use sample job descriptions" },
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
                        addFiles(Array.from(e.dataTransfer.files ?? []))
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
                      <p style={{ fontFamily: "var(--cv-font-sans)", fontWeight: 600, fontSize: "var(--cv-text-small)", color: "var(--cv-ink)" }}>
                        Drop JD PDFs or TXT files
                      </p>
                    </div>
                    <input
                      ref={inputRef}
                      type="file"
                      multiple
                      accept=".pdf,.txt,application/pdf,text/plain"
                      className="sr-only"
                      onChange={(e: ChangeEvent<HTMLInputElement>) => {
                        addFiles(Array.from(e.target.files ?? []))
                        e.target.value = ""
                      }}
                    />
                    {jdFiles.map((f, i) => (
                      <div key={`${f.name}-${i}`} className="flex items-center gap-2 text-sm" style={{ fontFamily: "var(--cv-font-sans)" }}>
                        <FileText size={16} /> {f.name}
                      </div>
                    ))}
                  </motion.div>
                )}

                {jdSourceMode === "sample" && (
                  <motion.div
                    key="sample"
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.3, ease: EASE }}
                    className="grid gap-3 sm:grid-cols-2"
                  >
                    {samples.map((sample) => {
                      const selected = selectedSampleIds.includes(sample.id)
                      return (
                        <button
                          key={sample.id}
                          type="button"
                          onClick={() => toggleSample(sample.id)}
                          className="cv-card relative overflow-hidden p-5 text-left transition-shadow"
                          style={{
                            outline: selected ? "2px solid var(--cv-accent)" : undefined,
                            background: selected ? "var(--cv-accent-soft)" : "var(--cv-card-surface)",
                          }}
                        >
                          <span className="cv-badge mb-2">{sample.category}</span>
                          <p style={{ fontFamily: "var(--cv-font-serif)", fontSize: "var(--cv-text-h3)", fontWeight: 500, color: "var(--cv-ink)" }}>
                            {sample.role_title}
                          </p>
                          <p className="mt-1" style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-caption)", color: "var(--cv-ink-muted)", lineHeight: 1.5 }}>
                            {sample.summary}
                          </p>
                        </button>
                      )
                    })}
                  </motion.div>
                )}
              </AnimatePresence>

              {error && (
                <p className="mt-4" style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "#FCA5A5" }}>
                  {error}
                </p>
              )}
              {statusMsg && (
                <p className="mt-4" style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "var(--cv-accent)" }}>
                  {statusMsg}
                </p>
              )}

              {jdSourceMode && (
                <Button
                  type="button"
                  disabled={busy}
                  onClick={confirmJdAndMatch}
                  className="mt-6 w-full rounded-full text-white sm:w-auto sm:px-8"
                  style={{ background: "var(--cv-accent)" }}
                >
                  {busy ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
                  Unlock Career Match
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </LockedSection>
  )
}
