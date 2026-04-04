// ─── Enums ────────────────────────────────────────────────────────────────────

export type UserRole = "student" | "teacher" | "admin";
export type SubmissionType = "text" | "file" | "both";
export type LatePolicy = "block" | "penalty" | "allow";
export type NotificationType =
  | "assignment_posted"
  | "deadline_reminder"
  | "grade_released"
  | "feedback_ready";

// ─── Core entities ────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  avatar_url?: string;
}

export interface ClassroomSettings {
  max_drafts: number;
  late_policy: LatePolicy;
  ai_feedback: boolean;
}

export interface Classroom {
  id: string;
  name: string;
  subject_code: string;
  section: string;
  semester: string;
  join_code: string;
  created_by: string;
  settings: ClassroomSettings;
}

export interface RubricLevel {
  excellent: string;
  good: string;
  average: string;
  poor: string;
}

export interface RubricCriterion {
  id: string;
  assignment_id: string;
  name: string;
  max_marks: number;
  order_index: number;
  levels: RubricLevel;
}

export interface Assignment {
  id: string;
  classroom_id: string;
  title: string;
  description: string;
  deadline: string;         // ISO timestamp
  total_marks: number;
  submission_type: SubmissionType;
  max_drafts: number;
  late_policy: LatePolicy;
  penalty_per_day: number;
  is_published: boolean;
  created_by: string;
  rubric_criteria: RubricCriterion[];
}

export interface Submission {
  id: string;
  assignment_id: string;
  student_id: string;
  content: string;
  file_url?: string;
  is_final: boolean;
  draft_number: number;
  is_late: boolean;
  submitted_at: string;
}

export interface AIFeedback {
  id: string;
  submission_id: string;
  criterion_id: string;
  estimated_score: number;
  feedback_text: string;
  generated_at: string;
}

export interface Grade {
  id: string;
  submission_id: string;
  criterion_id: string;
  score: number;
  level: "excellent" | "good" | "average" | "poor";
  feedback: string;
  graded_by: string;
  is_released: boolean;
}

export interface Notification {
  id: string;
  type: NotificationType;
  payload: Record<string, unknown>;
  is_read: boolean;
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}
