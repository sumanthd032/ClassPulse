import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Award, TrendingUp, Star, MessageSquare, ChevronRight } from 'lucide-react'
import { dashboardApi } from '@/api/dashboard'
import { Card, SkeletonCard } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { GradeTrendChart } from '@/components/GradeTrendChart'
import { formatDate } from '@/lib/utils'
import type { StudentGrade } from '@/types'

function ScoreBar({ score, max }: { score: number; max: number }) {
  const pct = Math.min(100, Math.round((score / max) * 100))
  const color = pct >= 80 ? 'bg-emerald-500' : pct >= 60 ? 'bg-amber-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-white/8 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-zinc-500 w-8 text-right">{pct}%</span>
    </div>
  )
}

function GradeCard({ grade }: { grade: StudentGrade }) {
  const pct = Math.round((grade.total_score / grade.total_marks) * 100)
  const variant = pct >= 80 ? 'success' : pct >= 60 ? 'warning' : 'danger'
  const letter = pct >= 90 ? 'A' : pct >= 80 ? 'B' : pct >= 70 ? 'C' : pct >= 60 ? 'D' : 'F'

  return (
    <Card hover className="group">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0 pr-4">
          <p className="text-sm font-semibold text-zinc-200 truncate">{grade.assignment_title}</p>
          <p className="text-xs text-zinc-500 mt-0.5">{grade.classroom_name}</p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <Badge variant={variant}>{letter}</Badge>
          <span className="text-xl font-bold text-zinc-100">{grade.total_score}<span className="text-sm font-normal text-zinc-500">/{grade.total_marks}</span></span>
        </div>
      </div>

      <ScoreBar score={grade.total_score} max={grade.total_marks} />

      {grade.teacher_comments && (
        <div className="mt-3 flex items-start gap-2 text-xs text-zinc-500 bg-bg-elevated rounded-xl px-3 py-2">
          <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-zinc-600" />
          <p className="leading-relaxed line-clamp-2">{grade.teacher_comments}</p>
        </div>
      )}

      <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/5">
        <p className="text-[10px] text-zinc-600">Graded {formatDate(grade.graded_at)}</p>
        <Link
          to={`/assignments/${grade.assignment_id}`}
          className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors flex items-center gap-1"
          onClick={e => e.stopPropagation()}
        >
          View assignment <ChevronRight className="w-3 h-3" />
        </Link>
      </div>
    </Card>
  )
}

export default function GradesPage() {
  const { data: grades = [], isLoading } = useQuery({
    queryKey: ['my-grades'],
    queryFn: dashboardApi.grades,
  })

  const { data: trends = [] } = useQuery({
    queryKey: ['grade-trends'],
    queryFn: dashboardApi.gradeTrends,
  })

  const avgScore = grades.length
    ? Math.round(grades.reduce((acc, g) => acc + (g.total_score / g.total_marks) * 100, 0) / grades.length)
    : null

  const highest = grades.length
    ? Math.max(...grades.map(g => Math.round((g.total_score / g.total_marks) * 100)))
    : null

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h2 className="text-xl font-bold text-zinc-100">My Grades</h2>
        <p className="text-sm text-zinc-500 mt-0.5">Released grades from your teachers</p>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : !grades.length ? (
        <EmptyState
          icon={<Star className="w-6 h-6" />}
          title="No grades yet"
          description="Your teacher hasn't released any grades yet. Check back after submissions are graded."
        />
      ) : (
        <>
          {/* Grade trend chart */}
          {trends.length > 0 && (
            <Card>
              <h3 className="text-sm font-semibold text-zinc-300 mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-accent" /> Grade Trend
              </h3>
              <GradeTrendChart data={trends} />
            </Card>
          )}

          {/* Summary bar */}
          <div className="grid grid-cols-3 gap-4">
            <Card className="text-center">
              <TrendingUp className="w-5 h-5 text-violet-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-zinc-100">{avgScore != null ? `${avgScore}%` : '—'}</p>
              <p className="text-xs text-zinc-500 mt-0.5">Average score</p>
            </Card>
            <Card className="text-center">
              <Award className="w-5 h-5 text-emerald-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-zinc-100">{highest != null ? `${highest}%` : '—'}</p>
              <p className="text-xs text-zinc-500 mt-0.5">Highest score</p>
            </Card>
            <Card className="text-center">
              <Star className="w-5 h-5 text-amber-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-zinc-100">{grades.length}</p>
              <p className="text-xs text-zinc-500 mt-0.5">Graded assignments</p>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {grades.map(g => <GradeCard key={g.id} grade={g} />)}
          </div>
        </>
      )}
    </div>
  )
}
