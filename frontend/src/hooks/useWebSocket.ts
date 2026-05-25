import { useEffect, useRef } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { useNotificationStore } from '@/stores/notificationStore'
import toast from 'react-hot-toast'
import type { WSEvent } from '@/types'

const IS_DEV = (import.meta as any).env.DEV

export function useWebSocket() {
  const { accessToken, isAuthenticated } = useAuthStore()
  const addNotification = useNotificationStore(s => s.addNotification)
  const wsRef = useRef<WebSocket | null>(null)
  const pollingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const lastNotificationIdRef = useRef<string>('')

  // Fallback: Poll for notifications in dev mode
  const pollNotifications = async () => {
    if (!isAuthenticated || !accessToken) return

    try {
      const response = await fetch('/api/v1/notifications?limit=10', {
        headers: { 'Authorization': `Bearer ${accessToken}` },
      })
      if (!response.ok) return

      const notifications = await response.json()
      // Only show new ones since last poll
      const newOnes = notifications.filter((n: any) => n.id !== lastNotificationIdRef.current)
      newOnes.forEach((n: any) => {
        if (!n.is_read) {
          toast(n.message, {
            icon: eventIcon(n.type),
            style: {
              background: '#1A1A1E',
              color: '#F4F4F5',
              border: '1px solid rgba(255,255,255,0.08)',
            },
          })
          addNotification(n)
          lastNotificationIdRef.current = n.id
        }
      })
    } catch (err) {
      console.debug('[Polling] Error fetching notifications')
    }

    pollingTimeoutRef.current = setTimeout(pollNotifications, 5000) // Poll every 5s
  }

  const connectWebSocket = () => {
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
    }

    ws.onerror = () => {
      if (!IS_DEV) {
        console.error('[WS] Connection failed')
      }
    }
  }

  useEffect(() => {
    if (!isAuthenticated || !accessToken) return

    if (IS_DEV) {
      // In dev: use polling instead of WebSocket (Vite proxy issue)
      pollNotifications()
    } else {
      // In production: use WebSocket
      connectWebSocket()
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (pollingTimeoutRef.current) {
        clearTimeout(pollingTimeoutRef.current)
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
