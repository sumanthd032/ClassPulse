import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, TrendingUp, Users, Award, BarChart3 } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import { dashboardApi } from '@/api/dashboard'
import { Card, SkeletonCard } from '@/components/ui/Card'

const BUCKET_COLORS = {
  '0-39':   '#EF4444',
  '40-59':  '#F59E0B',
  '60-74':  '#3B82F6',
  '75-89':  '#8B5CF6',
  '90-100': '#10B981',
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload?.length) {
    return (
      <div className="bg-bg-elevated border border-white/12 rounded-xl px-3 py-2 shadow-modal">
        <p className="text-xs text-zinc-400">{payload[0].payload.range}%</p>
        <p className="text-base font-bold text-zinc-100">{payload[0].value} students</p>
      </div>
    )
  }
  return null
}

export default function ClassroomAnalyticsPage() {
  const { id } = useParams<{ id: string }>()

  const { data: analytics, isLoading } = useQuery({
    queryKey: ['analytics', id],
    queryFn: () => dashboardApi.classroomAnalytics(id!),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="max-w-3xl space-y-4">
        <div className="skeleton h-8 w-48 rounded-lg" />
        <div className="grid grid-cols-3 gap-3">
          {[...Array(3)].map((_, i) => <div key={i} className="skeleton h-24 rounded-2xl" />)}
        </div>
        <SkeletonCard />
      </div>
    )
  }

  return (
    <div className="max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link
          to={`/classrooms/${id}`}
          className="p-2 rounded-xl hover:bg-white/6 text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-zinc-100 tracking-tight">Analytics</h1>
          <p className="text-sm text-zinc-500 mt-0.5">Grade distribution and performance insights</p>
        </div>
      </div>

      {analytics ? (
        <>
          {/* Stat cards */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-bg-surface border border-white/6 rounded-2xl p-4 text-center">
              <div className="w-9 h-9 rounded-xl bg-accent/10 flex items-center justify-center mx-auto mb-2">
                <Award className="w-4 h-4 text-accent" />
              </div>
              <p className="text-2xl font-bold text-zinc-100 tabular-nums">{analytics.average_percentage}%</p>
              <p className="text-xs text-zinc-500 mt-0.5">Class Average</p>
            </div>
            <div className="bg-bg-surface border border-white/6 rounded-2xl p-4 text-center">
              <div className="w-9 h-9 rounded-xl bg-emerald-500/10 flex items-center justify-center mx-auto mb-2">
                <Users className="w-4 h-4 text-emerald-400" />
              </div>
              <p className="text-2xl font-bold text-zinc-100 tabular-nums">{analytics.total_grades}</p>
              <p className="text-xs text-zinc-500 mt-0.5">Grades Released</p>
            </div>
            <div className="bg-bg-surface border border-white/6 rounded-2xl p-4 text-center">
              <div className="w-9 h-9 rounded-xl bg-blue-500/10 flex items-center justify-center mx-auto mb-2">
                <TrendingUp className="w-4 h-4 text-blue-400" />
              </div>
              <p className="text-2xl font-bold text-zinc-100 tabular-nums">
                {analytics.grade_distribution.find(d => d.range === '90-100')?.count ?? 0}
              </p>
              <p className="text-xs text-zinc-500 mt-0.5">A-Range (90%+)</p>
            </div>
          </div>

          {/* Grade Distribution Chart */}
          <div className="bg-bg-surface border border-white/6 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-5">
              <BarChart3 className="w-4 h-4 text-accent" />
              <h2 className="text-sm font-semibold text-zinc-300">Grade Distribution</h2>
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart
                data={analytics.grade_distribution}
                margin={{ top: 4, right: 4, bottom: 0, left: -20 }}
                barCategoryGap="35%"
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                <XAxis
                  dataKey="range"
                  tick={{ fill: '#52525B', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#52525B', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  allowDecimals={false}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {analytics.grade_distribution.map(entry => (
                    <Cell
                      key={entry.range}
                      fill={BUCKET_COLORS[entry.range as keyof typeof BUCKET_COLORS] ?? '#7C3AED'}
                      fillOpacity={0.85}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            {/* Legend */}
            <div className="flex items-center gap-4 mt-4 flex-wrap">
              {Object.entries(BUCKET_COLORS).map(([range, color]) => (
                <div key={range} className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: color }} />
                  <span className="text-[11px] text-zinc-500">{range}%</span>
                </div>
              ))}
            </div>
          </div>

          {/* Pass/fail summary */}
          {analytics.total_grades > 0 && (
            <div className="bg-bg-surface border border-white/6 rounded-2xl p-5">
              <h2 className="text-sm font-semibold text-zinc-300 mb-4">Performance Summary</h2>
              <div className="space-y-2.5">
                {analytics.grade_distribution.map(bucket => {
                  const pct = analytics.total_grades > 0
                    ? Math.round((bucket.count / analytics.total_grades) * 100)
                    : 0
                  const color = BUCKET_COLORS[bucket.range as keyof typeof BUCKET_COLORS] ?? '#7C3AED'
                  return (
                    <div key={bucket.range} className="flex items-center gap-3">
                      <span className="text-xs text-zinc-500 w-16 text-right tabular-nums">{bucket.range}%</span>
                      <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{ width: `${pct}%`, background: color }}
                        />
                      </div>
                      <span className="text-xs text-zinc-400 w-6 tabular-nums">{bucket.count}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="bg-bg-surface border border-white/6 rounded-2xl p-16 text-center">
          <BarChart3 className="w-10 h-10 text-zinc-700 mx-auto mb-3" />
          <p className="text-zinc-500 text-sm">No grade data available yet</p>
          <p className="text-zinc-700 text-xs mt-1">Release grades to see analytics here</p>
        </div>
      )}
    </div>
  )
}
