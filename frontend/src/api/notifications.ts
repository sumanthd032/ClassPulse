import client from './client'
import type { Notification } from '@/types'

export const notificationsApi = {
  list: () => client.get<Notification[]>('/notifications').then(r => r.data),

  markRead: (id: string) => client.patch(`/notifications/${id}/read`),

  markAllRead: () => client.patch('/notifications/read-all'),
}
