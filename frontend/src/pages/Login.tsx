import { useState, type FormEvent } from "react"
import { Link, useNavigate } from "react-router-dom"

import { AuthCard } from "@/components/AuthCard"
import { AuthDivider } from "@/components/AuthDivider"
import { FormErrorBanner } from "@/components/FormErrorBanner"
import { GoogleAuthButton } from "@/components/GoogleAuthButton"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuth } from "@/hooks/useAuth"

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [formError, setFormError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError(null)
    setIsSubmitting(true)

    try {
      await login(email, password)
      navigate("/dashboard", { replace: true })
    } catch (error) {
      // Show the backend's actual error (e.g. "Incorrect email or password")
      // rather than failing silently.
      setFormError(error instanceof Error ? error.message : "Something went wrong. Please try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthCard
      title="Welcome back"
      subtitle="Log in to continue your career journey."
      footer={
        <>
          Don&apos;t have an account?{" "}
          <Link to="/signup" className="font-semibold" style={{ color: "var(--cv-accent)" }}>
            Sign up
          </Link>
        </>
      }
    >
      {formError && (
        <div className="mb-4">
          <FormErrorBanner message={formError} />
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>

        <Button
          type="submit"
          disabled={isSubmitting}
          className="mt-2 text-white hover:opacity-90"
          style={{ background: "var(--cv-accent)" }}
        >
          {isSubmitting ? "Logging in…" : "Log in"}
        </Button>
      </form>

      <AuthDivider />

      <GoogleAuthButton
        onAuthenticated={() => navigate("/dashboard", { replace: true })}
        onError={setFormError}
      />
    </AuthCard>
  )
}
