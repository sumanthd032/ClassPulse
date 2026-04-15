import { cn } from '@/lib/utils'

interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 text-center', className)}>
      {icon && (
        <div className="w-14 h-14 rounded-2xl bg-bg-elevated border border-white/8 flex items-center justify-center text-zinc-500 mb-4">
          {icon}
        </div>
      )}
      <h3 className="text-base font-medium text-zinc-300 mb-1">{title}</h3>
      {description && <p className="text-sm text-zinc-500 max-w-xs mb-4">{description}</p>}
      {action}
    </div>
  )
}
