import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Send, Sparkles, Clock, AlertCircle, CheckCircle2,
  FileText, ChevronDown, ChevronUp, Award, MessageSquare
} from 'lucide-react'
import toast from 'react-hot-toast'
import { assignmentsApi } from '@/api/assignments'
import { submissionsApi } from '@/api/submissions'
import { gradingApi } from '@/api/grading'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { CommentThread } from '@/components/CommentThread'
import { formatDate, deadlineLabel, isPastDeadline, scoreColor } from '@/lib/utils'
import type { Submission, AIFeedback } from '@/types'

// ---- AI Feedback Card ----
function AIFeedbackCard({ feedback }: { feedback: AIFeedback[] }) {
  if (!feedback.length) return null

  const totalEstimated = feedback.reduce((acc, f) => acc + f.estimated_score, 0)
  const totalMax = feedback.reduce((acc, f) => acc + (f.criterion_max_marks ?? 10), 0)
  const pct = totalMax > 0 ? Math.round((totalEstimated / totalMax) * 100) : 0

  return (
    <Card className="border-violet-500/20 bg-violet-500/5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-xl bg-violet-500/15 flex items-center justify-center">
            <Sparkles className="w-3.5 h-3.5 text-violet-400" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-violet-300">AI Rubric Feedback</h4>
            <p className="text-[10px] text-zinc-500">Automatically generated — review with your teacher's grade</p>
          </div>
        </div>
        <div className="text-right">
          <p className={`text-lg font-bold ${scoreColor(totalEstimated, totalMax)}`}>~{totalEstimated}/{totalMax}</p>
          <p className="text-[10px] text-zinc-500">estimated · {pct}%</p>
        </div>
      </div>

      <div className="space-y-3">
        {feedback.map(f => (
          <FeedbackItem key={f.id} feedback={f} />
        ))}
      </div>
    </Card>
  )
}

