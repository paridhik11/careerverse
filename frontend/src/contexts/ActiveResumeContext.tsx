/**
 * ActiveResumeContext — tracks the currently active resume ID across pages.
 *
 * The Career Mentor sidebar is mounted globally (in App.tsx) and needs the
 * current resume ID to load history and send chat messages. Since different
 * pages surface the resume ID in different ways (URL param, router state, or
 * just "the last one the user worked on"), this context auto-extracts it from
 * known URL patterns and persists it to localStorage as a fallback for pages
 * that don't carry it in the URL (Skill Gap, Learning Roadmap).
 *
 * Pages do NOT need to import or call this context themselves — the URL
 * extraction covers all parameterised routes automatically.
 */

import { createContext, useContext, useEffect, useState } from "react"
import { useLocation } from "react-router-dom"

import { RESUME_ID_STORAGE_KEY } from "@/services/api"

// ---------------------------------------------------------------------------
// URL patterns that carry a resume ID as the first numeric capture group.
// ---------------------------------------------------------------------------

const RESUME_ID_PATTERNS: RegExp[] = [
  /^\/resume-report\/(\d+)/,
  /^\/career-matches\/(\d+)/,
  /^\/experience\/(\d+)/,
]

// ---------------------------------------------------------------------------
// Context shape
// ---------------------------------------------------------------------------

type ActiveResumeContextValue = {
  resumeId: number | null
  setResumeId: (id: number) => void
}

const ActiveResumeContext = createContext<ActiveResumeContextValue>({
  resumeId: null,
  setResumeId: () => undefined,
})

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function ActiveResumeProvider({ children }: { children: React.ReactNode }) {
  const location = useLocation()

  const [resumeId, setResumeIdState] = useState<number | null>(() => {
    const stored = localStorage.getItem(RESUME_ID_STORAGE_KEY)
    const parsed = stored ? parseInt(stored, 10) : NaN
    return isNaN(parsed) ? null : parsed
  })

  // Auto-extract resume ID from URL on every navigation.
  useEffect(() => {
    for (const pattern of RESUME_ID_PATTERNS) {
      const match = location.pathname.match(pattern)
      if (match) {
        const id = parseInt(match[1], 10)
        if (!isNaN(id)) {
          setResumeIdState(id)
          localStorage.setItem(RESUME_ID_STORAGE_KEY, String(id))
          return
        }
      }
    }
    // No match — keep the last known resume ID from localStorage.
  }, [location.pathname])

  function setResumeId(id: number) {
    setResumeIdState(id)
    localStorage.setItem(RESUME_ID_STORAGE_KEY, String(id))
  }

  return (
    <ActiveResumeContext.Provider value={{ resumeId, setResumeId }}>
      {children}
    </ActiveResumeContext.Provider>
  )
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useActiveResume(): ActiveResumeContextValue {
  return useContext(ActiveResumeContext)
}
