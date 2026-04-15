import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import {
  AlertTriangle, CheckCircle2, Eye, EyeOff,
  Sparkles, Users, ClipboardList, BookOpen, User,
  Download, Table2, GraduationCap, XCircle, Clock,
} from 'lucide-react'
import { classroomsApi } from '@/api/classrooms'
import { assignmentsApi } from '@/api/assignments'
import { gradingApi } from '@/api/grading'
import { submissionsApi } from '@/api/submissions'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Avatar } from '@/components/ui/Avatar'
import { EmptyState } from '@/components/ui/EmptyState'
import { formatDate, scoreColor } from '@/lib/utils'
import type { Submission, RubricCriteria, GradebookEntry } from '@/types'

const gradeSchema = z.object({
  total_score: z.coerce.number().min(0, 'Cannot be negative'),
  teacher_comments: z.string().optional(),
  is_released: z.boolean(),
})
type GradeForm = z.infer<typeof gradeSchema>

function GradePanel({ submission, maxMarks, criteria, onDone }: {
  submission: Submission; maxMarks: number; criteria: RubricCriteria[]; onDone: () => void
}) {
  const qc = useQueryClient()
  const [showContent, setShowContent] = useState(true)
  // Per-criterion scores: map from criterion_id -> score
  const [criterionScores, setCriterionScores] = useState<Record<string, number>>(() => {
    const init: Record<string, number> = {}
    criteria.forEach(c => { init[c.id] = 0 })
    return init
  })

  const { data: existingGrade } = useQuery({
    queryKey: ['grade', submission.id],
    queryFn: () => gradingApi.getGrade(submission.id),
    retry: false,
  })

  const { data: aiFeedback = [] } = useQuery({
    queryKey: ['feedback', submission.id],
    queryFn: () => submissionsApi.feedback(submission.id),
  })

  // Pre-populate criterion scores from existing grade (including AI auto-grade)
  useEffect(() => {
    if (existingGrade?.criterion_grades?.length && criteria.length > 0) {
      const init: Record<string, number> = {}
      criteria.forEach(c => { init[c.id] = 0 })
      existingGrade.criterion_grades.forEach((cg: { criterion_id: string; score: number }) => {
        init[cg.criterion_id] = cg.score
      })
      setCriterionScores(init)
      const total = Object.values(init).reduce((a, b) => a + b, 0)
      setValue('total_score', total)
    }
    if (existingGrade) {
      setValue('teacher_comments', existingGrade.teacher_comments ?? '')
      setValue('is_released', existingGrade.is_released ?? false)
    }
  }, [existingGrade, criteria]) // eslint-disable-line react-hooks/exhaustive-deps

  // Detect AI-auto-graded sentinel (grader_id === student_id)
  const isAiGraded = existingGrade && existingGrade.grader_id === submission.student_id

  // Compute total from criterion scores when criteria exist
  const criteriaTotal = criteria.length > 0
    ? Object.values(criterionScores).reduce((a, b) => a + b, 0)
    : null

  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<GradeForm>({
    resolver: zodResolver(gradeSchema),
    defaultValues: {
      total_score: 0,
      teacher_comments: '',
      is_released: false,
    },
  })

  // Keep total_score in sync with criterion scores when rubric is present
  const updateCriterionScore = (criterionId: string, value: number) => {
    const updated = { ...criterionScores, [criterionId]: value }
    setCriterionScores(updated)
    if (criteria.length > 0) {
      const total = Object.values(updated).reduce((a, b) => a + b, 0)
      setValue('total_score', total)
    }
  }

  const score = watch('total_score')
  const pct = maxMarks > 0 ? Math.round((Number(score) / maxMarks) * 100) : 0

  const mutation = useMutation({
    mutationFn: (data: GradeForm) => {
      const criterionScoresPayload = criteria.length > 0
        ? criteria.map(c => ({ criterion_id: c.id, score: criterionScores[c.id] ?? 0 }))
        : undefined
      return gradingApi.grade(submission.id, { ...data, criterion_scores: criterionScoresPayload })
    },
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ['grading-queue'] })
      toast.success(vars.is_released ? 'Grade saved and released to student!' : 'Grade saved as draft.')
      onDone()
    },
    onError: () => toast.error('Failed to save grade'),
  })

  const aiTotal = aiFeedback.reduce((acc, f) => acc + f.estimated_score, 0)
  const aiMax = aiFeedback.reduce((acc, f) => acc + (f.criterion_max_marks ?? 10), 0)

  return (
    <div className="space-y-4">
      {/* Student info */}
      <div className="flex items-center gap-3 p-3 bg-bg-elevated rounded-xl border border-white/6">
        <Avatar name={submission.student_name ?? submission.student_id} size="sm" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-zinc-200">{submission.student_name ?? 'Student'}</p>
          <p className="text-xs text-zinc-500">{submission.student_email ?? ''}</p>
        </div>
        <div className="flex gap-1.5 flex-shrink-0">
          {submission.is_late && <Badge variant="danger" dot>Late</Badge>}
          {submission.similarity_flagged && (
            <Badge variant="warning">
              <AlertTriangle className="w-3 h-3 mr-1" />
              {Math.round((submission.similarity_score ?? 0) * 100)}% similar
            </Badge>
          )}
        </div>
      </div>

      {/* Submitted on */}
      <p className="text-xs text-zinc-600">Submitted {formatDate(submission.submitted_at)}</p>

      {/* Submission content */}
      {submission.content && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Answer</span>
            <button
              type="button"
              onClick={() => setShowContent(v => !v)}
              className="text-zinc-600 hover:text-zinc-400 transition-colors flex items-center gap-1 text-xs"
            >
              {showContent ? <><EyeOff className="w-3.5 h-3.5" /> Hide</> : <><Eye className="w-3.5 h-3.5" /> Show</>}
            </button>
          </div>
          {showContent && (
            <div className="bg-bg-elevated border border-white/6 rounded-xl px-4 py-3 max-h-40 overflow-y-auto">
              <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">{submission.content}</p>
            </div>
          )}
        </div>
      )}

      {/* AI suggestions */}
      {aiFeedback.length > 0 && (
        <div className="border border-violet-500/20 bg-violet-500/5 rounded-xl p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-violet-400" />
              <span className="text-xs font-semibold text-violet-400">AI Suggested Scores</span>
            </div>
            <span className={`text-xs font-bold ${scoreColor(aiTotal, aiMax)}`}>
              ~{aiTotal}/{aiMax} pts
            </span>
          </div>
          <div className="space-y-1">
            {aiFeedback.map(f => (
              <div key={f.id} className="flex items-center justify-between text-xs">
                <span className="text-zinc-400 truncate flex-1">{f.criterion_name ?? 'Criterion'}</span>
                <span className={`font-semibold ml-2 flex-shrink-0 ${scoreColor(f.estimated_score, f.criterion_max_marks ?? 10)}`}>
                  {f.estimated_score}/{f.criterion_max_marks ?? '?'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI auto-grade banner */}
      {isAiGraded && (
        <div className="flex items-start gap-2.5 bg-violet-500/10 border border-violet-500/25 rounded-xl px-3 py-2.5">
          <Sparkles className="w-4 h-4 text-violet-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold text-violet-300">AI-suggested grade loaded</p>
            <p className="text-[11px] text-violet-400/70 mt-0.5">
              Criterion scores have been pre-filled by the AI. Review, adjust, and save to confirm.
            </p>
          </div>
        </div>
      )}

      {/* Existing teacher-confirmed grade notice */}
      {existingGrade && !isAiGraded && (
        <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-3 py-2">
          <CheckCircle2 className="w-3.5 h-3.5" />
          Already graded: {existingGrade.total_score}/{maxMarks} pts
          {existingGrade.is_released ? ' · Released' : ' · Not released yet'}
        </div>
      )}

      {/* Grade form */}
      <form onSubmit={handleSubmit(d => mutation.mutate(d))} className="space-y-3">
        {/* Per-criterion scoring (when rubric exists) */}
        {criteria.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Rubric Scoring</p>
            {criteria.map(c => (
              <div key={c.id} className="flex items-center gap-3 bg-bg-elevated border border-white/6 rounded-xl px-3 py-2">
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-zinc-300 truncate">{c.name}</p>
                  <p className="text-[10px] text-zinc-600">max {c.max_marks} pts</p>
                </div>
                <input
                  type="number"
                  min={0}
                  max={c.max_marks}
                  value={criterionScores[c.id] ?? 0}
                  onChange={e => updateCriterionScore(c.id, Math.min(c.max_marks, Math.max(0, Number(e.target.value))))}
                  className="w-16 bg-bg-surface border border-white/10 rounded-lg px-2 py-1 text-sm text-zinc-200 text-center focus:outline-none focus:border-accent/40"
                />
                <span className="text-xs text-zinc-600 w-8 text-right">/{c.max_marks}</span>
              </div>
            ))}
            <div className="flex items-center justify-between px-1">
              <span className="text-xs text-zinc-500">Rubric total</span>
              <span className={`text-sm font-bold ${scoreColor(criteriaTotal ?? 0, maxMarks)}`}>
                {criteriaTotal ?? 0}/{maxMarks} pts ({pct}%)
              </span>
            </div>
          </div>
        )}

        {/* Manual total score (shown when no rubric, or as override) */}
        {criteria.length === 0 && (
          <Input
            label={`Score (out of ${maxMarks})`}
            type="number"
            min={0}
            max={maxMarks}
            error={errors.total_score?.message}
            hint={`${pct}% · ${score || 0}/${maxMarks} points`}
            {...register('total_score')}
          />
        )}

        {/* Hidden field to ensure total_score is submitted when using rubric */}
        {criteria.length > 0 && (
          <input type="hidden" {...register('total_score')} />
        )}

        <div>
          <label className="block text-xs font-medium text-zinc-400 mb-1.5">Teacher comments (optional)</label>
          <textarea
            placeholder="Provide feedback to the student…"
            rows={3}
            className="w-full bg-bg-elevated border border-white/8 rounded-xl px-4 py-3 text-sm text-zinc-200 placeholder-zinc-600 resize-none focus:outline-none focus:border-accent/40 focus:ring-1 focus:ring-accent/20 transition-all"
            {...register('teacher_comments')}
          />
        </div>
        <label className="flex items-center gap-2.5 cursor-pointer group">
          <input
            type="checkbox"
            className="w-4 h-4 rounded border-white/20 bg-bg-elevated text-accent focus:ring-accent/30 cursor-pointer"
            {...register('is_released')}
          />
          <span className="text-sm text-zinc-400 group-hover:text-zinc-300 transition-colors">
            Release grade to student immediately
          </span>
        </label>
        <Button type="submit" className="w-full" loading={mutation.isPending}>
          <CheckCircle2 className="w-4 h-4 mr-1.5" />
          {existingGrade ? 'Update Grade' : 'Save Grade'}
        </Button>
      </form>
    </div>
  )
}

// -----------------------------------------------------------------------
// Gradebook tab
// -----------------------------------------------------------------------
function GradebookView({ assignmentId, assignmentTitle, maxMarks }: {
  assignmentId: string; assignmentTitle: string; maxMarks: number
}) {
  const [downloading, setDownloading] = useState(false)
  const { data: entries = [], isLoading } = useQuery({
    queryKey: ['gradebook', assignmentId],
    queryFn: () => gradingApi.gradebook(assignmentId),
  })

  const graded = entries.filter(e => e.score !== null && !e.is_ai_graded)
  const aiGraded = entries.filter(e => e.is_ai_graded)
  const submitted = entries.filter(e => e.has_submitted)
  const released = entries.filter(e => e.is_released)
  const avgPct = graded.length
    ? Math.round(graded.reduce((a, e) => a + (e.percentage ?? 0), 0) / graded.length)
    : null

  const handlePdf = async () => {
    setDownloading(true)
    try {
      await gradingApi.downloadPdf(assignmentId, assignmentTitle)
    } finally {
      setDownloading(false)
    }
  }

  const letterColor = (g: string | null) => {
    if (!g) return 'text-zinc-500'
    if (g === 'O' || g === 'A') return 'text-emerald-400'
    if (g === 'B') return 'text-blue-400'
    if (g === 'C') return 'text-amber-400'
    return 'text-red-400'
  }

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[...Array(5)].map((_, i) => <div key={i} className="skeleton h-12 rounded-xl" />)}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header + Download */}
      <div className="flex items-center justify-between">
        <div className="flex gap-3">
          {[
            { label: 'Students', value: entries.length, color: 'text-zinc-300' },
            { label: 'Submitted', value: submitted.length, color: 'text-blue-400' },
            { label: 'Graded', value: graded.length, color: 'text-violet-400' },
            { label: 'AI Suggested', value: aiGraded.length, color: 'text-violet-400' },
            { label: 'Released', value: released.length, color: 'text-emerald-400' },
            { label: 'Class Avg', value: avgPct !== null ? `${avgPct}%` : '—', color: scoreColor(avgPct ?? 0, 100) },
          ].map(s => (
            <div key={s.label} className="text-center px-3 py-1.5 bg-bg-elevated border border-white/6 rounded-xl">
              <p className={`text-lg font-bold tabular-nums ${s.color}`}>{s.value}</p>
              <p className="text-[10px] text-zinc-600">{s.label}</p>
            </div>
          ))}
        </div>
        <Button variant="secondary" size="sm" onClick={handlePdf} loading={downloading}>
          <Download className="w-3.5 h-3.5 mr-1.5" />
          Download PDF
        </Button>
      </div>

      {/* Table */}
      {entries.length === 0 ? (
        <EmptyState icon={<GraduationCap className="w-6 h-6" />} title="No students enrolled" description="Students will appear here once they join the classroom." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-white/8">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-bg-elevated border-b border-white/8">
                {['#', 'Student', 'Email', 'Submitted', 'Late', 'Score', '%', 'Grade', 'Status'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-[11px] font-semibold text-zinc-500 uppercase tracking-wider whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {entries.map((e: GradebookEntry, i) => (
                <tr key={e.student_id} className="border-b border-white/4 hover:bg-white/2 transition-colors">
                  <td className="px-4 py-3 text-zinc-600 text-xs">{i + 1}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Avatar name={e.student_name} size="xs" />
                      <span className="text-zinc-200 font-medium text-xs">{e.student_name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-zinc-500 text-xs">{e.student_email}</td>
                  <td className="px-4 py-3">
                    {e.has_submitted
                      ? <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      : <XCircle className="w-4 h-4 text-zinc-700" />}
                  </td>
                  <td className="px-4 py-3">
                    {e.is_late
                      ? <Badge variant="danger" className="text-[10px]">Late</Badge>
                      : <span className="text-zinc-700 text-xs">—</span>}
                  </td>
                  <td className="px-4 py-3">
                    {e.score !== null
                      ? <span className={`font-semibold ${scoreColor(e.score, maxMarks)}`}>{e.score}/{maxMarks}</span>
                      : <span className="text-zinc-700 text-xs">—</span>}
                  </td>
                  <td className="px-4 py-3">
                    {e.percentage !== null
                      ? <span className={`text-xs font-medium ${scoreColor(e.percentage, 100)}`}>{e.percentage}%</span>
                      : <span className="text-zinc-700 text-xs">—</span>}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`font-bold text-sm ${letterColor(e.letter_grade)}`}>
                      {e.letter_grade ?? '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {e.is_released
                      ? <Badge variant="success">Released</Badge>
                      : e.is_ai_graded
                      ? <Badge variant="purple"><Sparkles className="w-2.5 h-2.5 mr-1" />AI Suggested</Badge>
                      : e.score !== null
                      ? <Badge variant="warning"><Clock className="w-2.5 h-2.5 mr-1" />Pending</Badge>
                      : <span className="text-zinc-700 text-xs">Not graded</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="text-xs text-zinc-700">Grade scale: O ≥ 90% · A ≥ 75% · B ≥ 60% · C ≥ 50% · D ≥ 40% · F &lt; 40%</p>
    </div>
  )
}

// -----------------------------------------------------------------------
// Main page
// -----------------------------------------------------------------------
export default function GradingPage() {
  const [tab, setTab] = useState<'queue' | 'gradebook'>('queue')
  const [selectedClassroom, setSelectedClassroom] = useState<string | null>(null)
  const [selectedAssignment, setSelectedAssignment] = useState<string | null>(null)
  const [selectedSubmission, setSelectedSubmission] = useState<Submission | null>(null)

  const { data: classrooms = [] } = useQuery({
    queryKey: ['classrooms'],
    queryFn: classroomsApi.list,
  })

  const { data: assignments = [] } = useQuery({
    queryKey: ['assignments', selectedClassroom],
    queryFn: () => assignmentsApi.list(selectedClassroom!),
    enabled: !!selectedClassroom,
  })

  const { data: queue = [], isLoading: loadingQueue } = useQuery({
    queryKey: ['grading-queue', selectedAssignment],
    queryFn: () => gradingApi.queue(selectedAssignment!),
    enabled: !!selectedAssignment && tab === 'queue',
  })

  const teacherClassrooms = classrooms.filter(e => e.role === 'co_teacher')
  const selectedAssignmentData = assignments.find(a => a.id === selectedAssignment)

  return (
    <div className="max-w-6xl">
      <div className="mb-5 flex items-start justify-between">
        <div>
          <h2 className="text-xl font-bold text-zinc-100">Grading</h2>
          <p className="text-sm text-zinc-500 mt-0.5">Review submissions and track class performance</p>
        </div>
        {/* Tab switcher */}
        <div className="flex items-center bg-bg-elevated border border-white/8 rounded-xl p-1 gap-1">
          <button
            onClick={() => setTab('queue')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              tab === 'queue' ? 'bg-accent text-white' : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            <ClipboardList className="w-3.5 h-3.5" />
            Grading Queue
          </button>
          <button
            onClick={() => setTab('gradebook')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              tab === 'gradebook' ? 'bg-accent text-white' : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            <Table2 className="w-3.5 h-3.5" />
            Gradebook
          </button>
        </div>
      </div>

      {/* Classroom + Assignment selectors (shared) */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex items-center gap-2">
          <BookOpen className="w-3.5 h-3.5 text-zinc-500" />
          <select
            value={selectedClassroom ?? ''}
            onChange={e => {
              setSelectedClassroom(e.target.value || null)
              setSelectedAssignment(null)
              setSelectedSubmission(null)
            }}
            className="bg-bg-elevated border border-white/8 rounded-xl px-3 py-2 text-sm text-zinc-300 focus:outline-none focus:border-accent/30"
          >
            <option value="">Select classroom…</option>
            {teacherClassrooms.map(e => (
              <option key={e.classroom_id} value={e.classroom_id}>{e.classroom.name}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <ClipboardList className="w-3.5 h-3.5 text-zinc-500" />
          <select
            value={selectedAssignment ?? ''}
            onChange={e => { setSelectedAssignment(e.target.value || null); setSelectedSubmission(null) }}
            className="bg-bg-elevated border border-white/8 rounded-xl px-3 py-2 text-sm text-zinc-300 focus:outline-none focus:border-accent/30"
            disabled={!selectedClassroom}
          >
            <option value="">{selectedClassroom ? 'Select assignment…' : 'Select a class first'}</option>
            {assignments.map(a => (
              <option key={a.id} value={a.id}>{a.title}</option>
            ))}
          </select>
        </div>
        {selectedAssignment && tab === 'gradebook' && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => gradingApi.releaseAllGrades(selectedAssignment).then(() => toast.success('All grades released!'))}
          >
            <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
            Release All
          </Button>
        )}
      </div>

      {tab === 'gradebook' ? (
        selectedAssignment ? (
          <GradebookView
            assignmentId={selectedAssignment}
            assignmentTitle={selectedAssignmentData?.title ?? 'assignment'}
            maxMarks={selectedAssignmentData?.total_marks ?? 100}
          />
        ) : (
          <EmptyState
            icon={<Table2 className="w-6 h-6" />}
            title="Select an assignment"
            description="Choose a classroom and assignment above to view the gradebook."
          />
        )
      ) : (
        /* Grading Queue — 3-column layout */
        <div className="grid grid-cols-[220px_1fr] gap-4 h-[calc(100vh-17rem)]">
          {/* Submission list */}
          <Card padding="none" className="overflow-hidden flex flex-col">
            <div className="px-4 py-3 border-b border-white/6 flex items-center gap-2">
              <Users className="w-3.5 h-3.5 text-zinc-500" />
              <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Queue</h3>
              {queue.length > 0 && <Badge variant="warning" className="ml-auto">{queue.length}</Badge>}
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              {!selectedAssignment ? (
                <div className="text-center py-8">
                  <ClipboardList className="w-8 h-8 text-zinc-700 mx-auto mb-2" />
                  <p className="text-xs text-zinc-600">Select an assignment</p>
                </div>
              ) : loadingQueue ? (
                <div className="space-y-2 p-2">
                  {[...Array(3)].map((_, i) => <div key={i} className="skeleton h-14 rounded-xl" />)}
                </div>
              ) : queue.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle2 className="w-8 h-8 text-emerald-500/50 mx-auto mb-2" />
                  <p className="text-xs text-zinc-600 font-medium">All graded!</p>
                </div>
              ) : (
                queue.map((s: Submission) => (
                  <button
                    key={s.id}
                    onClick={() => setSelectedSubmission(s)}
                    className={`w-full text-left px-3 py-2.5 rounded-xl flex items-center gap-2.5 transition-all mb-0.5 border ${
                      selectedSubmission?.id === s.id
                        ? 'bg-accent/10 border-accent/20 text-accent'
                        : 'text-zinc-400 hover:bg-white/4 hover:text-zinc-200 border-transparent'
                    }`}
                  >
                    <Avatar name={s.student_name ?? s.student_id} size="xs" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold truncate">{s.student_name ?? 'Student'}</p>
                      <p className="text-[10px] text-zinc-600 mt-0.5">{formatDate(s.submitted_at)}</p>
                    </div>
                    <div className="flex flex-col items-end gap-1 flex-shrink-0">
                      {s.is_late && <Badge variant="danger" className="text-[9px]">Late</Badge>}
                      {s.similarity_flagged && <AlertTriangle className="w-3 h-3 text-amber-400" />}
                    </div>
                  </button>
                ))
              )}
            </div>
          </Card>

          {/* Grade panel */}
          <Card padding="none" className="overflow-hidden flex flex-col">
            <div className="px-4 py-3 border-b border-white/6 flex items-center gap-2">
              <User className="w-3.5 h-3.5 text-zinc-500" />
              <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                {selectedSubmission ? `Grading — ${selectedSubmission.student_name ?? 'Student'}` : 'Grade Panel'}
              </h3>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {!selectedSubmission ? (
                <EmptyState
                  icon={<Users className="w-6 h-6" />}
                  title="Select a submission"
                  description="Click a student from the queue to start grading."
                />
              ) : (
                <GradePanel
                  key={selectedSubmission.id}
                  submission={selectedSubmission}
                  maxMarks={selectedAssignmentData?.total_marks ?? 100}
                  criteria={selectedAssignmentData?.criteria ?? []}
                  onDone={() => setSelectedSubmission(null)}
                />
              )}
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
