import { Navigate, Route, Routes } from "react-router-dom"

import { PrivateRoute } from "@/components/PrivateRoute"
import { CareerMentorSidebar } from "@/components/CareerMentorSidebar"
import { AuthProvider } from "@/contexts/AuthContext"
import { ActiveResumeProvider } from "@/contexts/ActiveResumeContext"
import { CareerMatchesPage } from "@/pages/CareerMatches"
import { DashboardPage } from "@/pages/Dashboard"
import { JobDescriptionUploadPage } from "@/pages/JobDescriptionUpload"
import { LandingPage } from "@/pages/LandingPage"
import { LearningRoadmapPage } from "@/pages/LearningRoadmap"
import { LoginPage } from "@/pages/Login"
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
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

        {/* The mentor sidebar floats above all pages; it's hidden on public
            routes because resumeId will be null and it renders nothing. */}
        <CareerMentorSidebar />
      </ActiveResumeProvider>
    </AuthProvider>
  )
}

export default App
