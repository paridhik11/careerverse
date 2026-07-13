/**
 * Dashboard — one continuous scrollable journey page.
 *
 * Sections (top → bottom):
 *   Home → Resume Upload → Resume Report (+ JD choice) → Career Match
 *   → Virtual Experience → Roadmap (skill gap + 3-month plan)
 *
 * Shell: top navbar (logo, Home, mentor ring) + left sidebar anchors.
 * JourneyProgressProvider lives in App.tsx so state survives /experience hops.
 */

import { useEffect } from "react"
import { useLocation } from "react-router-dom"

import { CareerMatchSection } from "@/components/dashboard/CareerMatchSection"
import { DashboardNavbar } from "@/components/dashboard/DashboardNavbar"
import { DashboardSidebar } from "@/components/dashboard/DashboardSidebar"
import { HomeSection } from "@/components/dashboard/HomeSection"
import { ResumeReportSection } from "@/components/dashboard/ResumeReportSection"
import { ResumeUploadSection } from "@/components/dashboard/ResumeUploadSection"
import { RoadmapSection } from "@/components/dashboard/RoadmapSection"
import { VirtualExperienceSection } from "@/components/dashboard/VirtualExperienceSection"
import { useJourneyProgress } from "@/contexts/JourneyProgressContext"

export function DashboardPage() {
  const location = useLocation()
  const { scrollToSection } = useJourneyProgress()

  useEffect(() => {
    const hash = location.hash.replace("#", "")
    if (hash) {
      // Allow layout to paint before smooth-scrolling to the target section
      requestAnimationFrame(() => {
        scrollToSection(hash as Parameters<typeof scrollToSection>[0])
      })
    }
  }, [location.hash, scrollToSection])

  return (
    <div className="min-h-screen w-full" style={{ background: "var(--cv-bg)" }}>
      <DashboardNavbar />
      <DashboardSidebar />

      <main className="pt-[var(--cv-navbar-height)] lg:pl-[var(--cv-sidebar-width)]">
        <HomeSection />
        <ResumeUploadSection />
        <ResumeReportSection />
        <CareerMatchSection />
        <VirtualExperienceSection />
        <RoadmapSection />
      </main>
    </div>
  )
}
