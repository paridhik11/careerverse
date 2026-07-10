import { GoogleLogin, type CredentialResponse } from "@react-oauth/google"

import { useAuth } from "@/hooks/useAuth"
import { getGoogleClientId } from "@/services/auth"

/**
 * "Continue with Google" button shared by Login and Signup. Both flows hit
 * the same backend endpoint (`POST /auth/google`) — the backend decides
 * whether that Google account maps to a brand-new user or an existing one.
 */
export function GoogleAuthButton({
  onAuthenticated,
  onError,
}: {
  onAuthenticated: () => void
  onError: (message: string) => void
}) {
  const { loginWithGoogle } = useAuth()

  // Renders nothing (rather than a button that errors on click) when the
  // OAuth client id isn't configured for this environment.
  if (!getGoogleClientId()) {
    return (
      <p
        className="text-center text-xs text-gray-400"
        style={{ fontFamily: "var(--cv-font-sans)" }}
      >
        Google sign-in isn&apos;t configured for this environment.
      </p>
    )
  }

  async function handleSuccess(response: CredentialResponse) {
    if (!response.credential) {
      onError("Google didn't return a valid credential. Please try again.")
      return
    }

    try {
      await loginWithGoogle(response.credential)
      onAuthenticated()
    } catch (error) {
      onError(error instanceof Error ? error.message : "Google sign-in failed. Please try again.")
    }
  }

  return (
    <div className="flex justify-center">
      <GoogleLogin
        onSuccess={handleSuccess}
        onError={() => onError("Google sign-in failed. Please try again.")}
        theme="outline"
        shape="pill"
        size="large"
        text="continue_with"
        width="304"
      />
    </div>
  )
}
