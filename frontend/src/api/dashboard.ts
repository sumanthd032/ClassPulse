import api from "./client";

export interface DeadlineItem {
  assignment_id: string;
  assignment_title: string;
  classroom_name: string;
  deadline: string;
  has_final_submission: boolean;
  urgency: "red" | "orange" | "green";
}

export interface GradingQueueItem {
  assignment_id: string;
  assignment_title: string;
  classroom_name: string;
  deadline: string;
  total_submissions: number;
  graded_count: number;
}

export const dashboardApi = {
  deadlines: () => api.get<DeadlineItem[]>("/dashboard/deadlines").then((r) => r.data),
  gradingQueue: () =>
    api.get<GradingQueueItem[]>("/dashboard/grading-queue").then((r) => r.data),
};
