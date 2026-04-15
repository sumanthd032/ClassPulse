import { useAuthStore } from '@/stores/authStore'
import { authApi } from '@/api/auth'
import { useMutation, useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'

export function useAuth() {
  const { user, isAuthenticated, setAuth, logout: storeLogout } = useAuthStore()
  const navigate = useNavigate()

  const loginMutation = useMutation({
    mutationFn: (data: { email: string; password: string }) => authApi.login(data),
    onSuccess: async tokens => {
      localStorage.setItem('access_token', tokens.access_token)
      localStorage.setItem('refresh_token', tokens.refresh_token)
      const me = await authApi.me()
      setAuth(me, tokens.access_token, tokens.refresh_token)
      navigate('/dashboard')
    },
    onError: () => toast.error('Invalid email or password'),
  })

  const registerMutation = useMutation({
    mutationFn: (data: { email: string; password: string; full_name: string; role: string }) =>
      authApi.register(data),
    onSuccess: () => {
      toast.success('Account created! Please log in.')
      navigate('/login')
    },
    onError: (err: any) =>
      toast.error(err.response?.data?.detail || 'Registration failed'),
  })

  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSettled: () => {
      storeLogout()
      navigate('/login')
    },
  })

  return {
    user,
    isAuthenticated,
    login: loginMutation.mutate,
    isLoggingIn: loginMutation.isPending,
    register: registerMutation.mutate,
    isRegistering: registerMutation.isPending,
    logout: logoutMutation.mutate,
  }
}
