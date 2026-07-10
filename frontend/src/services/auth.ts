/**
 * Auth API client — talks to the backend's POST /signup, POST /login,
 * POST /auth/google, and GET /me endpoints. Keeps all fetch/URL details out
 * of pages and contexts.
 */

import { apiFetch } from "@/services/api"
import type { AuthResponse, AuthUser } from "@/types"

// Mirrors MIN_PASSWORD_LENGTH in backend/app/models/auth.py — keep in sync so
// the client-side check and the server-side validator agree.
export const MIN_PASSWORD_LENGTH = 8

/** The OAuth client ID used to render the "Continue with Google" button. */
export function getGoogleClientId(): string {
  return import.meta.env.VITE_GOOGLE_CLIENT_ID ?? ""
}

export function signupUser(email: string, password: string): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/signup", {
    method: "POST",
    body: { email, password },
    skipAuth: true,
  })
}

export function loginUser(email: string, password: string): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/login", {
    method: "POST",
    body: { email, password },
    skipAuth: true,
  })
}

/** Exchange a Google Identity Services ID token for our own JWT session. */
export function googleAuth(credential: string): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/auth/google", {
    method: "POST",
    body: { credential },
    skipAuth: true,
  })
}

export function getCurrentUser(options?: { suppressAuthRedirect?: boolean }): Promise<AuthUser> {
  return apiFetch<AuthUser>("/me", {
    method: "GET",
    suppressAuthRedirect: options?.suppressAuthRedirect,
  })
}
