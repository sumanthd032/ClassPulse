import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import toast from "react-hot-toast";
import { PlusCircle, Users, ClipboardList } from "lucide-react";
import { format } from "date-fns";

import { dashboardApi } from "@/api/dashboard";
import { classroomsApi } from "@/api/classrooms";
import { PageLayout } from "@/components/layout/PageLayout";
import { Button } from "@/components/common/Button";
import { Badge } from "@/components/common/Badge";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { Modal } from "@/components/common/Modal";
import { Input } from "@/components/common/Input";
import { useAuthStore } from "@/store/authStore";
import { useQueryClient } from "@tanstack/react-query";

export default function TeacherDashboard() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ name: "", subject_code: "", section: "", semester: "" });

  const { data: queue, isLoading: loadingQueue } = useQuery({
    queryKey: ["grading-queue"],
    queryFn: dashboardApi.gradingQueue,
    refetchInterval: 30_000,
  });

  const { data: classrooms, isLoading: loadingClassrooms } = useQuery({
    queryKey: ["classrooms"],
    queryFn: classroomsApi.list,
  });

  const handleCreateClassroom = async () => {
    if (!form.name || !form.subject_code || !form.section || !form.semester) {
      toast.error("Fill in all fields.");
      return;
    }
    setCreating(true);
    try {
      await classroomsApi.create(form);
      queryClient.invalidateQueries({ queryKey: ["classrooms"] });
      toast.success("Classroom created!");
      setShowCreate(false);
      setForm({ name: "", subject_code: "", section: "", semester: "" });
    } catch {
      toast.error("Failed to create classroom.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <PageLayout>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome, {user?.full_name?.split(" ")[0]}!
          </h1>
          <p className="text-sm text-gray-500">Manage your classrooms and grade submissions.</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <PlusCircle className="h-4 w-4" /> New Classroom
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        {/* Grading Queue */}
        <div className="lg:col-span-3">
          <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-gray-900">
            <ClipboardList className="h-4 w-4 text-blue-600" /> Grading Queue
          </h2>
          {loadingQueue ? (
            <LoadingSpinner />
          ) : !queue?.length ? (
            <div className="rounded-xl border border-dashed border-gray-300 p-8 text-center text-gray-500">
              Nothing to grade right now.
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {queue.map((item) => {
                const pending = item.total_submissions - item.graded_count;
                return (
                  <div
                    key={item.assignment_id}
                    className="flex cursor-pointer items-center justify-between rounded-xl bg-white p-4
                      shadow-sm ring-1 ring-gray-200 hover:ring-blue-400 transition"
                    onClick={() => navigate(`/teacher/grade/${item.assignment_id}`)}
                  >
                    <div>
                      <p className="font-medium text-gray-900">{item.assignment_title}</p>
                      <p className="text-xs text-gray-500">{item.classroom_name}</p>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <Badge variant={pending > 0 ? "orange" : "green"}>
                        {pending > 0 ? `${pending} to grade` : "All graded"}
                      </Badge>
                      <p className="text-xs text-gray-400">
                        {item.graded_count}/{item.total_submissions} graded
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Classrooms sidebar */}
        <div className="lg:col-span-2">
          <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-gray-900">
            <Users className="h-4 w-4 text-blue-600" /> My Classrooms
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
                  onClick={() => navigate(`/teacher/classroom/${c.id}`)}
                >
                  <p className="font-medium text-gray-900">{c.name}</p>
                  <p className="text-xs text-gray-500">{c.subject_code} · Sec {c.section}</p>
                  <p className="mt-1 font-mono text-xs text-blue-600">Code: {c.join_code}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Classroom Modal */}
      <Modal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title="Create New Classroom"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button onClick={handleCreateClassroom} loading={creating}>Create</Button>
          </>
        }
      >
        <div className="flex flex-col gap-3">
          <Input label="Course Name" placeholder="Database Management Systems"
            value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input label="Subject Code" placeholder="18CS53"
            value={form.subject_code} onChange={(e) => setForm({ ...form, subject_code: e.target.value })} />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Section" placeholder="4A"
              value={form.section} onChange={(e) => setForm({ ...form, section: e.target.value })} />
            <Input label="Semester" placeholder="5th Sem"
              value={form.semester} onChange={(e) => setForm({ ...form, semester: e.target.value })} />
          </div>
        </div>
      </Modal>
    </PageLayout>
  );
}
