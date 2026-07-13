import * as React from "react"

import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "border-[var(--cv-border)] text-[var(--cv-ink)] file:text-[var(--cv-ink)] placeholder:text-[var(--cv-ink-muted)] selection:bg-[var(--cv-accent)] selection:text-white flex h-9 w-full min-w-0 rounded-md border bg-[var(--cv-surface-subtle)] px-3 py-1 text-base shadow-xs transition-[color,box-shadow] outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        "focus-visible:border-[var(--cv-accent)] focus-visible:ring-[var(--cv-accent)]/40 focus-visible:ring-[3px]",
        "aria-invalid:ring-destructive/30 aria-invalid:border-destructive",
        className
      )}
      {...props}
    />
  )
}

export { Input }
