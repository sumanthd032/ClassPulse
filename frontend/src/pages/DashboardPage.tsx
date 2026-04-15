import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  BookOpen, ClipboardList, Send, TrendingUp, AlertCircle,
  Clock, ChevronRight, CheckCircle2, Star, Calendar, Award
} from 'lucide-react'
import { dashboardApi } from '@/api/dashboard'
import { useAuthStore } from '@/stores/authStore'
import { Card, SkeletonCard } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import type { StudentDashboard, TeacherDashboard } from '@/types'
import { formatDate, timeAgo } from '@/lib/utils'

function StatCard({ icon, label, value, color = 'text-accent', sub, href }: {
  icon: React.ReactNode; label: string; value: number | string
  color?: string; sub?: string; href?: string
}) {
  const content = (
    <Card hover={!!href} className="group">
      <div className="flex items-start justify-between">
        <div className={`w-11 h-11 rounded-2xl flex items-center justify-center flex-shrink-0 ${color} bg-current/10`}>
          <span className={color}>{icon}</span>
        </div>
        {href && <ChevronRight className="w-4 h-4 text-zinc-700 group-hover:text-zinc-400 transition-colors" />}
      </div>
      <div className="mt-4">
        <p className="text-3xl font-bold text-zinc-100 tabular-nums">{value}</p>
        <p className="text-sm text-zinc-500 font-medium mt-1">{label}</p>
        {sub && <p className="text-xs text-zinc-600 mt-0.5">{sub}</p>}
      </div>
    </Card>
  )
  return href ? <Link to={href}>{content}</Link> : content
}

