import client from './client'
import type { Announcement } from '@/types'

export const announcementsApi = {
  list: (classroomId: string, skip = 0, limit = 20) =>
    client.get<Announcement[]>(`/classrooms/${classroomId}/announcements`, { params: { skip, limit } }).then(r => r.data),

  create: (classroomId: string, data: { title: string; content: string; pinned?: boolean }) =>
    client.post<Announcement>(`/classrooms/${classroomId}/announcements`, data).then(r => r.data),

  update: (id: string, data: { title?: string; content?: string; pinned?: boolean }) =>
    client.patch<Announcement>(`/announcements/${id}`, data).then(r => r.data),

  delete: (id: string) =>
    client.delete(`/announcements/${id}`),
}
