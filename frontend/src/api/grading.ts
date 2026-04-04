import api from "./client";
import type { Grade } from "@/types";

export const gradingApi = {
  grade: (
    submissionId: string,
    grades: { criterion_id: string; score: number; level: string; feedback: string }[]
  ) =>
    api.post<Grade[]>(`/submissions/${submissionId}/grade`, { grades }).then((r) => r.data),

  release: (assignmentId: string) =>
    api.post(`/assignments/${assignmentId}/release-grades`).then((r) => r.data),
};
