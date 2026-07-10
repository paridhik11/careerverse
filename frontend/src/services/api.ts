/**
 * Shared API client: base URL config, a fetch wrapper with auth headers, and a
 * 401 interceptor. Feature-specific services (e.g. `services/auth.ts`) should
 * call `apiFetch` instead of the raw `fetch` API so every request gets the
 * same auth handling for free.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000"

export function getApiBaseUrl(): string {
  return API_BASE_URL.replace(/\/$/, "")
}

// MVP tradeoff: the JWT lives in localStorage for simplicity, which is
// readable by any JS on the page (XSS risk). Post-MVP, this should move to a
// backend-set httpOnly + Secure + SameSite cookie so client-side JS can never
// read the token at all.
export const AUTH_TOKEN_STORAGE_KEY = "careerverse_auth_token"

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

type ApiFetchOptions = Omit<RequestInit, "body"> & {
  body?: unknown
  /** Skip attaching the stored bearer token (used by login/signup themselves). */
  skipAuth?: boolean
  /**
   * Skip the auto-redirect-to-/login on a 401 (the error is still thrown).
   * Used by AuthContext's silent on-load session check: an expired/invalid
   * token there just means "treat as logged out", not "force-navigate away
   * from whatever public page the user is currently on".
   */
  suppressAuthRedirect?: boolean
}

function extractErrorMessage(body: unknown): string | null {
  if (!body || typeof body !== "object") {
    return null
  }

  const detail = (body as { detail?: unknown }).detail

  if (typeof detail === "string") {
    return detail
  }

  // FastAPI/Pydantic validation errors come back as an array of
  // { loc, msg, type } objects rather than a single string.
  if (Array.isArray(detail)) {
    return detail
      .map((item) =>
        typeof item === "object" && item !== null && "msg" in item
          ? String((item as { msg: unknown }).msg)
          : String(item)
      )
      .join(" ")
  }

  return null
}

/**
 * Fetch wrapper used by every service module. It:
 * - Prefixes requests with the API base URL
 * - Attaches the stored JWT as a Bearer token (unless `skipAuth`)
 * - Serializes JSON bodies and parses JSON responses
 * - Intercepts any 401: clears the stored token and redirects to /login, so an
 *   expired/invalid session is never left silently broken in the UI.
 */
export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { body, skipAuth, suppressAuthRedirect, headers, ...rest } = options

  const requestHeaders = new Headers(headers)
  // FormData must let the browser set Content-Type (with multipart boundary).
  // Forcing application/json would break file uploads.
  const isFormData = typeof FormData !== "undefined" && body instanceof FormData
  if (!isFormData) {
    requestHeaders.set("Content-Type", "application/json")
  }

  if (!skipAuth) {
    const token = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)
    if (token) {
      requestHeaders.set("Authorization", `Bearer ${token}`)
    }
  }

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...rest,
    headers: requestHeaders,
    body: body === undefined ? undefined : isFormData ? body : JSON.stringify(body),
  })

  if (response.status === 401) {
    localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY)
    if (
      !suppressAuthRedirect &&
      typeof window !== "undefined" &&
      window.location.pathname !== "/login"
    ) {
      window.location.href = "/login"
    }
    throw new ApiError("Your session has expired. Please log in again.", 401)
  }

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null)
    const message = extractErrorMessage(errorBody) ?? `Request failed with status ${response.status}.`
    throw new ApiError(message, response.status)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}
