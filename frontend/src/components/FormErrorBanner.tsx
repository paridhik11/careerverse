/**
 * Surfaces a backend error message (wrong password, duplicate email, etc.)
 * inline in the form instead of failing silently.
 */
export function FormErrorBanner({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="rounded-xl px-4 py-3 text-sm"
      style={{ background: "#FEE2E2", color: "#B91C1C", fontFamily: "var(--cv-font-sans)" }}
    >
      {message}
    </div>
  )
}
