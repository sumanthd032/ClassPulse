/**
 * GradingPage — rubric click-scoring interface for teachers.
 *
 * Key features:
 * - Lists all final submissions for an assignment.
 * - For each submission: shows student answer + rubric criteria as clickable cards.
 * - Clicking Excellent/Good/Average/Poor auto-calculates the score.
 * - AI-suggested grade is pre-filled (from AIFeedback estimated_score).
 * - "Release Grades" button makes all grades visible to students.
 */

import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { CheckCircle, ChevronDown, ChevronUp } from "lucide-react";

import { assignmentsApi } from "@/api/assignments";
import { submissionsApi } from "@/api/submissions";
import { gradingApi } from "@/api/grading";
import { PageLayout } from "@/components/layout/PageLayout";
import { Button } from "@/components/common/Button";
import { Badge } from "@/components/common/Badge";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import type { Submission, RubricCriterion } from "@/types";

const LEVEL_MULTIPLIERS = { excellent: 1.0, good: 0.75, average: 0.5, poor: 0.25 };
type Level = keyof typeof LEVEL_MULTIPLIERS;

export default function GradingPage() {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const queryClient = useQueryClient();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [grades, setGrades] = useState<Record<string, Record<string, { level: Level; score: number; feedback: string }>>>({});

  const { data: assignment, isLoading: loadingAssignment } = useQuery({
    queryKey: ["assignment", assignmentId],
    queryFn: () => assignmentsApi.get(assignmentId!),
  });

  const { data: submissions, isLoading: loadingSubmissions } = useQuery({
    queryKey: ["all-submissions", assignmentId],
    queryFn: () => submissionsApi.allSubmissions(assignmentId!),
    enabled: !!assignmentId,
  });

  const gradeMutation = useMutation({
    mutationFn: ({ submissionId, criteriaGrades }: { submissionId: string; criteriaGrades: unknown[] }) =>
      gradingApi.grade(submissionId, criteriaGrades as { criterion_id: string; score: number; level: string; feedback: string }[]),
    onSuccess: () => {
      toast.success("Grades saved!");
      queryClient.invalidateQueries({ queryKey: ["grading-queue"] });
    },
    onError: () => toast.error("Failed to save grades."),
  });

  const releaseMutation = useMutation({
    mutationFn: () => gradingApi.release(assignmentId!),
    onSuccess: (data: { released?: number }) => toast.success(`${data?.released ?? 0} grades released to students!`),
    onError: () => toast.error("Failed to release grades."),
  });

  const setLevel = (submissionId: string, criterionId: string, level: Level, maxMarks: number) => {
    const score = Math.round(maxMarks * LEVEL_MULTIPLIERS[level]);
    setGrades((prev) => ({
      ...prev,
      [submissionId]: {
        ...(prev[submissionId] ?? {}),
        [criterionId]: { level, score, feedback: prev[submissionId]?.[criterionId]?.feedback ?? "" },
      },
    }));
  };

  const saveGrades = (submissionId: string) => {
    const criteriaGrades = Object.entries(grades[submissionId] ?? {}).map(([criterion_id, g]) => ({
      criterion_id,
      score: g.score,
      level: g.level,
      feedback: g.feedback,
    }));
    gradeMutation.mutate({ submissionId, criteriaGrades });
  };

  if (loadingAssignment || loadingSubmissions) return <PageLayout><LoadingSpinner size="lg" /></PageLayout>;

  const criteria = assignment?.rubric_criteria ?? [];

  return (
    <PageLayout title={`Grade: ${assignment?.title}`}>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-gray-600">
          {submissions?.length ?? 0} final submission(s)
        </p>
        <Button onClick={() => releaseMutation.mutate()} loading={releaseMutation.isPending}>
          <CheckCircle className="h-4 w-4" /> Release All Grades
        </Button>
      </div>

      {!submissions?.length ? (
        <div className="rounded-xl border border-dashed border-gray-300 p-10 text-center text-gray-500">
          No final submissions yet.
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {submissions.map((sub) => (
            <SubmissionCard
              key={sub.id}
              submission={sub}
              criteria={criteria}
              grades={grades[sub.id] ?? {}}
              expanded={expandedId === sub.id}
              onToggle={() => setExpandedId((id) => (id === sub.id ? null : sub.id))}
              onSetLevel={(cId, level, maxMarks) => setLevel(sub.id, cId, level, maxMarks)}
              onSetFeedback={(cId, feedback) =>
                setGrades((prev) => ({
                  ...prev,
                  [sub.id]: { ...(prev[sub.id] ?? {}), [cId]: { ...(prev[sub.id]?.[cId] ?? { level: "good", score: 0 }), feedback } },
                }))
              }
              onSave={() => saveGrades(sub.id)}
              saving={gradeMutation.isPending}
            />
          ))}
        </div>
      )}
    </PageLayout>
  );
}

