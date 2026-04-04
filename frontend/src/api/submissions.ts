import api from "./client";
import type { Submission } from "@/types";

export const submissionsApi = {
  submitDraft: (assignmentId: string, content: string, file_url?: string) =>
    api
      .post<Submission>(`/assignments/${assignmentId}/submit-draft`, { content, file_url })
      .then((r) => r.data),

  submitFinal: (assignmentId: string, content: string, file_url?: string) =>
    api
      .post<Submission>(`/assignments/${assignmentId}/submit-final`, { content, file_url })
      .then((r) => r.data),

  mySubmissions: (assignmentId: string) =>
    api.get<Submission[]>(`/assignments/${assignmentId}/my-submissions`).then((r) => r.data),

  allSubmissions: (assignmentId: string) =>
    api.get<Submission[]>(`/assignments/${assignmentId}/submissions`).then((r) => r.data),
};
