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
import { MIN_PASSWORD_LENGTH } from "@/services/auth"

interface FieldErrors {
  email?: string
  password?: string
}

export function SignupPage() {
  const { signup } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  function validate(): boolean {
    const errors: FieldErrors = {}

    if (!email.trim()) {
      errors.email = "Email is required."
    }

    if (password.length < MIN_PASSWORD_LENGTH) {
      errors.password = `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`
    }

    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError(null)

    // Validate client-side before hitting the network at all.
    if (!validate()) {
      return
    }

    setIsSubmitting(true)
    try {
      await signup(email, password)
      navigate("/dashboard", { replace: true })
    } catch (error) {
      // Show the backend's actual error (e.g. "An account with this email
      // already exists") rather than failing silently.
      setFormError(error instanceof Error ? error.message : "Something went wrong. Please try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthCard
      title="Create your account"
      subtitle="Start exploring careers that actually fit you."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="font-semibold" style={{ color: "var(--cv-accent)" }}>
            Log in
          </Link>
        </>
      }
    >
      {formError && (
        <div className="mb-4">
          <FormErrorBanner message={formError} />
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            aria-invalid={Boolean(fieldErrors.email)}
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          {fieldErrors.email && <FieldErrorText message={fieldErrors.email} />}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            aria-invalid={Boolean(fieldErrors.password)}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          {fieldErrors.password ? (
            <FieldErrorText message={fieldErrors.password} />
          ) : (
            <p className="text-xs text-gray-500">At least {MIN_PASSWORD_LENGTH} characters.</p>
          )}
        </div>

        <Button
          type="submit"
          disabled={isSubmitting}
          className="mt-2 text-white hover:opacity-90"
          style={{ background: "var(--cv-accent)" }}
        >
          {isSubmitting ? "Creating account…" : "Sign up"}
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

function FieldErrorText({ message }: { message: string }) {
  return <p className="text-xs text-red-600">{message}</p>
}
