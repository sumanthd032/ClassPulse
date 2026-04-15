import { useState, useRef, useEffect } from 'react'
import { Bell } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi } from '@/api/notifications'
import { useNotificationStore } from '@/stores/notificationStore'
import { timeAgo } from '@/lib/utils'

export function NotificationBell() {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const qc = useQueryClient()
  const { notifications, unreadCount, setNotifications, markRead, markAllRead } = useNotificationStore()

  useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationsApi.list().then(data => { setNotifications(data); return data }),
    refetchInterval: 30_000,
  })

  const markAllMutation = useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => markAllRead(),
  })

  const markOneMutation = useMutation({
    mutationFn: notificationsApi.markRead,
    onSuccess: (_data, id) => markRead(id),
  })

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const typeIcon: Record<string, string> = {
    GRADE_RELEASED: '🎯',
    FEEDBACK_READY: '✨',
    NEW_ASSIGNMENT: '📋',
    PLAGIARISM_FLAG: '🚨',
    REMINDER: '⏰',
    AT_RISK: '⚠️',
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(v => !v)}
        className="relative p-2 rounded-xl hover:bg-white/6 text-zinc-400 hover:text-zinc-200 transition-colors"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 w-4 h-4 bg-accent text-white text-[9px] font-bold rounded-full flex items-center justify-center leading-none">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -4 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -4 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-full mt-2 w-80 bg-bg-surface border border-white/8 rounded-2xl shadow-modal z-50 overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/6">
              <span className="text-sm font-semibold text-zinc-200">Notifications</span>
              {unreadCount > 0 && (
                <button
                  onClick={() => markAllMutation.mutate()}
                  className="text-xs text-accent hover:text-accent/80 transition-colors"
                >
                  Mark all read
                </button>
              )}
            </div>

            {/* List */}
            <div className="max-h-80 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="py-10 text-center text-zinc-500 text-sm">No notifications yet</div>
              ) : (
                notifications.slice(0, 20).map(n => (
                  <button
                    key={n.id}
                    onClick={() => !n.is_read && markOneMutation.mutate(n.id)}
                    className={`w-full text-left px-4 py-3 flex gap-3 hover:bg-white/4 transition-colors border-b border-white/4 last:border-0 ${
                      !n.is_read ? 'bg-accent/5' : ''
                    }`}
                  >
                    <span className="text-base flex-shrink-0 mt-0.5">{typeIcon[n.type] ?? '🔔'}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-zinc-200 leading-snug">{n.title}</p>
                      <p className="text-xs text-zinc-500 mt-0.5 leading-snug line-clamp-2">{n.message}</p>
                      <p className="text-[10px] text-zinc-600 mt-1">{timeAgo(n.created_at)}</p>
                    </div>
                    {!n.is_read && (
                      <span className="w-1.5 h-1.5 rounded-full bg-accent flex-shrink-0 mt-1.5" />
                    )}
                  </button>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
