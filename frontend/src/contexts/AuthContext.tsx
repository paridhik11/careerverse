import { createContext, useCallback, useEffect, useState, type ReactNode } from "react"
import { useNavigate } from "react-router-dom"

import { getCurrentUser, googleAuth, loginUser, signupUser } from "@/services/auth"
import { AUTH_TOKEN_STORAGE_KEY } from "@/services/api"
import type { AuthUser } from "@/types"

export interface AuthContextValue {
  user: AuthUser | null
  isAuthenticated: boolean
  /** True while the initial GET /me verification (on app load) is in flight. */
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string) => Promise<void>
  /** `credential` is the ID token JWT from Google Identity Services. */
  loginWithGoogle: (credential: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()

  // A token in localStorage only means "we were logged in at some point" — it
  // could be expired, forged, or revoked. Always confirm it with the backend
  // before trusting it, instead of decoding it client-side and moving on.
  useEffect(() => {
    let isMounted = true

    async function verifyStoredSession() {
      const token = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)
      if (!token) {
        if (isMounted) setIsLoading(false)
        return
      }

      try {
        // suppressAuthRedirect: an expired/invalid token here just means "not
        // logged in" — it shouldn't force-navigate away from whatever public
        // page (e.g. the landing page) the user happens to be on.
        const currentUser = await getCurrentUser({ suppressAuthRedirect: true })
        if (isMounted) setUser(currentUser)
      } catch {
        localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY)
        if (isMounted) setUser(null)
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    verifyStoredSession()
    return () => {
      isMounted = false
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const response = await loginUser(email, password)
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, response.access_token)
    setUser(response.user)
  }, [])

  const signup = useCallback(async (email: string, password: string) => {
    const response = await signupUser(email, password)
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, response.access_token)
    setUser(response.user)
  }, [])

  const loginWithGoogle = useCallback(async (credential: string) => {
    const response = await googleAuth(credential)
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, response.access_token)
    setUser(response.user)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY)
    setUser(null)
    navigate("/login", { replace: true })
  }, [navigate])

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: user !== null,
        isLoading,
        login,
        signup,
        loginWithGoogle,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
