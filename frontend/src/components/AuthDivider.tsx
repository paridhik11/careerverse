/** "or" separator between the email/password form and the Google button. */
export function AuthDivider({ label = "or" }: { label?: string }) {
  return (
    <div className="my-4 flex items-center gap-3" role="separator">
      <span className="h-px flex-1" style={{ background: "var(--cv-border)" }} />
      <span
        className="text-xs"
        style={{ fontFamily: "var(--cv-font-sans)", color: "var(--cv-ink-muted)" }}
      >
        {label}
      </span>
      <span className="h-px flex-1" style={{ background: "var(--cv-border)" }} />
    </div>
  )
}
