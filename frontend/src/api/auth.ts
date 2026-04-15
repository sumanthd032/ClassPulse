import client from './client'
import type { User, TokenResponse } from '@/types'

export const authApi = {
  register: (data: { email: string; password: string; full_name: string; role: string }) =>
    client.post<User>('/auth/register', data).then(r => r.data),

  login: (data: { email: string; password: string }) =>
    client.post<TokenResponse>('/auth/login', data).then(r => r.data),

  logout: () => client.post('/auth/logout'),

  me: () => client.get<User>('/auth/me').then(r => r.data),

  updateProfile: (data: { full_name?: string; avatar_url?: string; password?: string }) =>
    client.patch<User>('/auth/me', data).then(r => r.data),
}
