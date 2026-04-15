// ============================================================
// ClassPulse — Shared TypeScript Types
// Mirrors the backend Pydantic schemas exactly.
// ============================================================

// --- Auth ---
export type UserRole = 'student' | 'teacher' | 'admin'

export interface User {
  id: string
  email: string
  full_name: string
  role: UserRole
  avatar_url?: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

// --- Classroom ---
export interface ClassroomSettings {
  max_drafts: number
  late_policy: 'block' | 'penalty' | 'allow'
  ai_feedback: boolean
}

export interface Classroom {
  id: string
  name: string
  subject_code: string
  section: string
  semester: string
  join_code: string
  created_by: string
  settings: ClassroomSettings
  created_at: string
}

export interface Enrollment {
  classroom_id: string
  role: 'student' | 'co_teacher'
  joined_at: string
  classroom: Classroom
}

export interface StudentListItem {
  user_id: string
  full_name: string
  email: string
  joined_at: string
}

// --- Assignment ---
export type SubmissionType = 'text' | 'file' | 'both'
export type LatePolicy = 'block' | 'penalty' | 'allow'

export interface RubricCriteria {
  id: string
  name: string
  max_marks: number
  order_index: number
  levels: Record<string, string>
}

export interface Assignment {
  id: string
  classroom_id: string
  title: string
  description?: string
  deadline: string
  total_marks: number
  submission_type: SubmissionType
  max_drafts: number
  late_policy: LatePolicy
  penalty_per_day?: number
  is_published: boolean
  created_by: string
  criteria: RubricCriteria[]
}

// --- Submission ---
export interface Submission {
  id: string
  assignment_id: string
  student_id: string
  student_name?: string
  student_email?: string
  content?: string
  file_url?: string
  is_final: boolean
  draft_number: number
  is_late: boolean
  similarity_score?: number
  similarity_flagged: boolean
  submitted_at: string
}

// --- Student Grade (from /me/grades) ---
export interface StudentGrade {
  id: string
  assignment_id: string
  submission_id: string
  assignment_title: string
  classroom_name: string
  total_score: number
  total_marks: number
  teacher_comments?: string
  graded_at: string
}

// --- Upcoming deadline (from dashboard) ---
export interface UpcomingDeadline {
  id: string
  title: string
  classroom_name: string
  deadline: string
  total_marks: number
}

// --- AI Feedback ---
export interface AIFeedback {
  id: string
  submission_id: string
  criterion_id: string
  criterion_name?: string
  criterion_max_marks?: number
  estimated_score: number
  feedback_text: string
  suggested_level: 'excellent' | 'good' | 'average' | 'poor'
  generated_at: string
}

// --- Grade ---
export interface Grade {
  id: string
  submission_id: string
  assignment_id: string
  student_id: string
  grader_id: string
  total_score: number
  teacher_comments?: string
  is_released: boolean
  graded_at: string
  criterion_grades?: CriterionScore[]
}

// --- Notification ---
export interface Notification {
  id: string
  user_id: string
  type: string
  title: string
  message: string
  is_read: boolean
  created_at: string
}

// --- Dashboard ---
export interface StudentDashboard {
  role: 'student'
  enrolled_classes: number
  active_assignments: number
  total_submissions: number
  avg_score?: number
  upcoming_deadlines: UpcomingDeadline[]
  recent_grades: { id: string; assignment_title: string; classroom_name: string; total_score: number; graded_at: string }[]
}

export interface TeacherDashboard {
  role: 'teacher'
  active_classes: number
  total_assignments: number
  pending_grades: number
}

export type Dashboard = StudentDashboard | TeacherDashboard

// --- Announcement ---
export interface Announcement {
  id: string
  classroom_id: string
  author_id: string
  author: {
    id: string
    full_name: string
    avatar_url: string | null
    role: string
  }
  title: string
  content: string
  pinned: boolean
  attachment_urls: string[]
  comment_count: number
  created_at: string
  updated_at: string
}

// --- Topic ---
export interface Topic {
  id: string
  classroom_id: string
  title: string
  order_index: number
  created_at: string
}

// --- Material ---
export interface Material {
  id: string
  classroom_id: string
  topic_id: string | null
  title: string
  material_type: 'link' | 'file' | 'video' | 'document'
  url: string | null
  description: string | null
  created_by: string
  created_at: string
}

// --- Comment ---
export interface Comment {
  id: string
  author_id: string
  author: {
    id: string
    full_name: string
    avatar_url: string | null
    role: string
  }
  content: string
  created_at: string
  updated_at: string
}

// --- Criterion Score ---
export interface CriterionScore {
  criterion_id: string
  score: number
  comment?: string
}

// --- Gradebook ---
export interface GradebookEntry {
  student_id: string
  student_name: string
  student_email: string
  has_submitted: boolean
  is_late: boolean
  score: number | null
  max_marks: number
  percentage: number | null
  letter_grade: string | null
  is_released: boolean
  is_ai_graded: boolean
}

// --- Grade Trend ---
export interface GradeTrend {
  assignment_title: string
  score: number
  total_marks: number
  pct: number
  graded_at: string
}

// --- Classroom Analytics ---
export interface ClassroomAnalytics {
  grade_distribution: { range: string; count: number }[]
  average_percentage: number
  total_grades: number
}

// --- File Upload ---
export interface FileUploadResponse {
  file_id: string
  filename: string
  url: string
  size: number
  mime_type: string
}

// --- WebSocket Events ---
export type WSEventType =
  | 'GRADE_RELEASED'
  | 'FEEDBACK_READY'
  | 'NEW_ASSIGNMENT'
  | 'PLAGIARISM_FLAG'
  | 'REMINDER'
  | 'AT_RISK'

export interface WSEvent {
  type: WSEventType
  title: string
  message: string
  [key: string]: unknown
}
