'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { authApi, User } from '@/services/api'

export function useAuth() {
  const queryClient = useQueryClient()
  const router = useRouter()

  const {
    data: user,
    isLoading,
    error,
  } = useQuery<User>({
    queryKey: ['currentUser'],
    queryFn: authApi.getMe,
    retry: false,
    enabled: typeof window !== 'undefined' && !!localStorage.getItem('access_token'),
  })

  const loginMutation = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authApi.login(email, password),
    onSuccess: (data) => {
      localStorage.setItem('access_token', data.access_token)
      queryClient.invalidateQueries({ queryKey: ['currentUser'] })
      router.push('/dashboard')
    },
  })

  const registerMutation = useMutation({
    mutationFn: (data: {
      email: string
      password: string
      first_name?: string
      last_name?: string
      account_name: string
    }) => authApi.register(data),
    onSuccess: () => {
      router.push('/login?registered=true')
    },
  })

  const logout = () => {
    localStorage.removeItem('access_token')
    queryClient.clear()
    router.push('/login')
  }

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    error,
    login: loginMutation.mutate,
    loginError: loginMutation.error,
    isLoggingIn: loginMutation.isPending,
    register: registerMutation.mutate,
    registerError: registerMutation.error,
    isRegistering: registerMutation.isPending,
    logout,
  }
}
