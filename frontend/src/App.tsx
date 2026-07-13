import { Navigate, Route, Routes } from "react-router-dom"

import { PrivateRoute } from "@/components/PrivateRoute"
import { CareerMentorSidebar } from "@/components/CareerMentorSidebar"
import { AuthProvider } from "@/contexts/AuthContext"
import { ActiveResumeProvider } from "@/contexts/ActiveResumeContext"
import { JourneyProgressProvider } from "@/contexts/JourneyProgressContext"
import { MentorUiProvider } from "@/contexts/MentorUiContext"
import { PreviewWithState } from "@/dev/PreviewWithState"
import {
  mockCareerMatchesState,
  mockJobDescriptionUploadState,
  mockLearningRoadmapState,
  mockResumeReportState,
  mockSkillGapState,
  mockVirtualExperienceState,
} from "@/dev/previewMocks"
import { CareerMatchesPage } from "@/pages/CareerMatches"
import { DashboardPage } from "@/pages/Dashboard"
import { JobDescriptionUploadPage } from "@/pages/JobDescriptionUpload"
import { LandingPage } from "@/pages/LandingPage"
import { LearningRoadmapPage } from "@/pages/LearningRoadmap"
import { LoginPage } from "@/pages/Login"
import { PreviewPage } from "@/pages/Preview"
import { ResumeReportPage } from "@/pages/ResumeReport"
import { SkillGapPage } from "@/pages/SkillGap"
import { UploadResumePage } from "@/pages/UploadResume"
import { VirtualExperiencePage } from "@/pages/VirtualExperience"
import { SignupPage } from "@/pages/Signup"

export function App() {
  return (
    <AuthProvider>
      {/* ActiveResumeProvider must sit inside the router (BrowserRouter wraps
          App in main.tsx) so it can call useLocation to auto-extract resume IDs
          from URL params. The CareerMentorSidebar is mounted here — outside the
          Route tree — so it persists across all page navigations. */}
      <ActiveResumeProvider>
        <MentorUiProvider>
          <JourneyProgressProvider>
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/signup" element={<SignupPage />} />
              <Route
                path="/dashboard"
                element={
                  <PrivateRoute>
                    <DashboardPage />
                  </PrivateRoute>
                }
              />
              {/* Resume review flow — upload → AI review → report */}
              <Route
                path="/resume/upload"
                element={
                  <PrivateRoute>
                    <UploadResumePage />
                  </PrivateRoute>
                }
              />
              <Route
                path="/resume-report/:id"
                element={
                  <PrivateRoute>
                    <ResumeReportPage />
                  </PrivateRoute>
                }
              />
              {/* Career exploration flow — JD upload → matches → experience → skill gap */}
              <Route
                path="/job-descriptions/upload"
                element={
                  <PrivateRoute>
                    <JobDescriptionUploadPage />
                  </PrivateRoute>
                }
              />
              {/* Alias used by Resume Report "Upload Job Descriptions" CTA */}
              <Route
                path="/upload-jd"
                element={
                  <PrivateRoute>
                    <JobDescriptionUploadPage />
                  </PrivateRoute>
                }
              />
              <Route
                path="/career-matches/:resumeId"
                element={
                  <PrivateRoute>
                    <CareerMatchesPage />
                  </PrivateRoute>
                }
              />
              <Route
                path="/experience/:resumeId/:jobMatchId"
                element={
                  <PrivateRoute>
                    <VirtualExperiencePage />
                  </PrivateRoute>
                }
              />
              <Route
                path="/skill-gap"
                element={
                  <PrivateRoute>
                    <SkillGapPage />
                  </PrivateRoute>
                }
              />
              <Route
                path="/learning-roadmap"
                element={
                  <PrivateRoute>
                    <LearningRoadmapPage />
                  </PrivateRoute>
                }
              />

              {/* ── DEV ONLY: /preview showcase — remove before production ──
                  Delete: these routes, pages/Preview.tsx, and src/dev/          */}
              <Route path="/preview" element={<PreviewPage />} />
              <Route path="/preview/landing" element={<LandingPage />} />
              <Route path="/preview/resume-upload" element={<UploadResumePage />} />
              <Route
                path="/preview/resume-report"
                element={
                  <PreviewWithState state={mockResumeReportState}>
                    <ResumeReportPage />
                  </PreviewWithState>
                }
              />
              <Route
                path="/preview/upload-jd"
                element={
                  <PreviewWithState state={mockJobDescriptionUploadState}>
                    <JobDescriptionUploadPage />
                  </PreviewWithState>
                }
              />
              <Route
                path="/preview/career-matches"
                element={
                  <PreviewWithState state={mockCareerMatchesState}>
                    <CareerMatchesPage />
                  </PreviewWithState>
                }
              />
              <Route
                path="/preview/virtual-experience"
                element={
                  <PreviewWithState state={mockVirtualExperienceState}>
                    <VirtualExperiencePage />
                  </PreviewWithState>
                }
              />
              <Route
                path="/preview/skill-gap"
                element={
                  <PreviewWithState state={mockSkillGapState}>
                    <SkillGapPage />
                  </PreviewWithState>
                }
              />
              <Route
                path="/preview/learning-roadmap"
                element={
                  <PreviewWithState state={mockLearningRoadmapState}>
                    <LearningRoadmapPage />
                  </PreviewWithState>
                }
              />
              <Route path="/preview/dashboard" element={<DashboardPage />} />

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>

            {/* Mentor panel is global; Dashboard navbar opens it via MentorUiProvider.
                FAB is hidden on /dashboard (navbar ring is the trigger). */}
            <CareerMentorSidebar />
          </JourneyProgressProvider>
        </MentorUiProvider>
      </ActiveResumeProvider>
    </AuthProvider>
  )
}

export default App
