/**
 * Student Dashboard — shows deadline calendar + enrolled classrooms.
 *
 * React Query (useQuery) pattern:
 * - useQuery({ queryKey, queryFn }) fetches data and caches it.
 * - queryKey is a unique identifier — if two components use the same key, they share the cache.
 * - refetchInterval: 60000 means re-fetch every 60s (deadlines change as time passes).
 * - isLoading / error / data are destructured from the result.
 */

import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Clock, BookOpen, CheckCircle } from "lucide-react";
import { formatDistanceToNow, format } from "date-fns";

import { dashboardApi } from "@/api/dashboard";
import { classroomsApi } from "@/api/classrooms";
import { PageLayout } from "@/components/layout/PageLayout";
import { Badge } from "@/components/common/Badge";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { useAuthStore } from "@/store/authStore";

const urgencyVariant = { red: "red", orange: "orange", green: "green" } as const;

export default function StudentDashboard() {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const { data: deadlines, isLoading: loadingDeadlines } = useQuery({
    queryKey: ["deadlines"],
    queryFn: dashboardApi.deadlines,
    refetchInterval: 60_000,  // refresh every minute — urgency colors change over time
  });

  const { data: classrooms, isLoading: loadingClassrooms } = useQuery({
    queryKey: ["classrooms"],
    queryFn: classroomsApi.list,
  });

  return (
    <PageLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Good {getGreeting()}, {user?.full_name?.split(" ")[0]}!
        </h1>
        <p className="text-sm text-gray-500">Here's what needs your attention.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Deadline Calendar */}
        <div className="lg:col-span-2">
          <h2 className="mb-3 text-base font-semibold text-gray-900 flex items-center gap-2">
            <Clock className="h-4 w-4 text-blue-600" /> Upcoming Deadlines
          </h2>

          {loadingDeadlines ? (
            <LoadingSpinner />
          ) : !deadlines?.length ? (
            <div className="rounded-xl border border-dashed border-gray-300 p-8 text-center text-gray-500">
              No upcoming deadlines. 
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {deadlines.map((item) => (
                <div
                  key={item.assignment_id}
                  className="flex cursor-pointer items-center justify-between rounded-xl bg-white p-4
                    shadow-sm ring-1 ring-gray-200 hover:ring-blue-400 transition"
                  onClick={() => navigate(`/student/assignment/${item.assignment_id}`)}
                >
                  <div>
                    <p className="font-medium text-gray-900">{item.assignment_title}</p>
                    <p className="text-xs text-gray-500">{item.classroom_name}</p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <Badge variant={urgencyVariant[item.urgency]}>
                      {item.has_final_submission
                        ? "Submitted"
                        : formatDistanceToNow(new Date(item.deadline), { addSuffix: true })}
                    </Badge>
                    <p className="text-xs text-gray-400">
                      {format(new Date(item.deadline), "dd MMM, h:mm a")}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Classrooms */}
        <div>
          <h2 className="mb-3 text-base font-semibold text-gray-900 flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-blue-600" /> My Classrooms
          </h2>
          {loadingClassrooms ? (
            <LoadingSpinner />
          ) : (
            <div className="flex flex-col gap-3">
              {classrooms?.map((c) => (
                <div
                  key={c.id}
                  className="cursor-pointer rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200
                    hover:ring-blue-400 transition"
                  onClick={() => navigate(`/student/classroom/${c.id}`)}
                >
                  <p className="font-medium text-gray-900">{c.name}</p>
                  <p className="text-xs text-gray-500">
                    {c.subject_code} · Sec {c.section} · {c.semester}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </PageLayout>
  );
}

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "morning";
  if (h < 17) return "afternoon";
  return "evening";
}
