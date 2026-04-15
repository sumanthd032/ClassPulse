import client from './client'

export interface PlatformStats {
  total_users: number
  total_students: number
  total_teachers: number
  total_classrooms: number
  total_assignments: number
  total_submissions: number
  total_grades: number
  pending_grades: number
}

export interface AdminUser {
  id: string
  email: string
  full_name: string
  role: string
  avatar_url?: string
}

export interface AdminClassroom {
  id: string
  name: string
  subject_code: string
  section: string
  semester: string
  student_count: number
  created_at: string
}

export const adminApi = {
  stats: () => client.get<PlatformStats>('/admin/stats').then(r => r.data),

  users: (params?: { role?: string; limit?: number; offset?: number }) =>
    client.get<{ total: number; items: AdminUser[] }>('/admin/users', { params }).then(r => r.data),

  classrooms: (params?: { limit?: number; offset?: number }) =>
    client.get<{ total: number; items: AdminClassroom[] }>('/admin/classrooms', { params }).then(r => r.data),
}
