/**
 * JobDescriptionUploadPage — continues the flow from ResumeReportPage.
 *
 * User flow:
 *   1. Arrive here from the Resume Report's "Upload Job Descriptions" CTA,
 *      carrying `resumeId` via location.state (see `JobDescriptionUploadState`).
 *   2. Select one or more PDF/TXT job descriptions (drag-and-drop or click-to-browse).
 *   3. Click "Find My Career Matches" → POST /job-descriptions/upload, then
 *      POST /job-matches/{resumeId}.
 *   4. Display the Top 3 career matches returned by the Career Recommendation
 *      Agent as simple, on-brand result cards.
 *
 * State machine mirrors UploadResumePage: idle → uploading → matching → done | error.
 */

import { useCallback, useRef, useState, type ChangeEvent, type DragEvent } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { AnimatePresence, motion } from "framer-motion"
import {
  AlertCircle,
  Briefcase,
  FileText,
  RotateCcw,
  Sparkles,
  Trash2,
  Upload,
} from "lucide-react"

import { FormErrorBanner } from "@/components/FormErrorBanner"
import { Button } from "@/components/ui/button"
import { uploadJobDescriptions } from "@/services/jobDescriptions"
import { generateJobMatches } from "@/services/jobMatches"
import { ApiError } from "@/services/api"
import type { JobDescriptionUploadState, JobMatch } from "@/types"

/* ─── Constants ─────────────────────────────────────────────────────────── */

const ACCEPTED_EXTENSIONS = [".pdf", ".txt"]
const MAX_BYTES = 10 * 1024 * 1024
const MAX_FILES = 5
const EASE = [0.22, 1, 0.36, 1] as const

type Phase = "idle" | "uploading" | "matching" | "done" | "error"

const STEPS: Array<{ phase: Phase; label: string; description: string }> = [
  { phase: "uploading", label: "Uploading Job Descriptions", description: "Extracting text and indexing for retrieval…" },
  { phase: "matching", label: "Finding Your Matches", description: "GPT-4o is comparing your resume against real job postings…" },
]

const ACTIVE_STEP_INDEX: Record<Phase, number> = {
  idle: -1,
  uploading: 0,
  matching: 1,
  done: -1,
  error: -1,
}

const CONFIDENCE_STYLES: Record<JobMatch["confidence_score"], { bg: string; text: string }> = {
  High: { bg: "rgba(34, 197, 94, 0.16)", text: "#4ADE80" },
  Medium: { bg: "rgba(251, 191, 36, 0.16)", text: "#FBBF24" },
  Low: { bg: "var(--cv-surface-subtle)", text: "var(--cv-ink-muted)" },
}

/* ─── Helpers ───────────────────────────────────────────────────────────── */

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function isAcceptedFile(file: File): boolean {
  const lowerName = file.name.toLowerCase()
  return ACCEPTED_EXTENSIONS.some((ext) => lowerName.endsWith(ext))
}

function phaseErrorHeading(phase: Phase): string {
  switch (phase) {
    case "uploading":
      return "Upload failed"
    case "matching":
      return "Could not generate matches"
    default:
      return "Something went wrong"
  }
}

/* ─── Sub-components ────────────────────────────────────────────────────── */

function PulsingDot() {
  return (
    <span className="relative flex size-2.5">
      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#6B7FFF] opacity-60" />
      <span className="relative inline-flex size-2.5 rounded-full bg-[#6B7FFF]" />
    </span>
  )
}

