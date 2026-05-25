import { useEffect, useRef } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { useNotificationStore } from '@/stores/notificationStore'
import toast from 'react-hot-toast'
import type { WSEvent } from '@/types'

export function useWebSocket() {
  const { accessToken, isAuthenticated } = useAuthStore()
  const addNotification = useNotificationStore(s => s.addNotification)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!isAuthenticated || !accessToken) return

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const wsUrl = `${protocol}://${window.location.host}/ws?token=${accessToken}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('[WS] Connected')
    }

    ws.onmessage = e => {
      try {
        const event: WSEvent = JSON.parse(e.data)
        // Show a toast
        toast(event.message, {
          icon: eventIcon(event.type),
          style: {
            background: '#1A1A1E',
            color: '#F4F4F5',
            border: '1px solid rgba(255,255,255,0.08)',
          },
        })
        // Push into notification store (will appear in bell)
        addNotification({
          id: crypto.randomUUID(),
          user_id: '',
          type: event.type,
          title: event.title,
          message: event.message,
          is_read: false,
          created_at: new Date().toISOString(),
        })
      } catch { /* ignore malformed messages */ }
    }

    ws.onclose = () => console.log('[WS] Disconnected')
    ws.onerror = (e) => {
      console.error('[WS] Error:', e)
    }

    return () => ws.close()
  }, [isAuthenticated, accessToken])
}

function eventIcon(type: string): string {
  const icons: Record<string, string> = {
    GRADE_RELEASED: '📊',
    FEEDBACK_READY: '✨',
    NEW_ASSIGNMENT: '📋',
    PLAGIARISM_FLAG: '🚨',
    REMINDER: '⏰',
    AT_RISK: '⚠️',
  }
  return icons[type] ?? '🔔'
}
