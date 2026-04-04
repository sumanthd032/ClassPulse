/**
 * AssignmentPage — the core student experience.
 *
 * This page implements the Draft → AI Feedback → Improve → Final Submit loop:
 * 1. Student reads assignment description + rubric criteria.
 * 2. Writes answer in textarea.
 * 3. Clicks "Submit Draft" → POST /submit-draft → Celery AI feedback task queued.
 * 4. Polls /my-submissions every 5s until AI feedback appears.
 * 5. Reads per-criterion feedback, improves answer.
 * 6. Repeats until satisfied, then clicks "Submit Final".
 */

import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import toast from "react-hot-toast";
import { Send, Lock, ChevronDown, ChevronUp } from "lucide-react";

import { assignmentsApi } from "@/api/assignments";
import { submissionsApi } from "@/api/submissions";
import { PageLayout } from "@/components/layout/PageLayout";
import { Button } from "@/components/common/Button";
import { Badge } from "@/components/common/Badge";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import type { Submission, AIFeedback, RubricCriterion } from "@/types";

export default function AssignmentPage() {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const queryClient = useQueryClient();
  const [content, setContent] = useState("");
  const [showRubric, setShowRubric] = useState(false);

  const { data: assignment, isLoading: loadingAssignment } = useQuery({
    queryKey: ["assignment", assignmentId],
    queryFn: () => assignmentsApi.get(assignmentId!),
    enabled: !!assignmentId,
  });

  // Poll for submissions every 5 seconds to detect when AI feedback arrives
  const { data: submissions, isLoading: loadingSubmissions } = useQuery({
    queryKey: ["my-submissions", assignmentId],
    queryFn: () => submissionsApi.mySubmissions(assignmentId!),
    enabled: !!assignmentId,
    refetchInterval: 5000,
  });

  const hasFinal = submissions?.some((s) => s.is_final) ?? false;
  const latestDraft = submissions?.filter((s) => !s.is_final).slice(-1)[0];
  const draftCount = submissions?.filter((s) => !s.is_final).length ?? 0;
  const maxDrafts = assignment?.max_drafts ?? 3;

  const submitDraftMutation = useMutation({
    mutationFn: () => submissionsApi.submitDraft(assignmentId!, content),
    onSuccess: () => {
      toast.success("Draft submitted! AI feedback is generating...");
      queryClient.invalidateQueries({ queryKey: ["my-submissions", assignmentId] });
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? "Submission failed.";
      toast.error(msg);
    },
  });

  const submitFinalMutation = useMutation({
    mutationFn: () => submissionsApi.submitFinal(assignmentId!, content),
    onSuccess: () => {
      toast.success("Final submission locked in!");
      queryClient.invalidateQueries({ queryKey: ["my-submissions", assignmentId] });
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? "Final submission failed.";
      toast.error(msg);
    },
  });

  if (loadingAssignment) return <PageLayout><LoadingSpinner size="lg" /></PageLayout>;
  if (!assignment) return <PageLayout><p>Assignment not found.</p></PageLayout>;

  return (
    <PageLayout>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{assignment.title}</h1>
            <p className="mt-1 text-sm text-gray-500">
              Due: {format(new Date(assignment.deadline), "dd MMM yyyy, h:mm a")} ·{" "}
              {assignment.total_marks} marks
            </p>
          </div>
          <div className="flex gap-2">
            {hasFinal ? (
              <Badge variant="green">Final Submitted</Badge>
            ) : (
              <Badge variant="blue">
                {draftCount}/{maxDrafts} drafts used
              </Badge>
            )}
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        {/* Left: submission area */}
        <div className="lg:col-span-3 flex flex-col gap-4">
          {/* Assignment description */}
          <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-200">
            <h2 className="mb-2 font-semibold text-gray-900">Description</h2>
            <p className="whitespace-pre-wrap text-sm text-gray-700">{assignment.description}</p>
          </div>

          {/* Rubric toggle */}
          <button
            className="flex items-center gap-2 text-sm font-medium text-blue-600"
            onClick={() => setShowRubric((v) => !v)}
          >
            {showRubric ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            {showRubric ? "Hide" : "Show"} Rubric ({assignment.rubric_criteria?.length ?? 0} criteria)
          </button>

          {showRubric && (
            <div className="flex flex-col gap-3">
              {assignment.rubric_criteria?.map((c: RubricCriterion) => (
                <RubricCard key={c.id} criterion={c} />
              ))}
            </div>
          )}

          {/* Text editor */}
          {!hasFinal ? (
            <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-200">
              <h2 className="mb-3 font-semibold text-gray-900">Your Answer</h2>
              <textarea
                className="w-full rounded-lg border border-gray-300 p-3 text-sm focus:border-blue-500
                  focus:outline-none focus:ring-1 focus:ring-blue-500 min-h-[200px] resize-y"
                placeholder="Type your answer here..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
              />
              <div className="mt-3 flex gap-2">
                <Button
                  variant="secondary"
                  onClick={() => submitDraftMutation.mutate()}
                  loading={submitDraftMutation.isPending}
                  disabled={!content.trim() || draftCount >= maxDrafts}
                >
                  <Send className="h-4 w-4" /> Submit Draft
                </Button>
                <Button
                  onClick={() => submitFinalMutation.mutate()}
                  loading={submitFinalMutation.isPending}
                  disabled={!content.trim()}
                >
                  <Lock className="h-4 w-4" /> Submit Final
                </Button>
              </div>
              {draftCount >= maxDrafts && (
                <p className="mt-2 text-xs text-orange-600">
                  Draft limit reached. Please submit your final answer.
                </p>
              )}
            </div>
          ) : (
            <div className="rounded-xl bg-green-50 p-5 ring-1 ring-green-200">
              <p className="font-medium text-green-800">
                Final submission locked — waiting for grading.
              </p>
            </div>
          )}
        </div>

        {/* Right: draft history + AI feedback */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <h2 className="font-semibold text-gray-900">Draft History</h2>
          {loadingSubmissions ? (
            <LoadingSpinner />
          ) : !submissions?.length ? (
            <p className="text-sm text-gray-500">No drafts yet. Submit your first draft to get AI feedback.</p>
          ) : (
            submissions.map((sub) => <DraftCard key={sub.id} submission={sub} criteria={assignment.rubric_criteria ?? []} />)
          )}
        </div>
      </div>
    </PageLayout>
  );
}

function RubricCard({ criterion }: { criterion: RubricCriterion }) {
  return (
    <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200">
      <div className="flex items-center justify-between">
        <p className="font-medium text-gray-900">{criterion.name}</p>
        <Badge variant="gray">{criterion.max_marks} marks</Badge>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-1 text-xs text-gray-600">
        {Object.entries(criterion.levels ?? {}).map(([level, desc]) => (
          <div key={level}>
            <span className="font-semibold capitalize">{level}:</span> {desc as string}
          </div>
        ))}
      </div>
    </div>
  );
}

function DraftCard({ submission, criteria }: { submission: Submission; criteria: RubricCriterion[] }) {
  const hasFeedback = submission.ai_feedback && submission.ai_feedback.length > 0;
  const isGenerating = !submission.is_final && !hasFeedback;

  return (
    <div className={`rounded-xl p-4 shadow-sm ring-1 ${submission.is_final ? "bg-green-50 ring-green-200" : "bg-white ring-gray-200"}`}>
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-semibold text-gray-700">
          {submission.is_final ? "Final Submission" : `Draft ${submission.draft_number}`}
        </p>
        {isGenerating && (
          <span className="text-xs text-blue-600 animate-pulse">Generating feedback...</span>
        )}
      </div>
      <p className="text-xs text-gray-500 line-clamp-2">{submission.content}</p>

      {hasFeedback && (
        <div className="mt-3 flex flex-col gap-2">
          {submission.ai_feedback!.map((fb: AIFeedback) => {
            const criterion = criteria.find((c) => c.id === fb.criterion_id);
            return (
              <div key={fb.id} className="rounded-lg bg-blue-50 p-3">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs font-semibold text-blue-900">{criterion?.name ?? "Criterion"}</p>
                  <Badge variant="blue">{fb.estimated_score}/{criterion?.max_marks ?? "?"}</Badge>
                </div>
                <p className="text-xs text-blue-800">{fb.feedback_text}</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
