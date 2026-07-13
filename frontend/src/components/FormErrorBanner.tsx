/**
 * Surfaces a backend error message (wrong password, duplicate email, etc.)
 * inline in the form instead of failing silently.
 */
export function FormErrorBanner({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="rounded-xl border px-4 py-3 text-sm"
      style={{
        background: "rgba(239, 68, 68, 0.12)",
        borderColor: "rgba(239, 68, 68, 0.28)",
        color: "#FCA5A5",
        fontFamily: "var(--cv-font-sans)",
      }}
    >
      {message}
    </div>
  )
}
