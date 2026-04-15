import client from './client'
import type { Topic } from '@/types'

export const topicsApi = {
  list: (classroomId: string) =>
    client.get<Topic[]>(`/classrooms/${classroomId}/topics`).then(r => r.data),

  create: (classroomId: string, data: { title: string; order_index?: number }) =>
    client.post<Topic>(`/classrooms/${classroomId}/topics`, data).then(r => r.data),

  update: (id: string, data: { title?: string; order_index?: number }) =>
    client.patch<Topic>(`/topics/${id}`, data).then(r => r.data),

  delete: (id: string) =>
    client.delete(`/topics/${id}`),
}
