/**
 * Dashboard — continuous scrollable journey.
 *
 * Sections:
 *   Home → Resume → Resume Analysis → Career Compatibility → Career Explorer
 *   → Virtual Experience → Learning Roadmap
 *
 * Career Mentor is always available via sidebar / navbar FAB.
 */

import { useEffect } from "react"
import { useLocation } from "react-router-dom"

import { CareerCompatibilitySection } from "@/components/dashboard/CareerCompatibilitySection"
import { CareerMatchSection } from "@/components/dashboard/CareerMatchSection"
import { DashboardNavbar } from "@/components/dashboard/DashboardNavbar"
import { DashboardSidebar } from "@/components/dashboard/DashboardSidebar"
import { HomeSection } from "@/components/dashboard/HomeSection"
import { ResumeAnalysisSection } from "@/components/dashboard/ResumeAnalysisSection"
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
        <ResumeAnalysisSection />
        <CareerCompatibilitySection />
        <CareerMatchSection />
        <VirtualExperienceSection />
        <RoadmapSection />
      </main>
    </div>
  )
}
