/**
 * ResumeUploadSection — drag-and-drop resume upload only.
 * On success: parse + review via existing APIs, then unlock Resume Report.
 * No JD logic here.
 */

import { useCallback, useRef, useState, type ChangeEvent, type DragEvent } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { AlertCircle, CheckCircle2, FileText, RotateCcw, Sparkles, Trash2, Upload } from "lucide-react"

import { LockedSection } from "@/components/dashboard/LockedSection"
import { FormErrorBanner } from "@/components/FormErrorBanner"
import { Button } from "@/components/ui/button"
import { useJourneyProgress } from "@/contexts/JourneyProgressContext"
import { useActiveResume } from "@/contexts/ActiveResumeContext"
import { ApiError } from "@/services/api"
import { createResume, reviewResume } from "@/services/resume"

const ACCEPTED_MIME = "application/pdf"
const MAX_BYTES = 10 * 1024 * 1024
const EASE = [0.22, 1, 0.36, 1] as const

type Phase = "idle" | "uploading" | "parsing" | "reviewing" | "done" | "error"

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

export function ResumeUploadSection() {
  const { setResumeComplete, scrollToSection, unlocks } = useJourneyProgress()
  const { setResumeId } = useActiveResume()
  const inputRef = useRef<HTMLInputElement>(null)

  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [phase, setPhase] = useState<Phase>("idle")
  const [confirmation, setConfirmation] = useState<string | null>(null)

  const selectFile = useCallback((file: File | null) => {
    setFormError(null)
    setConfirmation(null)
    if (!file) {
      setSelectedFile(null)
      return
    }
    if (!isPdfFile(file)) {
      setSelectedFile(null)
      setFormError("Only PDF files are accepted.")
      return
    }
    if (file.size > MAX_BYTES) {
      setSelectedFile(null)
      setFormError("Your resume must be 10 MB or smaller.")
      return
    }
    setSelectedFile(file)
  }, [])

  async function handleAnalyze() {
    if (!selectedFile) return
    setFormError(null)
    try {
      setPhase("uploading")
      const record = await createResume(selectedFile)
      setPhase("parsing")
      await new Promise((r) => setTimeout(r, 500))
      setPhase("reviewing")
      const report = await reviewResume(record.id)

      setResumeId(record.id)
      setResumeComplete({
        resumeId: record.id,
        fileName: record.file_name,
        report,
        reviewedAt: new Date().toISOString(),
      })
      setConfirmation(
        `“${record.file_name}” analyzed — Resume Analysis, Career Compatibility, and Career Explorer are now unlocked.`,
      )
      setPhase("done")
      setTimeout(() => scrollToSection("resume-analysis"), 400)
    } catch (error) {
      setFormError(
        error instanceof ApiError
          ? error.message
          : error instanceof Error
            ? error.message
            : "Upload failed. Please try again.",
      )
      setPhase("error")
    }
  }

  const isProcessing = phase === "uploading" || phase === "parsing" || phase === "reviewing"

  return (
    <LockedSection
      id="resume"
      title="Resume"
      locked={false}
      className="px-6 lg:px-10"
    >
      <div className="mx-auto max-w-xl">
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
          Resume
        </p>
        <h2
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h1)",
            fontWeight: 400,
            color: "var(--cv-ink)",
            lineHeight: 1.15,
          }}
        >
          Upload your resume
        </h2>
        <p
          className="mt-3 mb-8"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            color: "var(--cv-ink-muted)",
            lineHeight: 1.6,
          }}
        >
          Drop a PDF. We parse and review it — no job description needed yet.
        </p>

        <div
          className="cv-card p-6 sm:p-8"
        >
          {formError && phase !== "idle" && (
            <div className="mb-4 flex items-start gap-3 rounded-[var(--cv-radius-card)] p-4" style={{ background: "rgba(239, 68, 68, 0.14)" }}>
              <AlertCircle size={18} className="mt-0.5 shrink-0" color="#F87171" aria-hidden />
              <p style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "#FCA5A5" }}>
                {formError}
              </p>
            </div>
          )}
          {phase === "idle" && formError && (
            <div className="mb-4">
              <FormErrorBanner message={formError} />
            </div>
          )}

          <AnimatePresence mode="wait">
            {isProcessing ? (
              <motion.div
                key="processing"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.35, ease: EASE }}
                className="flex flex-col items-center gap-4 py-8 text-center"
              >
                <Sparkles size={28} style={{ color: "var(--cv-accent)" }} className="animate-pulse" />
                <p style={{ fontFamily: "var(--cv-font-sans)", fontWeight: 600, color: "var(--cv-ink)" }}>
                  {phase === "uploading" && "Uploading…"}
                  {phase === "parsing" && "Parsing…"}
                  {phase === "reviewing" && "AI reviewing…"}
                </p>
              </motion.div>
            ) : phase === "done" && confirmation ? (
              <motion.div
                key="done"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center gap-3 py-6 text-center"
              >
                <CheckCircle2 size={32} style={{ color: "#4ADE80" }} />
                <p style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "var(--cv-ink)" }}>
                  {confirmation}
                </p>
                {unlocks.resumeAnalysis && (
                  <Button
                    type="button"
                    className="mt-2 rounded-full"
                    style={{ background: "var(--cv-accent)", color: "#fff" }}
                    onClick={() => scrollToSection("resume-analysis")}
                  >
                    View analysis
                  </Button>
                )}
              </motion.div>
            ) : phase === "error" ? (
              <motion.div key="err" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col gap-3">
                <Button type="button" className="rounded-full text-white" style={{ background: "var(--cv-accent)" }} onClick={handleAnalyze}>
                  <RotateCcw size={16} /> Try again
                </Button>
                <Button type="button" variant="outline" className="rounded-full" onClick={() => setPhase("idle")}>
                  Choose another file
                </Button>
              </motion.div>
            ) : (
              <motion.div key="picker" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col gap-4">
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
                  onDragLeave={(e: DragEvent) => {
                    e.preventDefault()
                    setIsDragging(false)
                  }}
                  onDrop={(e: DragEvent) => {
                    e.preventDefault()
                    setIsDragging(false)
                    selectFile(e.dataTransfer.files?.[0] ?? null)
                  }}
                  className="flex cursor-pointer flex-col items-center gap-3 rounded-[var(--cv-radius-card)] px-4 py-10 text-center transition-colors"
                  style={{
                    background: isDragging ? "var(--cv-accent-soft)" : "var(--cv-bg)",
                    border: "1px dashed var(--cv-border)",
                  }}
                >
                  <div className="cv-icon-circle size-12">
                    <Upload size={22} strokeWidth={1.6} style={{ color: "var(--cv-accent)" }} />
                  </div>
                  <p style={{ fontFamily: "var(--cv-font-sans)", fontWeight: 600, color: "var(--cv-ink)" }}>
                    {isDragging ? "Drop your PDF here" : "Drag & drop your resume"}
                  </p>
                  <p style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)", color: "var(--cv-ink-muted)" }}>
                    or click to browse · PDF · max 10 MB
                  </p>
                </div>
                <input
                  ref={inputRef}
                  type="file"
                  accept="application/pdf,.pdf"
                  className="sr-only"
                  onChange={(e: ChangeEvent<HTMLInputElement>) => {
                    selectFile(e.target.files?.[0] ?? null)
                    e.target.value = ""
                  }}
                />
                {selectedFile && (
                  <div className="cv-card flex items-center gap-3 p-4">
                    <div className="cv-icon-circle">
                      <FileText size={20} style={{ color: "var(--cv-accent)" }} aria-hidden />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate" style={{ fontFamily: "var(--cv-font-sans)", fontWeight: 600, fontSize: "var(--cv-text-small)" }}>
                        {selectedFile.name}
                      </p>
                      <p style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-caption)", color: "var(--cv-ink-muted)" }}>
                        {formatFileSize(selectedFile.size)}
                      </p>
                    </div>
                    <Button type="button" variant="ghost" size="icon" onClick={() => selectFile(null)} aria-label="Remove file">
                      <Trash2 size={18} />
                    </Button>
                  </div>
                )}
                <Button
                  type="button"
                  disabled={!selectedFile}
                  onClick={handleAnalyze}
                  className="w-full rounded-full text-white"
                  style={{ background: "var(--cv-accent)" }}
                >
                  <Sparkles size={16} /> Analyze resume
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </LockedSection>
  )
}
