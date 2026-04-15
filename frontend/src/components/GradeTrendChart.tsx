import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import type { GradeTrend } from '@/types'

interface Props {
  data: GradeTrend[]
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload?.length) {
    const d = payload[0].payload as GradeTrend
    return (
      <div className="bg-bg-elevated border border-white/12 rounded-xl px-3 py-2 shadow-modal">
        <p className="text-xs text-zinc-500 mb-1 max-w-[180px] truncate">{d.assignment_title}</p>
        <p className="text-lg font-bold text-accent">{d.pct}%</p>
        <p className="text-xs text-zinc-500">{d.score}/{d.total_marks} pts</p>
      </div>
    )
  }
  return null
}

export function GradeTrendChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-zinc-600 text-sm">
        No grades to display yet
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
        <XAxis
          dataKey="assignment_title"
          tick={{ fill: '#52525B', fontSize: 10 }}
          tickFormatter={v => v.length > 12 ? v.slice(0, 12) + '…' : v}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fill: '#52525B', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={v => `${v}%`}
        />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={60} stroke="rgba(239,68,68,0.3)" strokeDasharray="4 4" />
        <ReferenceLine y={75} stroke="rgba(245,158,11,0.3)" strokeDasharray="4 4" />
        <Line
          type="monotone"
          dataKey="pct"
          stroke="#7C3AED"
          strokeWidth={2}
          dot={{ fill: '#7C3AED', r: 3, strokeWidth: 0 }}
          activeDot={{ r: 5, fill: '#8B5CF6', strokeWidth: 0 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
