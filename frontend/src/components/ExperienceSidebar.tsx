/**
 * ExperienceSidebar — left navigation panel for VirtualExperiencePage.
 *
 * Shows: Overview → Task 1 … Task N → Finish.
 * Completed tasks display a checkmark, the active section is highlighted with
 * the indigo accent, locked tasks show a muted label.
 */

import { motion } from "framer-motion"
import { CheckCircle2, Flag, LayoutDashboard, Lock } from "lucide-react"

const EASE = [0.22, 1, 0.36, 1] as const

/* ─── Types ─────────────────────────────────────────────────────────────── */

export type SidebarSection = "overview" | number | "finish"

interface SidebarItem {
  id: SidebarSection
  label: string
  isLocked: boolean
  isCompleted: boolean
}

interface ExperienceSidebarProps {
  jobTitle: string
  totalTasks: number
  activeSection: SidebarSection
  completedTasks: number[]
  onNavigate: (section: SidebarSection) => void
}

/* ─── Component ─────────────────────────────────────────────────────────── */

export function ExperienceSidebar({
  jobTitle,
  totalTasks,
  activeSection,
  completedTasks,
  onNavigate,
}: ExperienceSidebarProps) {
  const allTasksDone = completedTasks.length === totalTasks

  const items: SidebarItem[] = [
    { id: "overview", label: "Overview", isLocked: false, isCompleted: false },
    ...Array.from({ length: totalTasks }, (_, i) => {
      const taskNumber = i + 1
      const prevDone = i === 0 || completedTasks.includes(i - 1)
      return {
        id: i as SidebarSection,
        label: `Task ${taskNumber}`,
        isLocked: !prevDone && !completedTasks.includes(i),
        isCompleted: completedTasks.includes(i),
      }
    }),
    { id: "finish", label: "Finish", isLocked: !allTasksDone, isCompleted: allTasksDone },
  ]

  return (
    <motion.aside
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, ease: EASE }}
      className="flex w-56 shrink-0 flex-col gap-1 rounded-[var(--cv-radius-main)] bg-white p-4"
      style={{ boxShadow: "var(--cv-shadow-card)" }}
    >
      {/* Role label */}
      <div className="mb-3 px-1">
        <p
          style={{
            fontFamily: "var(--cv-font-sans)",
            fontSize: "var(--cv-text-caption)",
            fontWeight: 700,
            color: "#9CA3AF",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
          }}
        >
          Virtual Experience
        </p>
        <h2
          className="mt-0.5 leading-tight text-gray-900"
          style={{
            fontFamily: "var(--cv-font-serif)",
            fontSize: "var(--cv-text-small)",
            fontWeight: 500,
          }}
        >
          {jobTitle}
        </h2>
      </div>

      <div className="h-px bg-gray-100" aria-hidden />
      <div className="mt-1 flex flex-col gap-0.5">
        {items.map((item) => (
          <SidebarNavItem
            key={String(item.id)}
            item={item}
            isActive={activeSection === item.id}
            onNavigate={onNavigate}
          />
        ))}
      </div>
    </motion.aside>
  )
}

/* ─── Single nav item ────────────────────────────────────────────────────── */

function SidebarNavItem({
  item,
  isActive,
  onNavigate,
}: {
  item: SidebarItem
  isActive: boolean
  onNavigate: (id: SidebarSection) => void
}) {
  const Icon =
    item.id === "overview"
      ? LayoutDashboard
      : item.id === "finish"
        ? Flag
        : null

  return (
    <button
      type="button"
      disabled={item.isLocked}
      onClick={() => !item.isLocked && onNavigate(item.id)}
      className="flex w-full items-center gap-2.5 rounded-[var(--cv-radius-card)] px-3 py-2.5 text-left transition-colors duration-150"
      style={{
        background: isActive ? "var(--cv-accent-muted)" : "transparent",
        cursor: item.isLocked ? "default" : "pointer",
      }}
    >
      {/* Icon / indicator */}
      <div className="shrink-0">
        {item.isCompleted ? (
          <CheckCircle2
            size={16}
            strokeWidth={2}
            style={{ color: "#22C55E" }}
            aria-hidden
          />
        ) : item.isLocked ? (
          <Lock size={14} strokeWidth={1.8} style={{ color: "#D1D5DB" }} aria-hidden />
        ) : Icon ? (
          <Icon
            size={16}
            strokeWidth={isActive ? 2 : 1.6}
            style={{ color: isActive ? "var(--cv-accent)" : "#9CA3AF" }}
            aria-hidden
          />
        ) : (
          <span
            className="flex size-4 items-center justify-center rounded-full"
            style={{
              background: isActive ? "var(--cv-accent)" : "#E5E7EB",
            }}
            aria-hidden
          >
            <span
              style={{
                fontFamily: "var(--cv-font-sans)",
                fontSize: "0.6rem",
                fontWeight: 700,
                color: isActive ? "#fff" : "#9CA3AF",
              }}
            >
              {typeof item.id === "number" ? item.id + 1 : ""}
            </span>
          </span>
        )}
      </div>

      {/* Label */}
      <span
        style={{
          fontFamily: "var(--cv-font-sans)",
          fontSize: "var(--cv-text-small)",
          fontWeight: isActive ? 700 : 500,
          color: item.isLocked
            ? "#D1D5DB"
            : isActive
              ? "var(--cv-accent)"
              : item.isCompleted
                ? "#374151"
                : "#6B7280",
        }}
      >
        {item.label}
      </span>
    </button>
  )
}
