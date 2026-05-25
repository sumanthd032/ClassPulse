import client from './client'
import type { Submission, AIFeedback } from '@/types'

export const submissionsApi = {
  submitDraft: (assignmentId: string, data: { content?: string; file_url?: string; attachments?: string[] }) =>
    client.post<Submission>(`/assignments/${assignmentId}/drafts`, data).then(r => r.data),

  submitFinal: (assignmentId: string, data: { content?: string; file_url?: string; attachments?: string[] }) =>
    client.post<Submission>(`/assignments/${assignmentId}/final`, data).then(r => r.data),

  mine: (assignmentId: string) =>
    client.get<Submission[]>(`/assignments/${assignmentId}/my-submission`).then(r => r.data),

  all: (assignmentId: string) =>
    client.get<Submission[]>(`/assignments/${assignmentId}/submissions`).then(r => r.data),

  get: (id: string) => client.get<Submission>(`/submissions/${id}`).then(r => r.data),

  feedback: (submissionId: string) =>
    client.get<AIFeedback[]>(`/submissions/${submissionId}/feedback`).then(r => r.data),
}
