import client from './client'
import type { Classroom, Enrollment, StudentListItem } from '@/types'

export const classroomsApi = {
  list: () => client.get<Enrollment[]>('/classrooms').then(r => r.data),

  get: (id: string) => client.get<Classroom>(`/classrooms/${id}`).then(r => r.data),

  create: (data: { name: string; subject_code: string; section: string; semester: string }) =>
    client.post<Classroom>('/classrooms', data).then(r => r.data),

  join: (join_code: string) =>
    client.post<Classroom>('/classrooms/join', { join_code }).then(r => r.data),

  update: (id: string, data: Partial<{ name: string; max_drafts: number; late_policy: string; ai_feedback: boolean }>) =>
    client.patch<Classroom>(`/classrooms/${id}`, data).then(r => r.data),

  students: (id: string) =>
    client.get<StudentListItem[]>(`/classrooms/${id}/students`).then(r => r.data),
}