function StudentView({ data }: { data: StudentDashboard }) {
  const urgentDeadlines = data.upcoming_deadlines?.filter(d => {
    const daysLeft = (new Date(d.deadline).getTime() - Date.now()) / 86_400_000
    return daysLeft < 2
  }) ?? []

  return (
    <div className="space-y-6">
      {/* Urgent alert */}
      {urgentDeadlines.length > 0 && (
        <div className="flex items-center gap-3 bg-amber-500/10 border border-amber-500/20 rounded-2xl px-4 py-3">
          <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <p className="text-sm text-amber-300">
            <span className="font-semibold">{urgentDeadlines.length} assignment{urgentDeadlines.length > 1 ? 's' : ''}</span> due within 48 hours — don't miss the deadline!
          </p>
        </div>
      )}

      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={<BookOpen className="w-5 h-5" />} label="Enrolled Classes" value={data.enrolled_classes} color="text-blue-400" href="/classrooms" />
        <StatCard icon={<ClipboardList className="w-5 h-5" />} label="Active Assignments" value={data.active_assignments} color="text-amber-400" />
        <StatCard icon={<Send className="w-5 h-5" />} label="Submissions Made" value={data.total_submissions} color="text-emerald-400" />
        <StatCard icon={<TrendingUp className="w-5 h-5" />} label="Average Score" value={data.avg_score != null ? `${data.avg_score}%` : '—'} color="text-violet-400" sub="across released grades" href="/grades" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Upcoming deadlines */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
              <Calendar className="w-4 h-4 text-amber-400" /> Upcoming Deadlines
            </h3>
            <Link to="/classrooms" className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors">View all →</Link>
          </div>
          {!data.upcoming_deadlines?.length ? (
            <div className="text-center py-6">
              <CheckCircle2 className="w-8 h-8 text-emerald-500/50 mx-auto mb-2" />
              <p className="text-sm text-zinc-600">All caught up! No upcoming deadlines.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {data.upcoming_deadlines.map(d => {
                const daysLeft = Math.ceil((new Date(d.deadline).getTime() - Date.now()) / 86_400_000)
                const isUrgent = daysLeft < 2
                return (
                  <Link key={d.id} to={`/assignments/${d.id}`}
                    className="flex items-center gap-3 p-3 rounded-xl hover:bg-white/4 transition-colors group border border-transparent hover:border-white/6"
                  >
                    <div className={`w-2 h-2 rounded-full flex-shrink-0 ${isUrgent ? 'bg-amber-400' : 'bg-blue-400'}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-zinc-300 truncate">{d.title}</p>
                      <p className="text-xs text-zinc-600">{d.classroom_name}</p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <Badge variant={isUrgent ? 'warning' : 'muted'} className="text-xs">
                        {daysLeft === 0 ? 'Today' : daysLeft === 1 ? 'Tomorrow' : `${daysLeft}d`}
                      </Badge>
                      <p className="text-[10px] text-zinc-700 mt-0.5">{d.total_marks} pts</p>
                    </div>
                  </Link>
                )
              })}
            </div>
          )}
        </Card>

        {/* Recent grades */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
              <Award className="w-4 h-4 text-violet-400" /> Recent Grades
            </h3>
            <Link to="/grades" className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors">View all →</Link>
          </div>
          {!data.recent_grades?.length ? (
            <div className="text-center py-6">
              <Star className="w-8 h-8 text-zinc-700 mx-auto mb-2" />
              <p className="text-sm text-zinc-600">No grades released yet.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {data.recent_grades.map(g => (
                <div key={g.id} className="flex items-center gap-3 p-3 rounded-xl hover:bg-white/4 transition-colors">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-zinc-300 truncate">{g.assignment_title}</p>
                    <p className="text-xs text-zinc-600">{g.classroom_name} · {timeAgo(g.graded_at)}</p>
                  </div>
                  <span className="text-sm font-bold text-emerald-400 flex-shrink-0">{g.total_score}</span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}

function TeacherView({ data }: { data: TeacherDashboard }) {
  return (
    <div className="space-y-6">
      {data.pending_grades > 0 && (
        <div className="flex items-center justify-between bg-violet-500/10 border border-violet-500/20 rounded-2xl px-4 py-3">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-4 h-4 text-violet-400 flex-shrink-0" />
            <p className="text-sm text-violet-300">
              <span className="font-semibold">{data.pending_grades} submission{data.pending_grades > 1 ? 's' : ''}</span> waiting to be graded.
            </p>
          </div>
          <Link to="/grading" className="text-xs font-medium text-violet-400 hover:text-violet-300 transition-colors">Grade now →</Link>
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard icon={<BookOpen className="w-5 h-5" />} label="Active Classes" value={data.active_classes} color="text-blue-400" href="/classrooms" />
        <StatCard icon={<ClipboardList className="w-5 h-5" />} label="Total Assignments" value={data.total_assignments} color="text-amber-400" />
        <StatCard icon={<AlertCircle className="w-5 h-5" />} label="Pending Grades" value={data.pending_grades} color="text-red-400" sub="need your attention" href="/grading" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link to="/classrooms">
          <Card hover className="group">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center text-blue-400">
                <BookOpen className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <p className="font-semibold text-zinc-200">My Classrooms</p>
                <p className="text-sm text-zinc-500">Manage classes and assignments</p>
              </div>
              <ChevronRight className="w-4 h-4 text-zinc-600 group-hover:text-zinc-300 transition-colors" />
            </div>
          </Card>
        </Link>
        <Link to="/grading">
          <Card hover className="group border-violet-500/20">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-violet-500/10 flex items-center justify-center text-violet-400">
                <Star className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <p className="font-semibold text-zinc-200">Grade Submissions</p>
                <p className="text-sm text-zinc-500">Review and score student work</p>
              </div>
              <ChevronRight className="w-4 h-4 text-zinc-600 group-hover:text-zinc-300 transition-colors" />
            </div>
          </Card>
        </Link>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { user } = useAuthStore()
  const { data, isLoading } = useQuery({ queryKey: ['dashboard'], queryFn: dashboardApi.get })

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

  return (
    <div className="max-w-5xl space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-zinc-100">
          {greeting},{' '}
          <span className="bg-gradient-to-r from-violet-400 to-blue-400 bg-clip-text text-transparent">
            {user?.full_name.split(' ')[0]}
          </span>{' '}👋
        </h2>
        <p className="text-sm text-zinc-500 mt-1">
          {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </p>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : data ? (
        data.role === 'student'
          ? <StudentView data={data as StudentDashboard} />
          : <TeacherView data={data as TeacherDashboard} />
      ) : null}
    </div>
  )
}
