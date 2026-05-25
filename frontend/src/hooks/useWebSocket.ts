import { useEffect, useRef } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { useNotificationStore } from '@/stores/notificationStore'
import toast from 'react-hot-toast'
import type { WSEvent } from '@/types'

export function useWebSocket() {
  const { accessToken, isAuthenticated } = useAuthStore()
  const addNotification = useNotificationStore(s => s.addNotification)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const MAX_RECONNECT_ATTEMPTS = 3

  const connect = () => {
    if (!isAuthenticated || !accessToken) return
    if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) return

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const wsUrl = `${protocol}://${window.location.host}/ws?token=${accessToken}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('[WS] Connected')
      reconnectAttemptsRef.current = 0
    }

    ws.onmessage = e => {
      try {
        const event: WSEvent = JSON.parse(e.data)
        toast(event.message, {
          icon: eventIcon(event.type),
          style: {
            background: '#1A1A1E',
            color: '#F4F4F5',
            border: '1px solid rgba(255,255,255,0.08)',
          },
        })
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

    ws.onclose = () => {
      console.log('[WS] Disconnected')
      // Attempt to reconnect with exponential backoff
      if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttemptsRef.current += 1
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000)
        reconnectTimeoutRef.current = setTimeout(connect, delay)
      }
    }

    ws.onerror = () => {
      console.debug('[WS] Connection error (WebSocket proxy may not be configured)')
    }
  }

  useEffect(() => {
    connect()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
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