function ProcessingPanel({ phase }: { phase: Phase }) {
  const activeIdx = ACTIVE_STEP_INDEX[phase]

  return (
    <motion.div
      key="processing"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      transition={{ duration: 0.35, ease: EASE }}
      className="flex flex-col gap-6 py-2"
    >
      <div className="h-1 w-full overflow-hidden rounded-full" style={{ background: "var(--cv-surface-subtle)" }}>
        <motion.div
          className="h-full rounded-full bg-[#6B7FFF]"
          initial={{ width: "0%" }}
          animate={{ width: `${((activeIdx + 1) / STEPS.length) * 100}%` }}
          transition={{ duration: 0.6, ease: EASE }}
        />
      </div>

      <div className="flex flex-col gap-4">
        {STEPS.map((step, idx) => {
          const isDone = idx < activeIdx
          const isActive = idx === activeIdx
          const isPending = idx > activeIdx

          return (
            <div key={step.phase} className="flex items-start gap-3">
              <div className="mt-0.5 flex size-5 shrink-0 items-center justify-center">
                {isDone ? (
                  <svg viewBox="0 0 20 20" fill="none" className="size-5" aria-hidden>
                    <circle cx="10" cy="10" r="10" fill="var(--cv-accent-muted)" />
                    <path d="M6 10l3 3 5-5" stroke="var(--cv-accent)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                ) : isActive ? (
                  <PulsingDot />
                ) : (
                  <span className="flex size-5 items-center justify-center rounded-full border-2" style={{ borderColor: "var(--cv-border)" }} aria-hidden />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <p
                  style={{
                    fontFamily: "var(--cv-font-sans)",
                    fontSize: "var(--cv-text-small)",
                    fontWeight: isActive ? 700 : isPending ? 400 : 500,
                    color: isActive ? "var(--cv-ink)" : "var(--cv-ink-muted)",
                    lineHeight: 1.4,
                  }}
                >
                  {step.label}
                </p>
                {isActive && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.3 }}
                    style={{
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "var(--cv-text-caption)",
                      color: "var(--cv-ink-muted)",
                      marginTop: "2px",
                    }}
                  >
                    {step.description}
                  </motion.p>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <p
        className="text-center"
        style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-caption)", color: "var(--cv-ink-muted)" }}
      >
        This may take up to 30 seconds — please don't close this tab.
      </p>
    </motion.div>
  )
}

/** One Top-3 career match result card. */
function JobMatchCard({ match }: { match: JobMatch }) {
  const confidence = CONFIDENCE_STYLES[match.confidence_score]

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: (match.rank - 1) * 0.07, ease: EASE }}
      className="rounded-[var(--cv-radius-card)] p-5"
      style={{ background: "var(--cv-card-surface)", boxShadow: "var(--cv-shadow-card)" }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span
            className="flex size-9 shrink-0 items-center justify-center rounded-full"
            style={{
              background: "var(--cv-accent-soft)",
              fontFamily: "var(--cv-font-serif)",
              fontSize: "var(--cv-text-h3)",
              fontWeight: 500,
              color: "var(--cv-accent)",
            }}
            aria-hidden
          >
            {match.rank}
          </span>
          <div>
            <h3
              style={{
                fontFamily: "var(--cv-font-serif)",
                fontSize: "var(--cv-text-h3)",
                fontWeight: 500,
                color: "var(--cv-ink)",
                lineHeight: 1.25,
              }}
            >
              {match.role_title}
            </h3>
            <span
              className="mt-0.5 inline-flex rounded-full px-2.5 py-0.5"
              style={{
                background: confidence.bg,
                color: confidence.text,
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-caption)",
                fontWeight: 600,
              }}
            >
              {match.confidence_score} confidence
            </span>
          </div>
        </div>

        <div className="shrink-0 text-right">
          <span
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize: "var(--cv-text-h2)",
              fontWeight: 400,
              color: "var(--cv-accent)",
            }}
          >
            {match.match_percent}%
          </span>
          <p
            style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-caption)", color: "var(--cv-ink-muted)" }}
          >
            match
          </p>
        </div>
      </div>

      <p
        className="mt-4"
        style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", lineHeight: 1.6, color: "var(--cv-ink-muted)" }}
      >
        {match.career_overview}
      </p>

      <p
        className="mt-3"
        style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", lineHeight: 1.6, color: "var(--cv-ink-muted)" }}
      >
        {match.reasoning}
      </p>

      {match.missing_skills.length > 0 && (
        <div className="mt-4">
          <p
            className="mb-2"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-caption)",
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              color: "var(--cv-ink-muted)",
            }}
          >
            Missing skills for this role
          </p>
          <div className="flex flex-wrap gap-2">
            {match.missing_skills.map((skill, i) => (
              <span
                key={i}
                className="rounded-full px-3 py-1"
                style={{
                  background: "var(--cv-surface-subtle)",
                  color: "var(--cv-ink)",
                  fontFamily: "var(--cv-font-sans)",
                  fontSize: "var(--cv-text-caption)",
                  fontWeight: 500,
                }}
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  )
}

/* ─── Missing-state (no resumeId in location.state) ─────────────────────── */

function MissingResumeState() {
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
          <Briefcase size={24} strokeWidth={1.6} color="var(--cv-accent)" />
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
          Analyze a resume first
        </h1>
        <p
          className="mt-3"
          style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", lineHeight: 1.6, color: "var(--cv-ink-muted)" }}
        >
          Career matches are compared against a specific resume. Please
          analyze your resume first, then continue to job descriptions from
          your report.
        </p>
        <Button
          type="button"
          className="mt-6 w-full text-white hover:opacity-90"
          style={{ background: "var(--cv-accent)" }}
          onClick={() => navigate("/resume/upload")}
        >
          Upload Resume
        </Button>
      </motion.div>
    </div>
  )
}

