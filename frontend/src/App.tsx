import { lazy, Suspense, useEffect } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'

// Eagerly loaded (small, auth critical)
import LoginPage from '@/pages/auth/LoginPage'
import RegisterPage from '@/pages/auth/RegisterPage'

// Lazily loaded (split into separate chunks)
const DashboardPage = lazy(() => import('@/pages/DashboardPage'))
const ClassroomsPage = lazy(() => import('@/pages/classrooms/ClassroomsPage'))
const ClassroomDetailPage = lazy(() => import('@/pages/classrooms/ClassroomDetailPage'))
const AssignmentDetailPage = lazy(() => import('@/pages/assignments/AssignmentDetailPage'))
const CreateAssignmentPage = lazy(() => import('@/pages/assignments/CreateAssignmentPage'))
const GradingPage = lazy(() => import('@/pages/GradingPage'))
const GradesPage = lazy(() => import('@/pages/GradesPage'))
const ProfilePage = lazy(() => import('@/pages/ProfilePage'))
const AdminDashboardPage = lazy(() => import('@/pages/admin/AdminDashboardPage'))
const ClassroomAnalyticsPage = lazy(() => import('@/pages/classrooms/ClassroomAnalyticsPage'))

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[40vh]">
      <div className="w-5 h-5 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
    </div>
  )
}

// Scroll to top on route change
function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])
  return null
}

export default function App() {
  return (
    <>
      <ScrollToTop />
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected app shell */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/classrooms" element={<ClassroomsPage />} />
              <Route path="/classrooms/:id" element={<ClassroomDetailPage />} />
              <Route path="/classrooms/:id/analytics" element={<ClassroomAnalyticsPage />} />
              <Route path="/classrooms/:id/assignments/new" element={<CreateAssignmentPage />} />
              <Route path="/assignments/:id" element={<AssignmentDetailPage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/grades" element={<GradesPage />} />

              {/* Teacher-only */}
              <Route element={<ProtectedRoute roles={['teacher', 'admin']} />}>
                <Route path="/grading" element={<GradingPage />} />
              </Route>

              {/* Admin-only */}
              <Route element={<ProtectedRoute roles={['admin']} />}>
                <Route path="/admin" element={<AdminDashboardPage />} />
              </Route>
            </Route>
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
    </>
  )
}
