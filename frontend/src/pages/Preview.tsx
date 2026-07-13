/**
 * DEV ONLY — temporary component / page showcase hub.
 *
 * Removal checklist (before production):
 *   1. Delete this file (pages/Preview.tsx)
 *   2. Delete the src/dev/ folder
 *   3. Remove /preview* routes from App.tsx
 *   4. Revert optional skillGap location.state support in SkillGap.tsx if undesired
 */

import { Link } from "react-router-dom"
import {
  Briefcase,
  ClipboardList,
  FileText,
  FlaskConical,
  LayoutDashboard,
  Map,
  Sparkles,
  Target,
  Upload,
} from "lucide-react"
import type { LucideIcon } from "lucide-react"

import { type ColorVariant } from "@/components/JourneyCard"

type PreviewLink = {
  title: string
  description: string
  to: string
  colorVariant: ColorVariant
  icon: LucideIcon
  needsMockState: boolean
}

const PREVIEW_LINKS: PreviewLink[] = [
  {
    title: "Landing",
    description: "Public marketing home — hero, features, CTA.",
    to: "/preview/landing",
    colorVariant: "lavender",
    icon: Sparkles,
    needsMockState: false,
  },
  {
    title: "Resume Upload",
    description: "Upload + review flow entry (live API if backend is up).",
    to: "/preview/resume-upload",
    colorVariant: "amber",
    icon: Upload,
    needsMockState: false,
  },
  {
    title: "Resume Report",
    description: "AI review results with mock report payload.",
    to: "/preview/resume-report",
    colorVariant: "amber",
    icon: FileText,
    needsMockState: true,
  },
  {
    title: "Upload JD",
    description: "Job description upload step with mock resumeId.",
    to: "/preview/upload-jd",
    colorVariant: "sage",
    icon: ClipboardList,
    needsMockState: true,
  },
  {
    title: "Career Matches",
    description: "Top-3 matches UI with mock JobMatch list.",
    to: "/preview/career-matches",
    colorVariant: "sage",
    icon: Briefcase,
    needsMockState: true,
  },
  {
    title: "Virtual Experience",
    description: "Day-in-role simulation with mock tasks & feedback.",
    to: "/preview/virtual-experience",
    colorVariant: "lavender",
    icon: FlaskConical,
    needsMockState: true,
  },
  {
    title: "Skill Gap",
    description: "Gap analysis UI with preloaded mock skillGap (no API).",
    to: "/preview/skill-gap",
    colorVariant: "sky",
    icon: Target,
    needsMockState: true,
  },
  {
    title: "Learning Roadmap",
    description: "3-month plan UI with mock roadmap content.",
    to: "/preview/learning-roadmap",
    colorVariant: "sky",
    icon: Map,
    needsMockState: true,
  },
  {
    title: "Dashboard",
    description: "Continuous scroll journey (Home → Resume → Match → Experience → Roadmap).",
    to: "/preview/dashboard",
    colorVariant: "lavender",
    icon: LayoutDashboard,
    needsMockState: false,
  },
]

const cardBg: Record<ColorVariant, string> = {
  amber: "bg-[var(--cv-card-surface)]",
  sage: "bg-[var(--cv-card-surface)]",
  sky: "bg-[var(--cv-card-surface)]",
  lavender: "bg-[var(--cv-card-surface)]",
}

const iconBg: Record<ColorVariant, string> = {
  amber: "bg-[var(--cv-accent-soft)]",
  sage: "bg-[var(--cv-accent-soft)]",
  sky: "bg-[var(--cv-accent-soft)]",
  lavender: "bg-[var(--cv-accent-soft)]",
}

const iconColor: Record<ColorVariant, string> = {
  amber: "text-[var(--cv-accent)]",
  sage: "text-[var(--cv-accent)]",
  sky: "text-[var(--cv-accent)]",
  lavender: "text-[var(--cv-accent)]",
}

export function PreviewPage() {
  return (
    <div
      className="min-h-screen w-full px-4 py-10 md:px-8 lg:px-10"
      style={{ background: "var(--cv-bg)" }}
    >
      <div className="mx-auto max-w-3xl">
        <div
          className="mb-8 rounded-[1.25rem] px-5 py-4"
          style={{ background: "rgba(245, 158, 11, 0.14)", color: "#FBBF24" }}
        >
          <p
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-small)",
              fontWeight: 600,
            }}
          >
            Development only — page showcase
          </p>
          <p
            className="mt-1 opacity-90"
            style={{
              fontFamily: "var(--cv-font-sans)",
              fontSize: "var(--cv-text-caption)",
            }}
          >
            Remove <code className="font-medium">/preview</code> routes,{" "}
            <code className="font-medium">pages/Preview.tsx</code>, and{" "}
            <code className="font-medium">src/dev/</code> before production.
            Preview routes skip auth so UI can be reviewed independently.
          </p>
        </div>

        <h1
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-h1)",
            fontWeight: 400,
            lineHeight: 1.15,
            color: "var(--cv-ink)",
          }}
        >
          Component showcase
        </h1>
        <p
          className="mt-2"
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-body)",
            lineHeight: 1.6,
            color: "var(--cv-ink-muted)",
          }}
        >
          Open any major screen with mock navigation state where the real flow
          would normally pass data via <code>location.state</code>.
        </p>

        <ul className="mt-8 flex flex-col gap-3">
          {PREVIEW_LINKS.map((item) => {
            const Icon = item.icon
            return (
              <li key={item.to}>
                <Link
                  to={item.to}
                  className={`cv-card flex items-start gap-4 p-6 transition-shadow duration-200 hover:shadow-[var(--cv-shadow-main)] ${cardBg[item.colorVariant]}`}
                >
                  <div
                    className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full ${iconBg[item.colorVariant]}`}
                  >
                    <Icon
                      className={`h-5 w-5 ${iconColor[item.colorVariant]}`}
                      strokeWidth={1.8}
                    />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        style={{
                          fontFamily: "var(--cv-font-serif)",
                          fontSize: "var(--cv-text-h3)",
                          fontWeight: 500,
                          color: "var(--cv-ink)",
                        }}
                      >
                        {item.title}
                      </span>
                      {item.needsMockState && (
                        <span
                          className="rounded-full px-2.5 py-0.5"
                          style={{
                            fontFamily: "var(--cv-font-sans)",
                            fontSize: "var(--cv-text-caption)",
                            fontWeight: 500,
                            background: "var(--cv-surface-subtle)",
                            color: "var(--cv-accent-2)",
                          }}
                        >
                          mock state
                        </span>
                      )}
                    </div>
                    <p
                      className="mt-1"
                      style={{
                        fontFamily: "var(--cv-font-sans)",
                        fontSize: "var(--cv-text-small)",
                        lineHeight: 1.5,
                        color: "var(--cv-ink-muted)",
                      }}
                    >
                      {item.description}
                    </p>
                    <p
                      className="mt-2"
                      style={{
                        fontFamily: "var(--cv-font-sans)",
                        fontSize: "var(--cv-text-caption)",
                        color: "var(--cv-ink-muted)",
                      }}
                    >
                      {item.to}
                    </p>
                  </div>
                </Link>
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}
