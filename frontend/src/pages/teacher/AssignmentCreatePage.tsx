/**
 * Assignment Create Page — teachers build an assignment with a rubric.
 *
 * Key UX decisions:
 * - Rubric criteria are added dynamically (add/remove rows).
 * - Each criterion has: name, max_marks, and 4 level descriptors (excellent/good/average/poor).
 * - The total_marks field auto-validates against sum of criteria marks.
 */

import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { PlusCircle, Trash2 } from "lucide-react";

import { assignmentsApi } from "@/api/assignments";
import { PageLayout } from "@/components/layout/PageLayout";
import { Button } from "@/components/common/Button";
import { Input } from "@/components/common/Input";

interface CriterionDraft {
  name: string;
  max_marks: number;
  levels: { excellent: string; good: string; average: string; poor: string };
}

const defaultCriterion = (): CriterionDraft => ({
  name: "",
  max_marks: 10,
  levels: { excellent: "", good: "", average: "", poor: "" },
});

export default function AssignmentCreatePage() {
  const { classroomId } = useParams<{ classroomId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [deadline, setDeadline] = useState("");
  const [maxDrafts, setMaxDrafts] = useState(3);
  const [criteria, setCriteria] = useState<CriterionDraft[]>([defaultCriterion()]);

  const totalMarks = criteria.reduce((sum, c) => sum + Number(c.max_marks), 0);

  const createMutation = useMutation({
    mutationFn: () =>
      assignmentsApi.create(classroomId!, {
        title,
        description,
        deadline: new Date(deadline).toISOString(),
        total_marks: totalMarks,
        max_drafts: maxDrafts,
        rubric_criteria: criteria.map((c, i) => ({ ...c, order_index: i })),
      }),
    onSuccess: (assignment) => {
      toast.success("Assignment created! Publish when ready.");
      queryClient.invalidateQueries({ queryKey: ["assignments", classroomId] });
      navigate(`/teacher/classroom/${classroomId}`);
    },
    onError: () => toast.error("Failed to create assignment."),
  });

  const updateCriterion = (index: number, field: string, value: string | number) => {
    setCriteria((prev) => {
      const next = [...prev];
      if (field.startsWith("levels.")) {
        const level = field.split(".")[1] as keyof CriterionDraft["levels"];
        next[index] = { ...next[index], levels: { ...next[index].levels, [level]: value } };
      } else {
        next[index] = { ...next[index], [field]: value };
      }
      return next;
    });
  };

  return (
    <PageLayout title="Create Assignment">
      <div className="max-w-3xl">
        <div className="flex flex-col gap-4 rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
          <Input label="Assignment Title" placeholder="ER Diagram — Hospital Management System"
            value={title} onChange={(e) => setTitle(e.target.value)} />

          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700">Description</label>
            <textarea
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500
                focus:outline-none focus:ring-1 focus:ring-blue-500 min-h-[100px]"
              placeholder="Describe the assignment task..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input label="Deadline" type="datetime-local"
              value={deadline} onChange={(e) => setDeadline(e.target.value)} />
            <Input label="Max Drafts" type="number" min={1} max={10}
              value={maxDrafts} onChange={(e) => setMaxDrafts(Number(e.target.value))} />
          </div>
        </div>

        {/* Rubric Builder */}
        <div className="mt-6 rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-gray-900">Rubric Criteria</h2>
              <p className="text-xs text-gray-500">
                Total: <strong>{totalMarks} marks</strong> — AI feedback is powered by these criteria
              </p>
            </div>
            <Button variant="secondary" size="sm" onClick={() => setCriteria((p) => [...p, defaultCriterion()])}>
              <PlusCircle className="h-4 w-4" /> Add Criterion
            </Button>
          </div>

          <div className="flex flex-col gap-4">
            {criteria.map((c, i) => (
              <div key={i} className="rounded-lg bg-gray-50 p-4 ring-1 ring-gray-200">
                <div className="mb-3 flex items-center gap-2">
                  <Input className="flex-1" placeholder="Criterion name (e.g. Normalization)"
                    value={c.name} onChange={(e) => updateCriterion(i, "name", e.target.value)} />
                  <Input className="w-24" type="number" placeholder="Marks"
                    value={c.max_marks} onChange={(e) => updateCriterion(i, "max_marks", Number(e.target.value))} />
                  <button
                    className="text-red-500 hover:text-red-700 p-1"
                    onClick={() => setCriteria((p) => p.filter((_, j) => j !== i))}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {(["excellent", "good", "average", "poor"] as const).map((level) => (
                    <div key={level}>
                      <label className="text-xs font-medium capitalize text-gray-600">{level}</label>
                      <input
                        className="mt-0.5 w-full rounded border border-gray-300 px-2 py-1 text-xs"
                        placeholder={`Describe ${level} performance...`}
                        value={c.levels[level]}
                        onChange={(e) => updateCriterion(i, `levels.${level}`, e.target.value)}
                      />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-4 flex gap-3">
          <Button variant="ghost" onClick={() => navigate(-1)}>Cancel</Button>
          <Button
            onClick={() => createMutation.mutate()}
            loading={createMutation.isPending}
            disabled={!title || !deadline || criteria.length === 0}
          >
            Create Assignment
          </Button>
        </div>
      </div>
    </PageLayout>
  );
}
