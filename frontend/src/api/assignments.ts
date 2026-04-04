import api from "./client";
import type { Assignment } from "@/types";

export const assignmentsApi = {
  list: (classroomId: string) =>
    api.get<Assignment[]>(`/classrooms/${classroomId}/assignments`).then((r) => r.data),

  get: (id: string) => api.get<Assignment>(`/assignments/${id}`).then((r) => r.data),

  create: (classroomId: string, data: Partial<Assignment> & { rubric_criteria?: unknown[] }) =>
    api.post<Assignment>(`/classrooms/${classroomId}/assignments`, data).then((r) => r.data),

  publish: (id: string) =>
    api.post<Assignment>(`/assignments/${id}/publish`).then((r) => r.data),
};
