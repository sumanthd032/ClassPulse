import client from './client'
import type { Assignment } from '@/types'

export const assignmentsApi = {
  list: (classroomId: string) =>
    client.get<Assignment[]>(`/classrooms/${classroomId}/assignments`).then(r => r.data),

  get: (id: string) => client.get<Assignment>(`/assignments/${id}`).then(r => r.data),

  create: (classroomId: string, data: {
    title: string
    description?: string
    deadline: string
    total_marks: number
    submission_type: string
    max_drafts: number
    late_policy: string
    penalty_per_day?: number
    is_published: boolean
    criteria: { name: string; max_marks: number; levels: Record<string, string> }[]
  }) => client.post<Assignment>(`/classrooms/${classroomId}/assignments`, data).then(r => r.data),

  update: (id: string, data: Partial<{ title: string; description: string; deadline: string; is_published: boolean }>) =>
    client.patch<Assignment>(`/assignments/${id}`, data).then(r => r.data),
}
