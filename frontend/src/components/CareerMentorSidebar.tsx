/**
 * CareerMentorSidebar — the global persistent chat panel for the Career Mentor.
 *
 * Rendered once in App.tsx (outside the Route tree) so it survives page
 * navigation without re-mounting. The panel slides out from the right side
 * of the viewport when the floating action button is clicked.
 *
 * Behaviour
 * ---------
 * - On mount, loads conversation history via GET /career-mentor/history if a
 *   resume ID is available.
 * - Handles the streaming response with a typewriter effect: each incoming
 *   token is appended to the "in-flight" assistant bubble in real time.
 * - When no resume ID is available (the user hasn't uploaded a resume yet),
 *   the panel shows a friendly prompt to start the flow.
 *
 * Design tokens used
 * ------------------
 * - Sidebar bg: --cv-card-lavender (Career Mentor's pastel per DESIGN_SYSTEM.md)
 * - Icon: Users (Lucide) per the icon mapping
 * - Accent: --cv-accent (#6B7FFF indigo)
 * - Typography: Fraunces for the header, Manrope everywhere else
 */

import { useEffect, useRef, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { MessageSquare, Send, Users, X, Loader2 } from "lucide-react"

import { useActiveResume } from "@/contexts/ActiveResumeContext"
import { getMentorHistory, streamMentorChat } from "@/services/careerMentor"
import type { MentorMessageRecord } from "@/types"

// ---------------------------------------------------------------------------
// Animation config (matches DESIGN_SYSTEM.md expo-out easing)
// ---------------------------------------------------------------------------

const EASE = [0.22, 1, 0.36, 1] as const

const panelVariants = {
  hidden: { x: "100%", opacity: 0 },
  visible: { x: 0, opacity: 1, transition: { duration: 0.35, ease: EASE } },
  exit: { x: "100%", opacity: 0, transition: { duration: 0.25, ease: EASE } },
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function MessageBubble({ role, content }: { role: "user" | "assistant"; content: string }) {
  const isUser = role === "user"

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      {!isUser && (
        <div
          className="mr-2 mt-1 flex size-7 shrink-0 items-center justify-center rounded-full"
          style={{ background: "var(--cv-card-lavender-icon)" }}
          aria-hidden
        >
          <Users size={14} strokeWidth={2} style={{ color: "#5B21B6" }} />
        </div>
      )}
      <div
        className="max-w-[82%] rounded-2xl px-4 py-2.5"
        style={{
          background: isUser ? "var(--cv-accent)" : "white",
          boxShadow: isUser ? "none" : "var(--cv-shadow-card)",
          fontFamily: "var(--cv-font-sans)",
          fontSize: "0.8125rem",
          lineHeight: 1.6,
          color: isUser ? "#fff" : "#1F2937",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}
      >
        {content}
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex justify-start mb-3">
      <div
        className="mr-2 mt-1 flex size-7 shrink-0 items-center justify-center rounded-full"
        style={{ background: "var(--cv-card-lavender-icon)" }}
        aria-hidden
      >
        <Users size={14} strokeWidth={2} style={{ color: "#5B21B6" }} />
      </div>
      <div
        className="flex items-center gap-1 rounded-2xl bg-white px-4 py-3"
        style={{ boxShadow: "var(--cv-shadow-card)" }}
      >
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="block size-1.5 rounded-full"
            style={{ background: "#9CA3AF" }}
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
          />
        ))}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Sidebar component
// ---------------------------------------------------------------------------

export function CareerMentorSidebar() {
  const { resumeId } = useActiveResume()

  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<MentorMessageRecord[]>([])
  const [streamingText, setStreamingText] = useState<string | null>(null)
  const [inputValue, setInputValue] = useState("")
  const [isSending, setIsSending] = useState(false)
  const [historyError, setHistoryError] = useState<string | null>(null)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Load history when sidebar opens or resumeId changes.
  useEffect(() => {
    if (!isOpen || !resumeId) return

    setHistoryError(null)
    getMentorHistory(resumeId)
      .then((msgs) => setMessages(msgs))
      .catch(() => setHistoryError("Couldn't load conversation history."))
  }, [isOpen, resumeId])

  // Scroll to bottom whenever messages or the streaming text change.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, streamingText])

  async function handleSend() {
    if (!resumeId || !inputValue.trim() || isSending) return

    const userText = inputValue.trim()
    setInputValue("")
    setIsSending(true)
    setStreamingText("")

    // Optimistically add the user message.
    const userMessage: MentorMessageRecord = {
      id: Date.now(),
      resume_id: resumeId,
      role: "user",
      content: userText,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])

    await streamMentorChat(
      resumeId,
      userText,
      (chunk) => {
        setStreamingText((prev) => (prev ?? "") + chunk)
      },
      (fullText) => {
        // Stream complete — move the streamed text into the messages list.
        const assistantMessage: MentorMessageRecord = {
          id: Date.now() + 1,
          resume_id: resumeId,
          role: "assistant",
          content: fullText,
          created_at: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, assistantMessage])
        setStreamingText(null)
        setIsSending(false)
      },
      (error) => {
        // On error, show the error as an assistant message.
        const errorMessage: MentorMessageRecord = {
          id: Date.now() + 1,
          resume_id: resumeId,
          role: "assistant",
          content: error,
          created_at: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, errorMessage])
        setStreamingText(null)
        setIsSending(false)
      },
    )
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <>
      {/* Floating action button */}
      <motion.button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex size-14 items-center justify-center rounded-full shadow-lg"
        style={{
          background: "var(--cv-accent)",
          display: isOpen ? "none" : "flex",
        }}
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.95 }}
        aria-label="Open Career Mentor"
        title="Career Mentor"
      >
        <MessageSquare size={22} strokeWidth={2} color="#fff" />
      </motion.button>

      {/* Sidebar panel */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop (mobile) */}
            <motion.div
              key="backdrop"
              className="fixed inset-0 z-40 bg-black/20 md:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
            />

            <motion.aside
              key="panel"
              variants={panelVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="fixed bottom-0 right-0 top-0 z-50 flex w-full flex-col md:w-[400px]"
              style={{
                background: "var(--cv-bg)",
                boxShadow: "-4px 0 24px 0 rgb(0 0 0 / 0.12)",
              }}
              aria-label="Career Mentor chat panel"
            >
              {/* Header */}
              <div
                className="flex shrink-0 items-center gap-3 border-b px-5 py-4"
                style={{
                  background: "var(--cv-card-lavender)",
                  borderColor: "var(--cv-card-lavender-icon)",
                }}
              >
                <div
                  className="flex size-9 shrink-0 items-center justify-center rounded-full"
                  style={{ background: "var(--cv-card-lavender-icon)" }}
                  aria-hidden
                >
                  <Users size={18} strokeWidth={2} style={{ color: "#5B21B6" }} />
                </div>
                <div className="flex-1 min-w-0">
                  <h2
                    className="truncate"
                    style={{
                      fontFamily: "var(--cv-font-serif)",
                      fontSize: "var(--cv-text-h3)",
                      fontWeight: 500,
                      color: "#1F2937",
                      lineHeight: 1.3,
                    }}
                  >
                    Career Mentor
                  </h2>
                  <p
                    style={{
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "var(--cv-text-caption)",
                      color: "#6B7280",
                    }}
                  >
                    Ask about your career, skills, or interview prep
                  </p>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="ml-auto flex size-8 shrink-0 items-center justify-center rounded-full hover:bg-black/10 transition-colors"
                  aria-label="Close mentor panel"
                >
                  <X size={18} style={{ color: "#374151" }} />
                </button>
              </div>

              {/* Message area */}
              <div className="flex-1 overflow-y-auto px-4 py-4">
                {!resumeId ? (
                  <div className="flex h-full flex-col items-center justify-center text-center px-4">
                    <div
                      className="mb-3 flex size-14 items-center justify-center rounded-full"
                      style={{ background: "var(--cv-card-lavender)" }}
                    >
                      <Users size={24} strokeWidth={1.6} style={{ color: "#7C3AED" }} />
                    </div>
                    <p
                      style={{
                        fontFamily: "var(--cv-font-serif)",
                        fontSize: "var(--cv-text-h3)",
                        fontWeight: 500,
                        color: "#1F2937",
                        marginBottom: "0.5rem",
                      }}
                    >
                      Upload your resume first
                    </p>
                    <p
                      style={{
                        fontFamily: "var(--cv-font-sans)",
                        fontSize: "var(--cv-text-small)",
                        color: "#6B7280",
                        lineHeight: 1.6,
                      }}
                    >
                      The mentor uses your resume, career match, skill gap, and
                      roadmap data to give you personalised guidance.
                    </p>
                  </div>
                ) : historyError ? (
                  <p
                    className="text-center mt-8"
                    style={{
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "var(--cv-text-small)",
                      color: "#9CA3AF",
                    }}
                  >
                    {historyError}
                  </p>
                ) : (
                  <>
                    {messages.length === 0 && !streamingText && (
                      <div className="flex flex-col items-center justify-center py-10 text-center">
                        <p
                          style={{
                            fontFamily: "var(--cv-font-sans)",
                            fontSize: "var(--cv-text-small)",
                            color: "#9CA3AF",
                            lineHeight: 1.6,
                          }}
                        >
                          Ask me anything about your career — why a role matched,
                          what skills to build, or get mock interview questions.
                        </p>
                        {/* Suggested prompts */}
                        <div className="mt-5 flex flex-col gap-2 w-full">
                          {[
                            "Why did my top career match my resume?",
                            "What are my most important missing skills?",
                            "Give me 5 interview questions for my chosen role.",
                          ].map((prompt) => (
                            <button
                              key={prompt}
                              onClick={() => {
                                setInputValue(prompt)
                                inputRef.current?.focus()
                              }}
                              className="rounded-xl px-4 py-2.5 text-left transition-colors hover:opacity-80"
                              style={{
                                background: "var(--cv-card-lavender)",
                                fontFamily: "var(--cv-font-sans)",
                                fontSize: "var(--cv-text-caption)",
                                color: "#5B21B6",
                                fontWeight: 500,
                              }}
                            >
                              {prompt}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {messages.map((msg) => (
                      <MessageBubble key={msg.id} role={msg.role} content={msg.content} />
                    ))}

                    {/* In-flight streaming assistant bubble */}
                    {streamingText !== null && (
                      streamingText === "" ? (
                        <TypingIndicator />
                      ) : (
                        <MessageBubble role="assistant" content={streamingText} />
                      )
                    )}
                  </>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input area */}
              {resumeId && (
                <div
                  className="shrink-0 border-t px-4 py-3"
                  style={{
                    borderColor: "#E5E7EB",
                    background: "white",
                  }}
                >
                  <div
                    className="flex items-end gap-2 rounded-2xl px-4 py-2"
                    style={{
                      background: "var(--cv-bg)",
                      border: "1.5px solid #E5E7EB",
                    }}
                  >
                    <textarea
                      ref={inputRef}
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder="Ask your mentor…"
                      rows={1}
                      disabled={isSending}
                      className="flex-1 resize-none bg-transparent outline-none"
                      style={{
                        fontFamily: "var(--cv-font-sans)",
                        fontSize: "var(--cv-text-small)",
                        color: "#1F2937",
                        lineHeight: 1.5,
                        maxHeight: "120px",
                        overflowY: "auto",
                      }}
                    />
                    <button
                      onClick={handleSend}
                      disabled={!inputValue.trim() || isSending}
                      className="mb-0.5 flex size-8 shrink-0 items-center justify-center rounded-full transition-colors disabled:opacity-40"
                      style={{ background: "var(--cv-accent)" }}
                      aria-label="Send message"
                    >
                      {isSending ? (
                        <Loader2 size={15} className="animate-spin" color="#fff" />
                      ) : (
                        <Send size={15} color="#fff" strokeWidth={2} />
                      )}
                    </button>
                  </div>
                  <p
                    className="mt-1.5 text-center"
                    style={{
                      fontFamily: "var(--cv-font-sans)",
                      fontSize: "0.6875rem",
                      color: "#D1D5DB",
                    }}
                  >
                    Enter to send · Shift+Enter for new line
                  </p>
                </div>
              )}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  )
}