function FeedbackItem({ feedback: f }: { feedback: AIFeedback }) {
  const [expanded, setExpanded] = useState(false)
  const max = f.criterion_max_marks ?? 10
  const pct = Math.round((f.estimated_score / max) * 100)
  const levelColors = {
    excellent: 'success', good: 'blue', average: 'warning', poor: 'danger'
  } as const

  // Parse feedback_text: "Strengths: ...\nImprovements: ..."
  const parts = f.feedback_text.split('\nImprovements:')
  const strengths = parts[0].replace('Strengths:', '').trim()
  const improvements = parts[1]?.trim() ?? ''

  return (
    <div className="border border-white/6 rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(v => !v)}
        className="w-full flex items-center gap-3 p-3 hover:bg-white/3 transition-colors text-left"
      >
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-zinc-300">{f.criterion_name ?? 'Criterion'}</p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <div className="w-16 h-1.5 bg-white/8 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${pct >= 80 ? 'bg-emerald-500' : pct >= 60 ? 'bg-amber-500' : 'bg-red-500'}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className={`text-xs font-bold ${scoreColor(f.estimated_score, max)}`}>
            {f.estimated_score}/{max}
          </span>
          <Badge variant={levelColors[f.suggested_level] ?? 'muted'} className="text-[10px]">
            {f.suggested_level}
          </Badge>
          {expanded ? <ChevronUp className="w-3.5 h-3.5 text-zinc-600" /> : <ChevronDown className="w-3.5 h-3.5 text-zinc-600" />}
        </div>
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-2 border-t border-white/5">
          {strengths && (
            <div>
              <p className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider mt-2 mb-1">Strengths</p>
              <p className="text-xs text-zinc-400 leading-relaxed">{strengths}</p>
            </div>
          )}
          {improvements && (
            <div>
              <p className="text-[10px] font-semibold text-amber-400 uppercase tracking-wider mb-1">To improve</p>
              <p className="text-xs text-zinc-400 leading-relaxed">{improvements}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ---- Grade Card (shown to student when grade is released) ----
function GradeCard({ submissionId, totalMarks }: { submissionId: string; totalMarks: number }) {
  const { data: grade } = useQuery({
    queryKey: ['grade', submissionId],
    queryFn: () => gradingApi.getGrade(submissionId),
    retry: false,
  })
  if (!grade) return null

  const pct = Math.round((grade.total_score / totalMarks) * 100)
  const letter = pct >= 90 ? 'A' : pct >= 80 ? 'B' : pct >= 70 ? 'C' : pct >= 60 ? 'D' : 'F'

  return (
    <Card className="border-emerald-500/20 bg-emerald-500/5">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-xl bg-emerald-500/15 flex items-center justify-center">
          <Award className="w-5 h-5 text-emerald-400" />
        </div>
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-emerald-300">Grade Released</h4>
          <p className="text-[10px] text-zinc-500">Graded {formatDate(grade.graded_at)}</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-emerald-400">{grade.total_score}<span className="text-sm font-normal text-zinc-500">/{totalMarks}</span></p>
          <p className="text-xs text-zinc-500">{pct}% · {letter}</p>
        </div>
      </div>
      {grade.teacher_comments && (
        <div className="flex items-start gap-2 bg-bg-elevated rounded-xl px-3 py-2.5 mt-2">
          <MessageSquare className="w-3.5 h-3.5 text-zinc-500 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-zinc-300 leading-relaxed">{grade.teacher_comments}</p>
        </div>
      )}
    </Card>
  )
}

// ---- Submission History ----
function SubmissionHistory({ submissions }: { submissions: Submission[] }) {
  if (!submissions.length) return null
  return (
    <div>
      <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">Submission History</h4>
      <div className="space-y-2">
        {[...submissions].reverse().map(s => (
          <div key={s.id} className="flex items-center gap-3 p-3 rounded-xl bg-bg-elevated border border-white/6">
            <div className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0 ${
              s.is_final ? 'bg-emerald-500/15 text-emerald-400' : 'bg-bg-surface text-zinc-500 border border-white/8'
            }`}>
              {s.is_final ? '✓' : s.draft_number}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-zinc-400">
                {s.is_final ? 'Final submission' : `Draft ${s.draft_number}`}
              </p>
              <p className="text-[10px] text-zinc-600 line-clamp-1 mt-0.5">
                {s.content?.slice(0, 80) ?? 'File submission'}
              </p>
            </div>
            <div className="flex items-center gap-1.5 flex-shrink-0">
              {s.is_late && <Badge variant="danger" dot className="text-[9px]">Late</Badge>}
              <span className="text-[10px] text-zinc-600">{formatDate(s.submitted_at)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ---- Main Page ----
export default function AssignmentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { user } = useAuthStore()
  const qc = useQueryClient()
  const [content, setContent] = useState('')
  const isStudent = user?.role === 'student'

  const { data: assignment, isLoading: loadingA } = useQuery({
    queryKey: ['assignment', id],
    queryFn: () => assignmentsApi.get(id!),
    enabled: !!id,
  })

  const { data: mySubmissions = [] } = useQuery({
    queryKey: ['my-submissions', id],
    queryFn: () => submissionsApi.mine(id!),
    enabled: !!id && isStudent,
    refetchInterval: 5000, // poll for AI feedback
  })

  const latestDraft = [...mySubmissions].filter(s => !s.is_final).pop()
  const finalSub = mySubmissions.find(s => s.is_final)
  const hasFinal = !!finalSub
  const draftCount = mySubmissions.filter(s => !s.is_final).length
  const maxDrafts = assignment?.max_drafts ?? 3
  const canDraft = draftCount < maxDrafts && !hasFinal

  const { data: feedback = [], isLoading: loadingFeedback } = useQuery({
    queryKey: ['feedback', latestDraft?.id],
    queryFn: () => submissionsApi.feedback(latestDraft!.id),
    enabled: !!latestDraft?.id,
    refetchInterval: query => !query.state.data?.length ? 5000 : false, // poll until feedback arrives
  })

  const draftMutation = useMutation({
    mutationFn: () => submissionsApi.submitDraft(id!, { content }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-submissions', id] })
      toast.success('Draft saved! AI feedback generating…')
    },
    onError: (e: any) => toast.error(e.response?.data?.detail ?? 'Failed to save draft'),
  })

  const finalMutation = useMutation({
    mutationFn: () => submissionsApi.submitFinal(id!, { content }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-submissions', id] })
      toast.success('Final submission submitted!')
      setContent('')
    },
    onError: (e: any) => toast.error(e.response?.data?.detail ?? 'Submission failed'),
  })

  if (loadingA) {
    return (
      <div className="max-w-3xl space-y-4">
        <div className="skeleton h-7 w-64" />
        <div className="skeleton h-4 w-96" />
        <div className="skeleton h-48 rounded-2xl" />
      </div>
    )
  }

  if (!assignment) return <p className="text-zinc-500">Assignment not found.</p>

  const isPast = isPastDeadline(assignment.deadline)
  const daysUntil = isPast ? -1 : (new Date(assignment.deadline).getTime() - Date.now()) / 86_400_000
  const dlVariant = isPast ? 'danger' : daysUntil < 1 ? 'warning' : daysUntil < 3 ? 'blue' : 'muted'

  return (
    <div className="max-w-3xl space-y-5">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          <Badge variant={dlVariant}>
            <Clock className="w-3 h-3 mr-1" />
            {deadlineLabel(assignment.deadline)} · {formatDate(assignment.deadline)}
          </Badge>
          <Badge variant="muted"><FileText className="w-3 h-3 mr-1" />{assignment.total_marks} pts</Badge>
          <Badge variant="muted">{assignment.submission_type}</Badge>
          {hasFinal && <Badge variant="success"><CheckCircle2 className="w-3 h-3 mr-1" />Submitted</Badge>}
          {!assignment.is_published && <Badge variant="warning">Draft</Badge>}
        </div>
        <h2 className="text-xl font-bold text-zinc-100">{assignment.title}</h2>
        {assignment.description && (
          <p className="text-sm text-zinc-400 mt-2 leading-relaxed">{assignment.description}</p>
        )}
      </div>

      {/* Released grade (student) */}
      {isStudent && finalSub && (
        <GradeCard submissionId={finalSub.id} totalMarks={assignment.total_marks} />
      )}

      {/* Rubric */}
      {assignment.criteria.length > 0 && (
        <Card>
          <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">Grading Rubric</h4>
          <div className="space-y-1">
            {assignment.criteria.map((c, i) => (
              <div key={c.id} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-zinc-700 font-mono w-4">{i + 1}.</span>
                  <span className="text-sm text-zinc-300">{c.name}</span>
                </div>
                <span className="text-xs font-semibold text-zinc-500">{c.max_marks} pts</span>
              </div>
            ))}
            <div className="flex items-center justify-between pt-2">
              <span className="text-xs font-semibold text-zinc-400">Total</span>
              <span className="text-xs font-bold text-zinc-300">{assignment.total_marks} pts</span>
            </div>
          </div>
        </Card>
      )}

      {/* Student submission area */}
      {isStudent && !hasFinal && (
        <Card>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-zinc-200">Your Answer</h4>
            <span className="text-xs text-zinc-600 bg-bg-elevated px-2 py-1 rounded-lg">
              Draft {draftCount}/{maxDrafts}
            </span>
          </div>

          {!canDraft && draftCount >= maxDrafts && (
            <div className="flex items-center gap-2 text-amber-400 text-xs bg-amber-500/10 border border-amber-500/20 rounded-xl px-3 py-2 mb-3">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
              All {maxDrafts} drafts used. Submit your final answer when ready.
            </div>
          )}

          {assignment.late_policy === 'block' && isPast && (
            <div className="flex items-center gap-2 text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2 mb-3">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
              The deadline has passed. Late submissions are not accepted for this assignment.
            </div>
          )}

          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            placeholder="Write your answer here…"
            rows={10}
            disabled={assignment.late_policy === 'block' && isPast}
            className="w-full bg-bg-elevated border border-white/8 rounded-xl px-4 py-3 text-sm text-zinc-200 placeholder-zinc-600 resize-none focus:outline-none focus:border-accent/40 focus:ring-1 focus:ring-accent/20 transition-all disabled:opacity-50"
          />
          <div className="flex justify-between items-center mt-3">
            <p className="text-xs text-zinc-600">{content.length} characters</p>
            <div className="flex gap-2">
              {canDraft && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => draftMutation.mutate()}
                  loading={draftMutation.isPending}
                  disabled={!content.trim() || (assignment.late_policy === 'block' && isPast)}
                >
                  <Sparkles className="w-3.5 h-3.5 mr-1.5" />
                  Save draft &amp; get AI feedback
                </Button>
              )}
              <Button
                size="sm"
                onClick={() => finalMutation.mutate()}
                loading={finalMutation.isPending}
                disabled={!content.trim() || (assignment.late_policy === 'block' && isPast)}
              >
                <Send className="w-3.5 h-3.5 mr-1.5" />
                Submit final
              </Button>
            </div>
          </div>
        </Card>
      )}

      {hasFinal && isStudent && !finalSub && (
        <div className="flex items-center gap-2 text-emerald-400 text-sm bg-emerald-500/10 border border-emerald-500/20 rounded-2xl px-4 py-3">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          Final answer submitted. Your teacher will release a grade soon.
        </div>
      )}

      {/* AI Feedback */}
      {isStudent && latestDraft && (
        loadingFeedback ? (
          <div className="flex items-center gap-2 text-sm text-zinc-500 bg-bg-elevated border border-white/6 rounded-2xl px-4 py-3">
            <div className="w-4 h-4 border-2 border-violet-400/40 border-t-violet-400 rounded-full animate-spin" />
            Generating AI feedback…
          </div>
        ) : feedback.length > 0 ? (
          <AIFeedbackCard feedback={feedback} />
        ) : (
          <div className="text-center py-4 text-xs text-zinc-600">
            Save a draft to receive AI feedback on your work.
          </div>
        )
      )}

      {/* Submission history */}
      {isStudent && <SubmissionHistory submissions={mySubmissions} />}

      {/* Teacher: link to grading */}
      {!isStudent && (
        <div className="flex items-center justify-between bg-bg-elevated border border-white/6 rounded-2xl px-4 py-3">
          <p className="text-sm text-zinc-400">Teacher view — see all student submissions</p>
          <Link to="/grading" className="text-xs font-medium text-violet-400 hover:text-violet-300 transition-colors">
            Go to Grading →
          </Link>
        </div>
      )}

      {/* Class Discussion */}
      <Card>
        <h4 className="text-sm font-semibold text-zinc-300 mb-4 flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-accent" /> Class Discussion
        </h4>
        <CommentThread type="assignment" targetId={id!} />
      </Card>
    </div>
  )
}
