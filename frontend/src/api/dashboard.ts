import client from './client'
import type { Dashboard, StudentGrade, GradeTrend, ClassroomAnalytics } from '@/types'

export const dashboardApi = {
  get: () => client.get<Dashboard>('/me/dashboard').then(r => r.data),
  grades: () => client.get<StudentGrade[]>('/me/grades').then(r => r.data),
  gradeTrends: () => client.get<GradeTrend[]>('/me/grade-trends').then(r => r.data),
  classroomAnalytics: (classroomId: string) =>
    client.get<ClassroomAnalytics>(`/classrooms/${classroomId}/analytics`).then(r => r.data),
}
