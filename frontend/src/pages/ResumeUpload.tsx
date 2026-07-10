import { useCallback, useRef, useState, type ChangeEvent, type DragEvent } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { CheckCircle2, FileText, Trash2, Upload } from "lucide-react"

import { FormErrorBanner } from "@/components/FormErrorBanner"
import { Button } from "@/components/ui/button"
import { uploadResume } from "@/services/resume"
import { ApiError } from "@/services/api"

const ACCEPTED_MIME = "application/pdf"
const MAX_BYTES = 10 * 1024 * 1024

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

/**
 * Resume upload screen — select a PDF (drag/drop or click), preview it,
 * optionally remove it, then POST to /resume/upload.
 * Analysis / parsing / AI are intentionally out of scope for this milestone.
 */
export function ResumeUploadPage() {
  const inputRef = useRef<HTMLInputElement>(null)

  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedName, setUploadedName] = useState<string | null>(null)

  const selectFile = useCallback((file: File | null) => {
    setFormError(null)
    setUploadedName(null)

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
      setFormError("Resume must be 10 MB or smaller.")
      return
    }

    setSelectedFile(file)
  }, [])

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null
    selectFile(file)
    // Allow re-selecting the same file after remove.
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
    const file = event.dataTransfer.files?.[0] ?? null
    selectFile(file)
  }

  function handleRemove() {
    selectFile(null)
    if (inputRef.current) {
      inputRef.current.value = ""
    }
  }

  async function handleUpload() {
    if (!selectedFile) return

    setFormError(null)
    setIsUploading(true)

    try {
      const result = await uploadResume(selectedFile)
      setUploadedName(result.file_name)
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : error instanceof Error
            ? error.message
            : "Upload failed. Please try again."
      setFormError(message)
    } finally {
      setIsUploading(false)
    }
  }

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
        <div className="mb-6">
          <div
            className="mb-4 flex size-11 items-center justify-center rounded-full"
            style={{ background: "var(--cv-card-amber-icon)" }}
            aria-hidden
          >
            <Upload size={20} strokeWidth={2} color="#111827" />
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
            Upload your resume
          </h1>
          <p
            className="mt-2 text-gray-500"
            style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)" }}
          >
            Drop a PDF resume to get started. Analysis comes in the next step.
          </p>
        </div>

        {formError && (
          <div className="mb-4">
            <FormErrorBanner message={formError} />
          </div>
        )}

        <AnimatePresence mode="wait">
          {uploadedName ? (
            <motion.div
              key="success"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              className="flex flex-col items-start gap-3 rounded-[var(--cv-radius-card)] p-5"
              style={{ background: "var(--cv-card-sage)" }}
            >
              <div className="flex items-center gap-3">
                <CheckCircle2 size={22} strokeWidth={2} color="#166534" aria-hidden />
                <div>
                  <p
                    className="text-gray-900"
                    style={{
                      fontFamily: "var(--cv-font-serif)",
                      fontSize: "var(--cv-text-h3)",
                      fontWeight: 500,
                    }}
                  >
                    Resume uploaded
                  </p>
                  <p
                    className="mt-0.5 text-gray-600"
                    style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)" }}
                  >
                    {uploadedName} is ready for the next step.
                  </p>
                </div>
              </div>
              <Button
                type="button"
                variant="outline"
                onClick={handleRemove}
                className="mt-1"
              >
                Upload a different file
              </Button>
            </motion.div>
          ) : (
            <motion.div
              key="picker"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              className="flex flex-col gap-4"
            >
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
                    style={{
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "var(--cv-text-body)",
                      fontWeight: 600,
                    }}
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

              {selectedFile && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
                  className="flex items-center gap-3 rounded-[var(--cv-radius-card)] p-4"
                  style={{
                    background: "var(--cv-card-amber)",
                    boxShadow: "var(--cv-shadow-card)",
                  }}
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
                      style={{
                        fontFamily: "var(--cv-font-sans)",
                        fontSize: "var(--cv-text-small)",
                        fontWeight: 600,
                      }}
                      title={selectedFile.name}
                    >
                      {selectedFile.name}
                    </p>
                    <p
                      className="text-gray-600"
                      style={{
                        fontFamily: "var(--cv-font-sans)",
                        fontSize: "var(--cv-text-caption)",
                      }}
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

              <Button
                type="button"
                disabled={!selectedFile || isUploading}
                onClick={handleUpload}
                className="w-full text-white hover:opacity-90"
                style={{ background: "var(--cv-accent)" }}
              >
                {isUploading ? "Uploading…" : "Upload resume"}
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}
