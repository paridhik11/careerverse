import {
  Briefcase,
  FileText,
  GitCompareArrows,
  Lock,
  Map,
  MessageCircle,
  Sparkles,
  Target,
} from "lucide-react"

import {
  useJourneyProgress,
  type DashboardSectionId,
  type JourneyUnlocks,
} from "@/contexts/JourneyProgressContext"
import { useMentorUi } from "@/contexts/MentorUiContext"

type NavItem =
  | {
      kind: "section"
      id: DashboardSectionId
      label: string
      icon: typeof FileText
      unlockKey: keyof JourneyUnlocks
    }
  | {
      kind: "mentor"
      id: "career-mentor"
      label: string
      icon: typeof MessageCircle
      unlockKey: "mentor"
    }

const NAV_ITEMS: NavItem[] = [
  { kind: "section", id: "resume", label: "Resume", icon: FileText, unlockKey: "resumeUpload" },
  {
    kind: "section",
    id: "resume-analysis",
    label: "Resume Analysis",
    icon: Target,
    unlockKey: "resumeAnalysis",
  },
  {
    kind: "section",
    id: "career-compatibility",
    label: "Career Compatibility",
    icon: GitCompareArrows,
    unlockKey: "careerCompatibility",
  },
  {
    kind: "section",
    id: "career-match",
    label: "Career Explorer",
    icon: Briefcase,
    unlockKey: "careerMatch",
  },
  {
    kind: "section",
    id: "virtual-experience",
    label: "Virtual Experience",
    icon: Sparkles,
    unlockKey: "virtualExperience",
  },
  {
    kind: "section",
    id: "roadmap",
    label: "Learning Roadmap",
    icon: Map,
    unlockKey: "roadmap",
  },
  {
    kind: "mentor",
    id: "career-mentor",
    label: "Career Mentor",
    icon: MessageCircle,
    unlockKey: "mentor",
  },
]

/**
 * Left sidebar — journey anchors. Staged unlocks:
 * Resume → Analysis / Compatibility / Explorer → VE → Roadmap.
 * Career Mentor is always available.
 */
export function DashboardSidebar() {
  const { unlocks, scrollToSection } = useJourneyProgress()
  const { openMentor } = useMentorUi()

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
              onClick={() => {
                if (!unlocked) return
                if (item.kind === "mentor") {
                  openMentor()
                  return
                }
                scrollToSection(item.id)
              }}
              className="flex items-center gap-3 rounded-full px-3 py-2.5 text-left transition-colors duration-150 disabled:cursor-not-allowed"
              style={{
                fontFamily: "var(--cv-font-sans)",
                fontSize: "var(--cv-text-small)",
                fontWeight: unlocked ? 600 : 500,
                color: unlocked ? "var(--cv-sidebar-active)" : "var(--cv-status-locked)",
                background: "transparent",
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
