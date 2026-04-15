import { cn } from '@/lib/utils'

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'purple' | 'blue' | 'muted'

interface BadgeProps {
  variant?: BadgeVariant
  children: React.ReactNode
  className?: string
  dot?: boolean
}

const variants: Record<BadgeVariant, string> = {
  default:  'bg-zinc-800 text-zinc-300 border border-white/8',
  success:  'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
  warning:  'bg-amber-500/10  text-amber-400  border border-amber-500/20',
  danger:   'bg-red-500/10    text-red-400    border border-red-500/20',
  purple:   'bg-violet-500/10 text-violet-400 border border-violet-500/20',
  blue:     'bg-blue-500/10   text-blue-400   border border-blue-500/20',
  muted:    'bg-white/5       text-zinc-500   border border-white/8',
}

const dotColors: Record<BadgeVariant, string> = {
  default:  'bg-zinc-400',
  success:  'bg-emerald-400',
  warning:  'bg-amber-400',
  danger:   'bg-red-400',
  purple:   'bg-violet-400',
  blue:     'bg-blue-400',
  muted:    'bg-zinc-500',
}

export function Badge({ variant = 'default', children, className, dot }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium',
        variants[variant],
        className
      )}
    >
      {dot && <span className={cn('w-1.5 h-1.5 rounded-full', dotColors[variant])} />}
      {children}
    </span>
  )
}
