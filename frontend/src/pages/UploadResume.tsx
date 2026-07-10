/**
 * UploadResumePage — the full, end-to-end resume review entry point.
 *
 * User flow:
 *   1. Select PDF (drag-and-drop or click-to-browse)
 *   2. Click "Analyze Resume"
 *   3. POST /resumes  → upload + parse (shows "Uploading..." then "Parsing...")
 *   4. POST /resumes/{id}/review  → AI review (shows "AI Reviewing...")
 *   5. Navigate to /resume-report/:id with the report in location.state
 *
 * State machine:
 *   idle → uploading → parsing → reviewing → (navigate) | error
 *
 * Error handling:
 *   Every phase has its own error copy. A "Try again" button resets to idle
 *   so the user can re-run without having to re-select the file.
 */

import { useCallback, useRef, useState, type ChangeEvent, type DragEvent } from "react"
import { useNavigate } from "react-router-dom"
import { AnimatePresence, motion } from "framer-motion"
import { AlertCircle, FileText, RotateCcw, Sparkles, Trash2, Upload } from "lucide-react"

import { FormErrorBanner } from "@/components/FormErrorBanner"
import { Button } from "@/components/ui/button"
import { createResume, reviewResume } from "@/services/resume"
import { ApiError } from "@/services/api"
import type { ResumeReportState } from "@/types"

/* ─── Constants ─────────────────────────────────────────────────────────── */

const ACCEPTED_MIME = "application/pdf"
const MAX_BYTES = 10 * 1024 * 1024

/* ─── Types ─────────────────────────────────────────────────────────────── */

type Phase = "idle" | "uploading" | "parsing" | "reviewing" | "error"

/* ─── Step config — drives the processing-state UI ─────────────────────── */

const STEPS: Array<{ phase: Phase; label: string; description: string }> = [
  { phase: "uploading", label: "Uploading Resume", description: "Sending your PDF to the server…" },
  { phase: "parsing",   label: "Parsing Resume",   description: "Extracting text, skills, and experience…" },
  { phase: "reviewing", label: "AI Reviewing",      description: "GPT-4o is reading every line of your resume…" },
]

const ACTIVE_STEP_INDEX: Record<Phase, number> = {
  idle:      -1,
  uploading:  0,
  parsing:    1,
  reviewing:  2,
  error:     -1,
}

/* ─── Helpers ───────────────────────────────────────────────────────────── */

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function isPdfFile(file: File): boolean {
  const byExtension = file.name.toLowerCase().endsWith(".pdf")
  const byMime = file.type === ACCEPTED_MIME || file.type === "" || file.type === "application/octet-stream"
  return byExtension && byMime
}

function phaseErrorHeading(phase: Phase): string {
  switch (phase) {
    case "uploading": return "Upload failed"
    case "parsing":   return "Parsing failed"
    case "reviewing": return "AI review failed"
    default:          return "Something went wrong"
  }
}

/* ─── Sub-components ────────────────────────────────────────────────────── */

/** Pulsing dot spinner shown next to the active step. */
function PulsingDot() {
  return (
    <span className="relative flex size-2.5">
      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#6B7FFF] opacity-60" />
      <span className="relative inline-flex size-2.5 rounded-full bg-[#6B7FFF]" />
    </span>
  )
}

interface ProcessingPanelProps {
  phase: Phase
}

