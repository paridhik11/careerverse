import { useContext } from "react"

import { AuthContext } from "@/contexts/AuthContext"

/**
 * Access the current auth state and actions (`login`, `signup`, `logout`).
 * Must be called from a component rendered inside `<AuthProvider>`.
 */
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
