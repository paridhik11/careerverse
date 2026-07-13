/**
 * DEV ONLY — injects mock location.state so flow pages render without walking
 * the real upload → match → simulate pipeline. Delete with src/dev/.
 */

import { type ReactNode } from "react"
import { Navigate, useLocation } from "react-router-dom"

/**
 * On first mount, if the current location has no state, replace-navigate to
 * the same pathname with the provided mock state. Once state is present,
 * render children (the real page).
 */
export function PreviewWithState({
  state,
  children,
}: {
  state: unknown
  children: ReactNode
}) {
  const location = useLocation()

  if (location.state == null) {
    return <Navigate to={location.pathname} replace state={state} />
  }

  return <>{children}</>
}
