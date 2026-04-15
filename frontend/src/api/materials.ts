import client from './client'
import type { Material } from '@/types'

export const materialsApi = {
  list: (classroomId: string) =>
    client.get<Material[]>(`/classrooms/${classroomId}/materials`).then(r => r.data),

  create: (classroomId: string, data: {
    title: string
    material_type: string
    url?: string
    description?: string
    topic_id?: string
    file_id?: string
  }) =>
    client.post<Material>(`/classrooms/${classroomId}/materials`, data).then(r => r.data),

  delete: (id: string) =>
    client.delete(`/materials/${id}`),
}
