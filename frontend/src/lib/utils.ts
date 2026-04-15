import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { format, formatDistanceToNow, isAfter, parseISO } from 'date-fns'

/** Merge Tailwind classes safely */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Format ISO date string → readable */
export function formatDate(iso: string): string {
  return format(parseISO(iso), 'MMM d, yyyy')
}

/** Format ISO date string → date + time */
export function formatDateTime(iso: string): string {
  return format(parseISO(iso), 'MMM d, yyyy · h:mm a')
}

/** Format ISO date → "3 hours ago" */
export function timeAgo(iso: string): string {
  return formatDistanceToNow(parseISO(iso), { addSuffix: true })
}

/** Format ISO date → "3 hours ago" (alias used in components) */
export { formatDistanceToNow as formatDistanceToNowRaw }

/** Wrapper: formatDistanceToNow from a string */
export function formatDistanceToNowStr(iso: string): string {
  return formatDistanceToNow(parseISO(iso), { addSuffix: true })
}

/** Check if a deadline has passed */
export function isPastDeadline(deadline: string): boolean {
  return isAfter(new Date(), parseISO(deadline))
}

/** Deadline countdown label */
export function deadlineLabel(deadline: string): string {
  if (isPastDeadline(deadline)) return 'Past due'
  return `Due ${formatDistanceToNow(parseISO(deadline), { addSuffix: true })}`
}

/** Get initials from full name */
export function getInitials(name: string): string {
  return name
    .split(' ')
    .slice(0, 2)
    .map(n => n[0])
    .join('')
    .toUpperCase()
}

/** Deterministic avatar color from string */
export function avatarColor(seed: string): string {
  const colors = [
    'from-violet-500 to-purple-600',
    'from-blue-500 to-cyan-500',
    'from-emerald-500 to-teal-500',
    'from-orange-500 to-amber-500',
    'from-rose-500 to-pink-500',
    'from-indigo-500 to-blue-500',
  ]
  let hash = 0
  for (let i = 0; i < seed.length; i++) hash = seed.charCodeAt(i) + ((hash << 5) - hash)
  return colors[Math.abs(hash) % colors.length]
}

/** Truncate text */
export function truncate(text: string, max: number): string {
  return text.length > max ? text.slice(0, max) + '…' : text
}

/** Score color based on percentage */
export function scoreColor(score: number, total: number): string {
  const pct = (score / total) * 100
  if (pct >= 80) return 'text-emerald-400'
  if (pct >= 60) return 'text-amber-400'
  return 'text-red-400'
}
