import {
  Briefcase,
  FileText,
  Lock,
  Map,
  Sparkles,
} from "lucide-react"

import {
  useJourneyProgress,
  type DashboardSectionId,
} from "@/contexts/JourneyProgressContext"

type NavItem = {
  id: DashboardSectionId
  label: string
  icon: typeof FileText
  unlockKey: "resumeUpload" | "careerMatch" | "virtualExperience" | "roadmap"
}

const NAV_ITEMS: NavItem[] = [
  { id: "resume", label: "Resume", icon: FileText, unlockKey: "resumeUpload" },
  { id: "career-match", label: "Career Match", icon: Briefcase, unlockKey: "careerMatch" },
  { id: "virtual-experience", label: "Virtual Experience", icon: Sparkles, unlockKey: "virtualExperience" },
  { id: "roadmap", label: "Roadmap", icon: Map, unlockKey: "roadmap" },
]

/**
 * Left sidebar — 4 journey anchors. Locked items are dimmed with a lock icon
 * and do not scroll until unlocked.
 */
export function DashboardSidebar() {
  const { unlocks, scrollToSection } = useJourneyProgress()

  return (
    <aside
      className="fixed left-0 top-[var(--cv-navbar-height)] z-30 hidden h-[calc(100vh-var(--cv-navbar-height))] w-[var(--cv-sidebar-width)] flex-col border-r px-3 py-6 lg:flex"
      style={{
        background: "var(--cv-sidebar)",
        borderColor: "var(--cv-border)",
      }}
      aria-label="Journey navigation"
    >
      <p
        className="mb-4 px-3"
        style={{
          fontFamily: "var(--cv-font-sans)",
          fontSize: "var(--cv-text-caption)",
          fontWeight: 600,
          color: "var(--cv-ink-muted)",
          letterSpacing: "0.08em",
          textTransform: "uppercase",
        }}
      >
        Your journey
      </p>

      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const unlocked = unlocks[item.unlockKey]
          const Icon = item.icon

          return (
            <button
              key={item.id}
              type="button"
              disabled={!unlocked}
              onClick={() => unlocked && scrollToSection(item.id)}
              className="flex items-center gap-3 rounded-full px-3 py-2.5 text-left transition-colors duration-150 disabled:cursor-not-allowed"
              style={{
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-small)",
                fontWeight: unlocked ? 600 : 500,
                color: unlocked ? "var(--cv-sidebar-active)" : "var(--cv-status-locked)",
                background: unlocked ? "transparent" : "transparent",
                opacity: unlocked ? 1 : 0.55,
              }}
              onMouseEnter={(e) => {
                if (unlocked) e.currentTarget.style.background = "var(--cv-accent-muted)"
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "transparent"
              }}
            >
              <Icon size={18} strokeWidth={unlocked ? 2 : 1.6} aria-hidden />
              <span className="flex-1">{item.label}</span>
              {!unlocked && <Lock size={14} strokeWidth={2} aria-hidden />}
            </button>
          )
        })}
      </nav>
    </aside>
  )
}
