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
        className="text-center text-xs"
        style={{ fontFamily: "var(--cv-font-sans)", color: "var(--cv-ink-muted)" }}
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
    // Google's widget renders in its own iframe and always follows the
    // system/browser color scheme unless explicitly isolated — without this,
    // it can render with mismatched (e.g. stray blue-tinted) chrome on a dark
    // page regardless of the `theme` prop below.
    <div className="flex justify-center" style={{ colorScheme: "light" }}>
      <GoogleLogin
        onSuccess={handleSuccess}
        onError={() => onError("Google sign-in failed. Please try again.")}
        theme="filled_black"
        shape="pill"
        size="large"
        text="continue_with"
        width="304"
      />
    </div>
  )
}
