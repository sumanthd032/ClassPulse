import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { BookOpen, Clock } from "lucide-react";

import { classroomsApi } from "@/api/classrooms";
import { assignmentsApi } from "@/api/assignments";
import { PageLayout } from "@/components/layout/PageLayout";
import { Badge } from "@/components/common/Badge";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";

export default function ClassroomPage() {
  const { classroomId } = useParams<{ classroomId: string }>();
  const navigate = useNavigate();

  const { data: classroom, isLoading: loadingClassroom } = useQuery({
    queryKey: ["classroom", classroomId],
    queryFn: () => classroomsApi.get(classroomId!),
  });

  const { data: assignments, isLoading: loadingAssignments } = useQuery({
    queryKey: ["assignments", classroomId],
    queryFn: () => assignmentsApi.list(classroomId!),
    enabled: !!classroomId,
  });

  if (loadingClassroom) return <PageLayout><LoadingSpinner size="lg" /></PageLayout>;

  return (
    <PageLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{classroom?.name}</h1>
        <p className="text-sm text-gray-500">
          {classroom?.subject_code} · Section {classroom?.section} · {classroom?.semester}
        </p>
        <div className="mt-2 inline-flex items-center gap-2 rounded-lg bg-gray-100 px-3 py-1.5">
          <span className="text-xs text-gray-600">Join Code:</span>
          <span className="font-mono font-bold text-gray-900">{classroom?.join_code}</span>
        </div>
      </div>

      <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-gray-900">
        <BookOpen className="h-4 w-4 text-blue-600" /> Assignments
      </h2>

      {loadingAssignments ? (
        <LoadingSpinner />
      ) : !assignments?.length ? (
        <div className="rounded-xl border border-dashed border-gray-300 p-8 text-center text-gray-500">
          No assignments yet.
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {assignments.map((a) => {
            const isPast = new Date(a.deadline) < new Date();
            return (
              <div
                key={a.id}
                className="cursor-pointer rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-200
                  hover:ring-blue-400 transition"
                onClick={() => navigate(`/student/assignment/${a.id}`)}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="font-semibold text-gray-900">{a.title}</p>
                  <Badge variant={isPast ? "red" : "green"}>
                    {isPast ? "Past due" : "Open"}
                  </Badge>
                </div>
                <p className="mt-1 text-xs text-gray-500 line-clamp-2">{a.description}</p>
                <div className="mt-3 flex items-center gap-1 text-xs text-gray-500">
                  <Clock className="h-3 w-3" />
                  Due {format(new Date(a.deadline), "dd MMM, h:mm a")}
                  <span className="ml-auto">{a.total_marks} marks</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </PageLayout>
  );
}
