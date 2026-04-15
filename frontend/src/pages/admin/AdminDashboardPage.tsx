import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Users, BookOpen, ClipboardList, Send, Star, AlertCircle, Shield,
} from 'lucide-react'
import { adminApi } from '@/api/admin'
import { Card, SkeletonCard } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Avatar } from '@/components/ui/Avatar'
import { formatDate } from '@/lib/utils'

interface StatTileProps {
  icon: React.ReactNode
  label: string
  value: number
  color: string
  sub?: string
}

function StatTile({ icon, label, value, color, sub }: StatTileProps) {
  return (
    <Card className="flex items-start gap-4">
      <div className={`w-10 h-10 rounded-xl bg-bg-elevated border border-white/8 flex items-center justify-center flex-shrink-0 ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-xs text-zinc-500 font-medium">{label}</p>
        <p className="text-2xl font-bold text-zinc-100 mt-0.5 leading-none">{value.toLocaleString()}</p>
        {sub && <p className="text-xs text-zinc-600 mt-1">{sub}</p>}
      </div>
    </Card>
  )
}

type Tab = 'overview' | 'users' | 'classrooms'

export default function AdminDashboardPage() {
  const [tab, setTab] = useState<Tab>('overview')
  const [userRole, setUserRole] = useState('')

  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: adminApi.stats,
  })

  const { data: users, isLoading: loadingUsers } = useQuery({
    queryKey: ['admin-users', userRole],
    queryFn: () => adminApi.users({ role: userRole || undefined, limit: 100 }),
    enabled: tab === 'users',
  })

  const { data: classrooms, isLoading: loadingClassrooms } = useQuery({
    queryKey: ['admin-classrooms'],
    queryFn: () => adminApi.classrooms({ limit: 100 }),
    enabled: tab === 'classrooms',
  })

  return (
    <div className="max-w-5xl">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
          <Shield className="w-5 h-5 text-amber-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-zinc-100">Admin Dashboard</h2>
          <p className="text-sm text-zinc-500">Platform-wide analytics and management</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-bg-elevated p-1 rounded-xl w-fit">
        {(['overview', 'users', 'classrooms'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all capitalize ${
              tab === t ? 'bg-bg-surface text-zinc-200 shadow-sm' : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {tab === 'overview' && (
        <>
          {loadingStats ? (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[...Array(8)].map((_, i) => <SkeletonCard key={i} />)}
            </div>
          ) : stats ? (
            <>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                <StatTile icon={<Users className="w-5 h-5" />} label="Total Users" value={stats.total_users} color="text-blue-400" />
                <StatTile icon={<Users className="w-5 h-5" />} label="Students" value={stats.total_students} color="text-emerald-400" />
                <StatTile icon={<Users className="w-5 h-5" />} label="Teachers" value={stats.total_teachers} color="text-violet-400" />
                <StatTile icon={<BookOpen className="w-5 h-5" />} label="Classrooms" value={stats.total_classrooms} color="text-cyan-400" />
              </div>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatTile icon={<ClipboardList className="w-5 h-5" />} label="Assignments" value={stats.total_assignments} color="text-amber-400" />
                <StatTile icon={<Send className="w-5 h-5" />} label="Submissions" value={stats.total_submissions} color="text-pink-400" />
                <StatTile icon={<Star className="w-5 h-5" />} label="Grades Given" value={stats.total_grades} color="text-yellow-400" />
                <StatTile
                  icon={<AlertCircle className="w-5 h-5" />}
                  label="Pending Grades"
                  value={stats.pending_grades}
                  color="text-red-400"
                  sub="awaiting review"
                />
              </div>
            </>
          ) : null}
        </>
      )}

      {/* Users Tab */}
      {tab === 'users' && (
        <Card padding="none">
          <div className="flex items-center gap-3 px-4 py-3 border-b border-white/6">
            <h3 className="text-sm font-semibold text-zinc-300 flex-1">
              Users {users ? <span className="text-zinc-600 font-normal ml-1">({users.total})</span> : ''}
            </h3>
            <select
              value={userRole}
              onChange={e => setUserRole(e.target.value)}
              className="bg-bg-elevated border border-white/8 rounded-lg px-2 py-1 text-xs text-zinc-300 focus:outline-none"
            >
              <option value="">All roles</option>
              <option value="student">Students</option>
              <option value="teacher">Teachers</option>
              <option value="admin">Admins</option>
            </select>
          </div>

          {loadingUsers ? (
            <div className="p-4 space-y-3">
              {[...Array(6)].map((_, i) => <div key={i} className="skeleton h-10 rounded-xl" />)}
            </div>
          ) : (
            <div className="divide-y divide-white/4">
              {users?.items.map(u => (
                <div key={u.id} className="flex items-center gap-3 px-4 py-2.5">
                  <Avatar name={u.full_name} size="sm" src={u.avatar_url} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-zinc-300 truncate">{u.full_name}</p>
                    <p className="text-xs text-zinc-600 truncate">{u.email}</p>
                  </div>
                  <Badge
                    variant={u.role === 'admin' ? 'warning' : u.role === 'teacher' ? 'purple' : 'muted'}
                    className="capitalize"
                  >
                    {u.role}
                  </Badge>
                </div>
              ))}
              {!users?.items.length && (
                <p className="text-center text-zinc-600 text-sm py-10">No users found</p>
              )}
            </div>
          )}
        </Card>
      )}

      {/* Classrooms Tab */}
      {tab === 'classrooms' && (
        <Card padding="none">
          <div className="px-4 py-3 border-b border-white/6">
            <h3 className="text-sm font-semibold text-zinc-300">
              Classrooms {classrooms ? <span className="text-zinc-600 font-normal ml-1">({classrooms.total})</span> : ''}
            </h3>
          </div>

          {loadingClassrooms ? (
            <div className="p-4 space-y-3">
              {[...Array(5)].map((_, i) => <div key={i} className="skeleton h-10 rounded-xl" />)}
            </div>
          ) : (
            <div className="divide-y divide-white/4">
              {classrooms?.items.map(c => (
                <div key={c.id} className="flex items-center gap-4 px-4 py-3">
                  <div className="w-9 h-9 rounded-xl bg-accent/10 flex items-center justify-center text-xs font-bold text-accent flex-shrink-0">
                    {c.subject_code.slice(0, 2)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-zinc-300 truncate">{c.name}</p>
                    <p className="text-xs text-zinc-600">{c.subject_code} · {c.section} · {c.semester}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-sm font-semibold text-zinc-300">{c.student_count}</p>
                    <p className="text-[10px] text-zinc-600">students</p>
                  </div>
                  <span className="text-xs text-zinc-600 flex-shrink-0 hidden sm:block">{formatDate(c.created_at)}</span>
                </div>
              ))}
              {!classrooms?.items.length && (
                <p className="text-center text-zinc-600 text-sm py-10">No classrooms found</p>
              )}
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