function SubmissionCard({
  submission, criteria, grades, expanded, onToggle, onSetLevel, onSetFeedback, onSave, saving
}: {
  submission: Submission;
  criteria: RubricCriterion[];
  grades: Record<string, { level: Level; score: number; feedback: string }>;
  expanded: boolean;
  onToggle: () => void;
  onSetLevel: (criterionId: string, level: Level, maxMarks: number) => void;
  onSetFeedback: (criterionId: string, feedback: string) => void;
  onSave: () => void;
  saving: boolean;
}) {
  const totalScore = Object.values(grades).reduce((sum, g) => sum + g.score, 0);

  return (
    <div className="rounded-xl bg-white shadow-sm ring-1 ring-gray-200">
      <button className="flex w-full items-center justify-between p-4" onClick={onToggle}>
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-blue-700 text-sm font-bold">
            S
          </div>
          <div className="text-left">
            <p className="font-medium text-gray-900">Student ID: {submission.student_id.slice(0, 8)}...</p>
            <p className="text-xs text-gray-500">{submission.is_late ? "Late submission" : "On time"}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {Object.keys(grades).length > 0 && (
            <Badge variant="blue">Score: {totalScore}</Badge>
          )}
          {expanded ? <ChevronUp className="h-4 w-4 text-gray-500" /> : <ChevronDown className="h-4 w-4 text-gray-500" />}
        </div>
      </button>

      {expanded && (
        <div className="border-t border-gray-100 p-4">
          {/* Student answer */}
          <div className="mb-4 rounded-lg bg-gray-50 p-3">
            <p className="mb-1 text-xs font-semibold text-gray-600">Student Answer</p>
            <p className="whitespace-pre-wrap text-sm text-gray-800">{submission.content}</p>
          </div>

          {/* Rubric click-grader */}
          <div className="flex flex-col gap-3">
            {criteria.map((criterion) => {
              const aiSuggestion = submission.ai_feedback?.find((f) => f.criterion_id === criterion.id);
              const currentGrade = grades[criterion.id];
              return (
                <div key={criterion.id} className="rounded-lg bg-gray-50 p-3 ring-1 ring-gray-200">
                  <div className="mb-2 flex items-center justify-between">
                    <p className="font-medium text-gray-900 text-sm">{criterion.name}</p>
                    <span className="text-xs text-gray-500">Max: {criterion.max_marks}</span>
                  </div>

                  {aiSuggestion && (
                    <p className="mb-2 rounded bg-blue-50 px-2 py-1 text-xs text-blue-700">
                      AI suggests: {aiSuggestion.estimated_score}/{criterion.max_marks} — {aiSuggestion.feedback_text.slice(0, 80)}...
                    </p>
                  )}

                  {/* Click-to-grade buttons */}
                  <div className="mb-2 flex gap-2">
                    {(["excellent", "good", "average", "poor"] as Level[]).map((level) => (
                      <button
                        key={level}
                        className={`flex-1 rounded py-1.5 text-xs font-medium capitalize transition
                          ${currentGrade?.level === level
                            ? "bg-blue-600 text-white"
                            : "bg-white text-gray-700 ring-1 ring-gray-300 hover:bg-gray-100"}`}
                        onClick={() => onSetLevel(criterion.id, level, criterion.max_marks)}
                      >
                        {level}
                        <br />
                        <span className="text-xs font-normal">
                          {Math.round(criterion.max_marks * LEVEL_MULTIPLIERS[level])}
                        </span>
                      </button>
                    ))}
                  </div>

                  <input
                    className="w-full rounded border border-gray-300 px-2 py-1 text-xs"
                    placeholder="Add feedback for this criterion..."
                    value={currentGrade?.feedback ?? ""}
                    onChange={(e) => onSetFeedback(criterion.id, e.target.value)}
                  />
                </div>
              );
            })}
          </div>

          <div className="mt-4 flex justify-end">
            <Button size="sm" onClick={onSave} loading={saving}>Save Grades</Button>
          </div>
        </div>
      )}
    </div>
  );
}
