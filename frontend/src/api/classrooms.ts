import api from "./client";
import type { Classroom, Enrollment } from "@/types";

export const classroomsApi = {
  list: () => api.get<Classroom[]>("/classrooms").then((r) => r.data),

  get: (id: string) => api.get<Classroom>(`/classrooms/${id}`).then((r) => r.data),

  create: (data: {
    name: string;
    subject_code: string;
    section: string;
    semester: string;
    settings?: object;
  }) => api.post<Classroom>("/classrooms", data).then((r) => r.data),

  join: (join_code: string) =>
    api.post<Enrollment>("/classrooms/join", { join_code }).then((r) => r.data),

  updateSettings: (id: string, settings: object) =>
    api.put<Classroom>(`/classrooms/${id}/settings`, { settings }).then((r) => r.data),
};
