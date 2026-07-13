/**
 * MentorUiContext — lets the Dashboard navbar open the Career Mentor panel
 * without coupling to CareerMentorSidebar internals.
 */

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react"

type MentorUiValue = {
  isOpen: boolean
  openMentor: () => void
  closeMentor: () => void
  toggleMentor: () => void
}

const MentorUiContext = createContext<MentorUiValue | null>(null)

export function MentorUiProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)

  const openMentor = useCallback(() => setIsOpen(true), [])
  const closeMentor = useCallback(() => setIsOpen(false), [])
  const toggleMentor = useCallback(() => setIsOpen((v) => !v), [])

  const value = useMemo(
    () => ({ isOpen, openMentor, closeMentor, toggleMentor }),
    [isOpen, openMentor, closeMentor, toggleMentor],
  )

  return <MentorUiContext.Provider value={value}>{children}</MentorUiContext.Provider>
}

export function useMentorUi(): MentorUiValue {
  const ctx = useContext(MentorUiContext)
  if (!ctx) {
    throw new Error("useMentorUi must be used within MentorUiProvider")
  }
  return ctx
}

/** Safe hook for pages outside the provider (falls back to local no-ops). */
export function useMentorUiOptional(): MentorUiValue | null {
  return useContext(MentorUiContext)
}
