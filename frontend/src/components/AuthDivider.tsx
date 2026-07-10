/** "or" separator between the email/password form and the Google button. */
export function AuthDivider({ label = "or" }: { label?: string }) {
  return (
    <div className="my-4 flex items-center gap-3" role="separator">
      <span className="h-px flex-1 bg-gray-200" />
      <span
        className="text-xs text-gray-400"
        style={{ fontFamily: "var(--cv-font-sans)" }}
      >
        {label}
      </span>
      <span className="h-px flex-1 bg-gray-200" />
    </div>
  )
}
