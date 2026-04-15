import { cn } from '@/lib/utils'

interface CardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
  onClick?: () => void
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

const paddings = { none: '', sm: 'p-4', md: 'p-5', lg: 'p-6' }

export function Card({ children, className, hover, onClick, padding = 'md' }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'relative overflow-hidden bg-gradient-to-b from-white/[0.055] to-white/[0.02] backdrop-blur-xl rounded-2xl shadow-card border border-white/10',
        hover && 'hover:shadow-card-hover hover:border-white/20 hover:-translate-y-0.5 transition-all duration-200 cursor-pointer',
        onClick && 'cursor-pointer',
        paddings[padding],
        className
      )}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/25 to-transparent" />
      {children}
    </div>
  )
}

export function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('flex items-center justify-between mb-4', className)}>
      {children}
    </div>
  )
}

export function CardTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return <h3 className={cn('text-base font-semibold text-zinc-100', className)}>{children}</h3>
}

// Skeleton card
export function SkeletonCard() {
  return (
    <div className="bg-bg-surface rounded-2xl p-5 border border-white/7">
      <div className="skeleton h-4 w-2/3 mb-3" />
      <div className="skeleton h-3 w-full mb-2" />
      <div className="skeleton h-3 w-4/5" />
    </div>
  )
}
