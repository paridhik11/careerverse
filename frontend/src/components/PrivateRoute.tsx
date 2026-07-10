import type { ReactNode } from "react"
import { Navigate } from "react-router-dom"

import { useAuth } from "@/hooks/useAuth"

/**
 * Route guard for authenticated-only pages. Waits for the initial GET /me
 * verification to finish before deciding, so a valid session isn't
 * incorrectly bounced to /login on a hard page refresh.
 */
export function PrivateRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <SessionCheckScreen />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function SessionCheckScreen() {
  return (
    <div
      className="flex h-screen w-screen items-center justify-center"
      style={{ background: "var(--cv-bg)" }}
    >
      <p
        className="text-gray-500"
        style={{ fontFamily: "var(--cv-font-sans)", fontSize: "var(--cv-text-small)" }}
      >
        Checking your session…
      </p>
    </div>
  )
}
