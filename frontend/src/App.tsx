/**
 * Root App component — sets up React Router, React Query, and Toaster.
 *
 * Routing strategy:
 * - Public routes: /login, /register (accessible without auth)
 * - Protected routes: wrapped in ProtectedRoute component that checks auth state.
 * - Role-based redirect: teachers go to /teacher, students go to /student.
 *
 * React Query QueryClient:
 * - staleTime: 30s — data is considered fresh for 30 seconds (no refetch on every mount)
 * - retry: 1 — retry failed requests once before showing error
 */

import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";

import { useAuthStore } from "@/store/authStore";
import LoginPage from "@/pages/auth/LoginPage";
import RegisterPage from "@/pages/auth/RegisterPage";
import StudentDashboard from "@/pages/student/StudentDashboard";
import ClassroomPage from "@/pages/student/ClassroomPage";
import AssignmentPage from "@/pages/student/AssignmentPage";
import TeacherDashboard from "@/pages/teacher/TeacherDashboard";
import AssignmentCreatePage from "@/pages/teacher/AssignmentCreatePage";
import GradingPage from "@/pages/teacher/GradingPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

function ProtectedRoute({ children, allowedRoles }: {
  children: React.ReactNode;
  allowedRoles?: string[];
}) {
  const { user, isAuthenticated } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated()) {
    // Redirect to login, preserving the intended URL so we can redirect back after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    // Wrong role — redirect to their dashboard
    return <Navigate to={user.role === "teacher" ? "/teacher" : "/student"} replace />;
  }

  return <>{children}</>;
}

function RootRedirect() {
  const { user, isAuthenticated } = useAuthStore();
  if (!isAuthenticated()) return <Navigate to="/login" replace />;
  return <Navigate to={user?.role === "teacher" ? "/teacher" : "/student"} replace />;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Student routes */}
          <Route path="/student" element={
            <ProtectedRoute allowedRoles={["student"]}>
              <StudentDashboard />
            </ProtectedRoute>
          } />
          <Route path="/student/classroom/:classroomId" element={
            <ProtectedRoute allowedRoles={["student"]}>
              <ClassroomPage />
            </ProtectedRoute>
          } />
          <Route path="/student/assignment/:assignmentId" element={
            <ProtectedRoute allowedRoles={["student"]}>
              <AssignmentPage />
            </ProtectedRoute>
          } />

          {/* Teacher routes */}
          <Route path="/teacher" element={
            <ProtectedRoute allowedRoles={["teacher", "admin"]}>
              <TeacherDashboard />
            </ProtectedRoute>
          } />
          <Route path="/teacher/classroom/:classroomId/create-assignment" element={
            <ProtectedRoute allowedRoles={["teacher", "admin"]}>
              <AssignmentCreatePage />
            </ProtectedRoute>
          } />
          <Route path="/teacher/grade/:assignmentId" element={
            <ProtectedRoute allowedRoles={["teacher", "admin"]}>
              <GradingPage />
            </ProtectedRoute>
          } />

          {/* Root → redirect based on role */}
          <Route path="/" element={<RootRedirect />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" />
    </QueryClientProvider>
  );
}
