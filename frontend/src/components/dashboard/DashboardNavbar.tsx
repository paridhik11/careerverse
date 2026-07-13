import { Link } from "react-router-dom"
import { Users } from "lucide-react"

import { useMentorUi } from "@/contexts/MentorUiContext"

/**
 * Top navbar: small logo (left), Home link, Career Mentor bot (right)
 * with a continuously rotating conic-gradient ring.
 */
export function DashboardNavbar() {
  const { openMentor, isOpen } = useMentorUi()

  return (
    <header
      className="fixed inset-x-0 top-0 z-40 flex h-[var(--cv-navbar-height)] items-center justify-between border-b px-4 md:px-6"
      style={{
        background: "rgba(11,10,20,0.85)",
        borderColor: "var(--cv-border)",
        backdropFilter: "blur(12px)",
      }}
    >
      <div className="flex items-center gap-6">
        <Link to="/dashboard" className="flex items-center gap-2 no-underline">
          <span
            style={{
              fontFamily: "var(--cv-font-serif)",
              fontSize: "1.15rem",
              fontWeight: 500,
              color: "var(--cv-ink)",
              letterSpacing: "-0.02em",
            }}
          >
            CareerVerse
          </span>
          <span
            className="rounded-full px-2 py-0.5"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "0.65rem",
              fontWeight: 700,
              background: "var(--cv-accent-muted)",
              color: "var(--cv-accent)",
              letterSpacing: "0.04em",
            }}
          >
            AI
          </span>
        </Link>

        <a
          href="#home"
          onClick={(e) => {
            e.preventDefault()
            document.getElementById("home")?.scrollIntoView({ behavior: "smooth" })
          }}
          className="hidden sm:inline"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-small)",
            fontWeight: 600,
            color: "var(--cv-ink-muted)",
            textDecoration: "none",
          }}
        >
          Home
        </a>
      </div>

      <button
        type="button"
        onClick={openMentor}
        aria-label="Open Career Mentor"
        aria-expanded={isOpen}
        className="relative flex size-11 items-center justify-center rounded-full outline-none focus-visible:ring-2 focus-visible:ring-[var(--cv-accent)]"
      >
        <span
          className="cv-mentor-ring absolute inset-0 rounded-full"
          style={{ padding: 2 }}
          aria-hidden
        />
        <span
          className="relative z-[1] flex size-9 items-center justify-center rounded-full"
          style={{ background: "var(--cv-bg-elevated)", boxShadow: "var(--cv-shadow-card)" }}
        >
          <Users size={18} strokeWidth={2} style={{ color: "var(--cv-accent)" }} />
        </span>
      </button>
    </header>
  )
}