/** Three-step processing timeline shown while the API calls are in flight. */
function ProcessingPanel({ phase }: ProcessingPanelProps) {
  const activeIdx = ACTIVE_STEP_INDEX[phase]

  return (
    <motion.div
      key="processing"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="flex flex-col gap-6 py-2"
    >
      {/* Progress bar */}
      <div className="h-1 w-full overflow-hidden rounded-full bg-gray-100">
        <motion.div
          className="h-full rounded-full bg-[#6B7FFF]"
          initial={{ width: "0%" }}
          animate={{ width: `${((activeIdx + 1) / STEPS.length) * 100}%` }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>

      {/* Steps */}
      <div className="flex flex-col gap-4">
        {STEPS.map((step, idx) => {
          const isDone = idx < activeIdx
          const isActive = idx === activeIdx
          const isPending = idx > activeIdx

          return (
            <div key={step.phase} className="flex items-start gap-3">
              {/* Step indicator */}
              <div className="mt-0.5 flex size-5 shrink-0 items-center justify-center">
                {isDone ? (
                  <svg viewBox="0 0 20 20" fill="none" className="size-5" aria-hidden>
                    <circle cx="10" cy="10" r="10" fill="#D4EDD8" />
                    <path d="M6 10l3 3 5-5" stroke="#166534" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                ) : isActive ? (
                  <PulsingDot />
                ) : (
                  <span
                    className="flex size-5 items-center justify-center rounded-full border-2 border-gray-200"
                    aria-hidden
                  />
                )}
              </div>

              {/* Step text */}
              <div className="min-w-0 flex-1">
                <p
                  style={{
                    fontFamily: "var(--cv-font-sans)",
                    fontSize: "var(--cv-text-small)",
                    fontWeight: isActive ? 700 : isPending ? 400 : 500,
                    color: isActive ? "#111827" : isPending ? "#9CA3AF" : "#374151",
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
                      color: "#6B7280",
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
        style={{
          fontFamily: "var(--cv-font-sans)",
          fontSize: "var(--cv-text-caption)",
          color: "#9CA3AF",
        }}
      >
        This may take up to 30 seconds — please don't close this tab.
      </p>
    </motion.div>
  )
}

/* ─── Main page ─────────────────────────────────────────────────────────── */

export function UploadResumePage() {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)

  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [phase, setPhase] = useState<Phase>("idle")
  const [errorPhase, setErrorPhase] = useState<Phase>("idle")

  /* ── File selection ─────────────────────────────────────────────────── */

  const selectFile = useCallback((file: File | null) => {
    setFormError(null)
    if (!file) { setSelectedFile(null); return }

    if (!isPdfFile(file)) {
      setSelectedFile(null)
      setFormError("Only PDF files are accepted. Please select a .pdf file.")
      return
    }
    if (file.size > MAX_BYTES) {
      setSelectedFile(null)
      setFormError("Your resume must be 10 MB or smaller.")
      return
    }
    setSelectedFile(file)
  }, [])

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    selectFile(event.target.files?.[0] ?? null)
    event.target.value = ""
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault(); event.stopPropagation(); setIsDragging(true)
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    event.preventDefault(); event.stopPropagation(); setIsDragging(false)
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault(); event.stopPropagation(); setIsDragging(false)
    selectFile(event.dataTransfer.files?.[0] ?? null)
  }

  function handleRemove() {
    selectFile(null)
    if (inputRef.current) inputRef.current.value = ""
  }

  /* ── Main flow ──────────────────────────────────────────────────────── */

  async function handleAnalyze() {
    if (!selectedFile) return

    setFormError(null)

    try {
      // Step 1: Upload + parse (POST /resumes)
      setPhase("uploading")
      const record = await createResume(selectedFile)

      // Step 2: Brief "Parsing" visual beat — the parse already happened
      // inside POST /resumes, but showing the step reassures the user.
      setPhase("parsing")
      await new Promise((resolve) => setTimeout(resolve, 700))

      // Step 3: AI review (POST /resumes/{id}/review)
      setPhase("reviewing")
      const report = await reviewResume(record.id)

      // Navigate to the report page, passing data via location.state so
      // the report page never needs to call the API again.
      const state: ResumeReportState = {
        report,
        resumeId: record.id,
        fileName: record.file_name,
        reviewedAt: new Date().toISOString(),
      }
      navigate(`/resume-report/${record.id}`, { state })
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

  /* ── Derived state ──────────────────────────────────────────────────── */

  const isProcessing = phase === "uploading" || phase === "parsing" || phase === "reviewing"

  /* ── Render ─────────────────────────────────────────────────────────── */

  return (
    <div
      className="flex min-h-screen w-full items-center justify-center px-4 py-10"
      style={{ background: "var(--cv-bg)" }}
    >
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-lg rounded-[var(--cv-radius-main)] bg-white p-6 sm:p-8"
        style={{ boxShadow: "var(--cv-shadow-main)" }}
      >
        {/* Header */}
        <div className="mb-6">
          <div
            className="mb-4 flex size-11 items-center justify-center rounded-full"
            style={{ background: isProcessing ? "var(--cv-card-lavender-icon)" : "var(--cv-card-amber-icon)" }}
            aria-hidden
          >
            {isProcessing
              ? <Sparkles size={20} strokeWidth={2} color="#111827" />
              : <Upload size={20} strokeWidth={2} color="#111827" />
            }
          </div>
          <h1
            className="text-gray-900"
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize: "var(--cv-text-h2)",
              fontWeight: 400,
              lineHeight: 1.2,
            }}
          >
            {isProcessing ? "Analyzing your resume" : "Upload your resume"}
          </h1>
          <p
            className="mt-2 text-gray-500"
            style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)" }}
          >
            {isProcessing
              ? "Sit tight — AI is reviewing every section of your resume."
              : "Drop a PDF to receive an AI-powered review of your resume."}
          </p>
        </div>

        {/* Error banner */}
        {phase === "error" && formError && (
          <div className="mb-4">
            <div
              className="flex items-start gap-3 rounded-[var(--cv-radius-card)] p-4"
              style={{ background: "#FEF2F2" }}
            >
              <AlertCircle size={18} strokeWidth={2} color="#DC2626" className="mt-0.5 shrink-0" aria-hidden />
              <div className="min-w-0 flex-1">
                <p
                  style={{
                    fontFamily: "var(--cv-font-sans)",
                    fontSize: "var(--cv-text-small)",
                    fontWeight: 600,
                    color: "#991B1B",
                  }}
                >
                  {phaseErrorHeading(errorPhase)}
                </p>
                <p
                  className="mt-0.5"
                  style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-caption)", color: "#B91C1C" }}
                >
                  {formError}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Form error (file validation) */}
        {phase === "idle" && formError && (
          <div className="mb-4">
            <FormErrorBanner message={formError} />
          </div>
        )}

        <AnimatePresence mode="wait">
          {isProcessing ? (
            <ProcessingPanel phase={phase} />
          ) : phase === "error" ? (
            /* ── Error state ─────────────────────────────────────────── */
            <motion.div
              key="error-actions"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              className="flex flex-col gap-3"
            >
              <Button
                type="button"
                onClick={handleAnalyze}
                className="w-full text-white hover:opacity-90"
                style={{ background: "var(--cv-accent)" }}
              >
                <RotateCcw size={16} strokeWidth={2} aria-hidden />
                Try again
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={handleRetry}
                className="w-full"
              >
                Upload a different file
              </Button>
            </motion.div>
          ) : (
            /* ── Idle: file picker ───────────────────────────────────── */
            <motion.div
              key="picker"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              className="flex flex-col gap-4"
            >
              {/* Drop zone */}
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
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className="flex cursor-pointer flex-col items-center justify-center gap-3 rounded-[var(--cv-radius-card)] px-4 py-10 text-center outline-none transition-shadow duration-200 focus-visible:ring-2 focus-visible:ring-[var(--cv-accent)]"
                style={{
                  background: isDragging ? "var(--cv-card-amber)" : "#F7F5F0",
                  boxShadow: isDragging ? "var(--cv-shadow-card)" : undefined,
                }}
                aria-label="Upload resume PDF. Drag and drop or click to browse."
              >
                <div
                  className="flex size-12 items-center justify-center rounded-full"
                  style={{ background: "var(--cv-card-amber-icon)" }}
                >
                  <Upload size={22} strokeWidth={1.6} color="#111827" />
                </div>
                <div>
                  <p
                    className="text-gray-900"
                    style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-body)", fontWeight: 600 }}
                  >
                    {isDragging ? "Drop your PDF here" : "Drag & drop your resume"}
                  </p>
                  <p
                    className="mt-1 text-gray-500"
                    style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)" }}
                  >
                    or click to browse · PDF only · max 10 MB
                  </p>
                </div>
              </div>

              <input
                ref={inputRef}
                type="file"
                accept="application/pdf,.pdf"
                className="sr-only"
                onChange={handleInputChange}
              />

              {/* Selected file preview */}
              {selectedFile && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
                  className="flex items-center gap-3 rounded-[var(--cv-radius-card)] p-4"
                  style={{ background: "var(--cv-card-amber)", boxShadow: "var(--cv-shadow-card)" }}
                >
                  <div
                    className="flex size-11 shrink-0 items-center justify-center rounded-full"
                    style={{ background: "var(--cv-card-amber-icon)" }}
                  >
                    <FileText size={20} strokeWidth={1.6} color="#111827" aria-hidden />
                  </div>
                  <div className="min-w-0 flex-1 text-left">
                    <p
                      className="truncate text-gray-900"
                      style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", fontWeight: 600 }}
                      title={selectedFile.name}
                    >
                      {selectedFile.name}
                    </p>
                    <p
                      className="text-gray-600"
                      style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-caption)" }}
                    >
                      {formatFileSize(selectedFile.size)}
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={handleRemove}
                    aria-label="Remove selected file"
                    className="shrink-0 text-gray-600 hover:text-gray-900"
                  >
                    <Trash2 size={18} strokeWidth={1.6} />
                  </Button>
                </motion.div>
              )}

              {/* CTA button */}
              <Button
                type="button"
                disabled={!selectedFile}
                onClick={handleAnalyze}
                className="w-full text-white hover:opacity-90"
                style={{ background: "var(--cv-accent)" }}
              >
                <Sparkles size={16} strokeWidth={2} aria-hidden />
                Analyze Resume
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}
