import client from './client'
import type { Grade, GradebookEntry, Submission } from '@/types'

export const gradingApi = {
  queue: (assignmentId: string) =>
    client.get<Submission[]>(`/assignments/${assignmentId}/grading-queue`).then(r => r.data),

  grade: (submissionId: string, data: { total_score: number; teacher_comments?: string; is_released: boolean; criterion_scores?: { criterion_id: string; score: number; comment?: string }[] }) =>
    client.post<Grade>(`/submissions/${submissionId}/grade`, data).then(r => r.data),

  getGrade: (submissionId: string) =>
    client.get<Grade>(`/submissions/${submissionId}/grade`).then(r => r.data),

  releaseAllGrades: (assignmentId: string) =>
    client.post(`/assignments/${assignmentId}/grades/release-all`).then(r => r.data),

  gradebook: (assignmentId: string) =>
    client.get<GradebookEntry[]>(`/assignments/${assignmentId}/gradebook`).then(r => r.data),

  downloadPdf: (assignmentId: string, assignmentTitle: string) => {
    client.get(`/assignments/${assignmentId}/gradebook/pdf`, { responseType: 'blob' }).then(r => {
      const url = URL.createObjectURL(new Blob([r.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `gradebook-${assignmentTitle.replace(/\s+/g, '-')}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    })
  },
}
