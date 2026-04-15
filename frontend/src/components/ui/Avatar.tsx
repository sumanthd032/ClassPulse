import { cn, getInitials, avatarColor } from '@/lib/utils'

interface AvatarProps {
  name: string
  size?: 'xs' | 'sm' | 'md' | 'lg'
  className?: string
  src?: string
}

const sizes = {
  xs: 'w-6 h-6 text-[10px]',
  sm: 'w-8 h-8 text-xs',
  md: 'w-10 h-10 text-sm',
  lg: 'w-12 h-12 text-base',
}

export function Avatar({ name, size = 'md', className, src }: AvatarProps) {
  if (src) {
    return (
      <img
        src={src}
        alt={name}
        className={cn('rounded-full object-cover', sizes[size], className)}
      />
    )
  }
  return (
    <div
      className={cn(
        'rounded-full bg-gradient-to-br flex items-center justify-center font-semibold text-white flex-shrink-0',
        avatarColor(name),
        sizes[size],
        className
      )}
    >
      {getInitials(name)}
    </div>
  )
}
