import client from './client'
import type { Comment } from '@/types'

export const commentsApi = {
  listForAnnouncement: (announcementId: string) =>
    client.get<Comment[]>(`/announcements/${announcementId}/comments`).then(r => r.data),

  addToAnnouncement: (announcementId: string, content: string) =>
    client.post<Comment>(`/announcements/${announcementId}/comments`, { content }).then(r => r.data),

  listForAssignment: (assignmentId: string) =>
    client.get<Comment[]>(`/assignments/${assignmentId}/comments`).then(r => r.data),

  addToAssignment: (assignmentId: string, content: string) =>
    client.post<Comment>(`/assignments/${assignmentId}/comments`, { content }).then(r => r.data),

  delete: (id: string) =>
    client.delete(`/comments/${id}`),
}