/* ─── Main page ─────────────────────────────────────────────────────────── */

export function JobDescriptionUploadPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as JobDescriptionUploadState | null
  const inputRef = useRef<HTMLInputElement>(null)

  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [phase, setPhase] = useState<Phase>("idle")
  const [errorPhase, setErrorPhase] = useState<Phase>("idle")
  const [matches, setMatches] = useState<JobMatch[]>([])

  if (!state?.resumeId) {
    return <MissingResumeState />
  }

  const resumeId = state.resumeId

  /* ── File selection ─────────────────────────────────────────────────── */

  const addFiles = useCallback((incoming: File[]) => {
    setFormError(null)
    if (incoming.length === 0) return

    setSelectedFiles((prev) => {
      const combined = [...prev]
      for (const file of incoming) {
        if (!isAcceptedFile(file)) {
          setFormError("Only PDF and TXT files are accepted.")
          continue
        }
        if (file.size > MAX_BYTES) {
          setFormError("Each job description must be 10 MB or smaller.")
          continue
        }
        if (combined.some((existing) => existing.name === file.name && existing.size === file.size)) {
          continue
        }
        combined.push(file)
      }
      if (combined.length > MAX_FILES) {
        setFormError(`You can upload up to ${MAX_FILES} job descriptions at a time.`)
        return combined.slice(0, MAX_FILES)
      }
      return combined
    })
  }, [])

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    addFiles(Array.from(event.target.files ?? []))
    event.target.value = ""
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    event.stopPropagation()
    setIsDragging(true)
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    event.stopPropagation()
    setIsDragging(false)
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    event.stopPropagation()
    setIsDragging(false)
    addFiles(Array.from(event.dataTransfer.files ?? []))
  }

  function handleRemove(index: number) {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index))
  }

  /* ── Main flow ──────────────────────────────────────────────────────── */

  async function handleFindMatches() {
    if (selectedFiles.length === 0) return

    setFormError(null)

    try {
      setPhase("uploading")
      await uploadJobDescriptions(selectedFiles)

      setPhase("matching")
      const response = await generateJobMatches(resumeId)

      setMatches(response.matches)
      setPhase("done")
      navigate(`/career-matches/${resumeId}`, {
        state: { matches: response.matches, resumeId },
      })
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : error instanceof Error
            ? error.message
            : "An unexpected error occurred. Please try again."
      setErrorPhase(phase)
      setFormError(message)
      setPhase("error")
    }
  }

  function handleRetry() {
    setFormError(null)
    setPhase("idle")
  }

  const isProcessing = phase === "uploading" || phase === "matching"

  /* ── Render: results view ──────────────────────────────────────────── */

  if (phase === "done" && matches.length > 0) {
    const sortedMatches = [...matches].sort((a, b) => a.rank - b.rank)

    return (
      <div className="min-h-screen w-full px-4 py-8 md:px-6" style={{ background: "var(--cv-bg)" }}>
        <motion.div
          className="mx-auto max-w-3xl space-y-5"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: EASE }}
        >
          <div className="text-center">
            <div
              className="mx-auto mb-4 flex size-11 items-center justify-center rounded-full"
              style={{ background: "var(--cv-accent-soft)" }}
              aria-hidden
            >
              <Sparkles size={20} strokeWidth={1.8} color="var(--cv-accent)" />
            </div>
            <h1
              style={{
                fontFamily: "var(--cv-font-serif)",
                fontSize: "var(--cv-text-h1)",
                fontWeight: 400,
                color: "var(--cv-ink)",
                lineHeight: 1.2,
              }}
            >
              Your Top 3 career matches
            </h1>
            <p
              className="mx-auto mt-2 max-w-md"
              style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", lineHeight: 1.6, color: "var(--cv-ink-muted)" }}
            >
              Ranked by how closely your resume matches each uploaded job description.
            </p>
          </div>

          <div className="flex flex-col gap-4">
            {sortedMatches.map((match) => (
              <JobMatchCard key={match.id} match={match} />
            ))}
          </div>

          <div className="pt-2 text-center">
            <Button type="button" variant="outline" onClick={() => navigate("/resume/upload")}>
              Analyze another resume
            </Button>
          </div>
        </motion.div>
      </div>
    )
  }

  /* ── Render: upload / processing / error view ────────────────────────── */

  return (
    <div className="flex min-h-screen w-full items-center justify-center px-4 py-10" style={{ background: "var(--cv-bg)" }}>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: EASE }}
        className="w-full max-w-lg rounded-[var(--cv-radius-main)] bg-[var(--cv-card-surface)] p-6 sm:p-8"
        style={{ boxShadow: "var(--cv-shadow-main)" }}
      >
        {/* Header */}
        <div className="mb-6">
          <div
            className="mb-4 flex size-11 items-center justify-center rounded-full"
            style={{ background: "var(--cv-accent-soft)" }}
            aria-hidden
          >
            {isProcessing ? (
              <Sparkles size={20} strokeWidth={2} color="var(--cv-accent)" />
            ) : (
              <Briefcase size={20} strokeWidth={2} color="var(--cv-accent)" />
            )}
          </div>
          <h1
            style={{ fontFamily: "var(--cv-font-serif)", fontSize: "var(--cv-text-h2)", fontWeight: 400, lineHeight: 1.2, color: "var(--cv-ink)" }}
          >
            {isProcessing ? "Finding your career matches" : "Upload job descriptions"}
          </h1>
          <p className="mt-2" style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "var(--cv-ink-muted)" }}>
            {isProcessing
              ? "Sit tight — comparing your resume against real job opportunities."
              : "Upload one or more PDF or TXT job descriptions to compare against your resume."}
          </p>
        </div>

        {/* Error banner */}
        {phase === "error" && formError && (
          <div className="mb-4">
            <div
              className="flex items-start gap-3 rounded-[var(--cv-radius-card)] border p-4"
              style={{ background: "rgba(239, 68, 68, 0.12)", borderColor: "rgba(239, 68, 68, 0.28)" }}
            >
              <AlertCircle size={18} strokeWidth={2} color="#F87171" className="mt-0.5 shrink-0" aria-hidden />
              <div className="min-w-0 flex-1">
                <p style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", fontWeight: 600, color: "#FCA5A5" }}>
                  {phaseErrorHeading(errorPhase)}
                </p>
                <p className="mt-0.5" style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-caption)", color: "#FCA5A5" }}>
                  {formError}
                </p>
              </div>
            </div>
          </div>
        )}

        {phase === "idle" && formError && (
          <div className="mb-4">
            <FormErrorBanner message={formError} />
          </div>
        )}

        <AnimatePresence mode="wait">
          {isProcessing ? (
            <ProcessingPanel phase={phase} />
          ) : phase === "error" ? (
            <motion.div
              key="error-actions"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.35, ease: EASE }}
              className="flex flex-col gap-3"
            >
              <Button
                type="button"
                onClick={handleFindMatches}
                className="w-full text-white hover:opacity-90"
                style={{ background: "var(--cv-accent)" }}
              >
                <RotateCcw size={16} strokeWidth={2} aria-hidden />
                Try again
              </Button>
              <Button type="button" variant="outline" onClick={handleRetry} className="w-full">
                Choose different files
              </Button>
            </motion.div>
          ) : (
            <motion.div
              key="picker"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.35, ease: EASE }}
              className="flex flex-col gap-4"
            >
              {/* Drop zone */}
              <div
                role="button"
                tabIndex={0}
                onClick={() => inputRef.current?.click()}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault()
                    inputRef.current?.click()
                  }
                }}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className="flex cursor-pointer flex-col items-center justify-center gap-3 rounded-[var(--cv-radius-card)] border px-4 py-10 text-center outline-none transition-shadow duration-200 focus-visible:ring-2 focus-visible:ring-[var(--cv-accent)]"
                style={{
                  background: isDragging ? "var(--cv-accent-muted)" : "var(--cv-surface-subtle)",
                  borderColor: isDragging ? "var(--cv-accent)" : "var(--cv-border)",
                  boxShadow: isDragging ? "var(--cv-shadow-card)" : undefined,
                }}
                aria-label="Upload job description PDF or TXT files. Drag and drop or click to browse."
              >
                <div className="flex size-12 items-center justify-center rounded-full" style={{ background: "var(--cv-accent-soft)" }}>
                  <Upload size={22} strokeWidth={1.6} color="var(--cv-accent)" />
                </div>
                <div>
                  <p style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-body)", fontWeight: 600, color: "var(--cv-ink)" }}>
                    {isDragging ? "Drop your files here" : "Drag & drop job descriptions"}
                  </p>
                  <p className="mt-1" style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "var(--cv-ink-muted)" }}>
                    or click to browse · PDF or TXT · up to {MAX_FILES} files · max 10 MB each
                  </p>
                </div>
              </div>

              <input
                ref={inputRef}
                type="file"
                accept=".pdf,.txt,application/pdf,text/plain"
                multiple
                className="sr-only"
                onChange={handleInputChange}
              />

              {/* Selected files */}
              {selectedFiles.length > 0 && (
                <div className="flex flex-col gap-2">
                  {selectedFiles.map((file, index) => (
                    <motion.div
                      key={`${file.name}-${file.size}-${index}`}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.35, ease: EASE }}
                      className="flex items-center gap-3 rounded-[var(--cv-radius-card)] p-4"
                      style={{ background: "var(--cv-surface-subtle)", boxShadow: "var(--cv-shadow-card)" }}
                    >
                      <div className="flex size-11 shrink-0 items-center justify-center rounded-full" style={{ background: "var(--cv-accent-soft)" }}>
                        <FileText size={20} strokeWidth={1.6} color="var(--cv-accent)" aria-hidden />
                      </div>
                      <div className="min-w-0 flex-1 text-left">
                        <p
                          className="truncate"
                          style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", fontWeight: 600, color: "var(--cv-ink)" }}
                          title={file.name}
                        >
                          {file.name}
                        </p>
                        <p style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-caption)", color: "var(--cv-ink-muted)" }}>
                          {formatFileSize(file.size)}
                        </p>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => handleRemove(index)}
                        aria-label={`Remove ${file.name}`}
                        className="shrink-0"
                        style={{ color: "var(--cv-ink-muted)" }}
                      >
                        <Trash2 size={18} strokeWidth={1.6} />
                      </Button>
                    </motion.div>
                  ))}
                </div>
              )}

              <Button
                type="button"
                disabled={selectedFiles.length === 0}
                onClick={handleFindMatches}
                className="w-full text-white hover:opacity-90"
                style={{ background: "var(--cv-accent)" }}
              >
                <Sparkles size={16} strokeWidth={2} aria-hidden />
                Find My Career Matches
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}
