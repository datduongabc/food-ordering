import { useMutation, useQueryClient, type QueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { api, noContent } from '@/lib/api/client'
import { guestCart } from '@/features/cart/guestCart'
import { cartSchema } from '@/features/cart/schemas'
import { authQueries } from './queries'
import { userSchema, type User } from './schemas'

const acceptedSchema = z.object({ detail: z.string() })

export interface LoginInput {
  email: string
  password: string
  remember: boolean
}

export interface RegisterInput {
  name: string
  email: string
  phone: string
  password: string
}

/**
 * Folds the visitor's browser cart into the account, then publishes the user. Merging first
 * means the header never flashes the account cart without the dishes just picked.
 */
async function completeSignIn(queryClient: QueryClient, user: User) {
  const lines = guestCart.lines()
  if (lines.length > 0) {
    try {
      const cart = await api.post('/cart/merge', cartSchema, { items: lines })
      guestCart.clear()
      queryClient.setQueryData(['cart', 'account'], cart)
    } catch {
      // Keep the browser cart; the customer can still add the dishes again.
    }
  } else {
    await queryClient.invalidateQueries({ queryKey: ['cart', 'account'] })
  }
  queryClient.setQueryData(authQueries.me().queryKey, user)
}

function login(input: LoginInput) {
  return api.post('/auth/login', userSchema, input)
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: login,
    onSuccess: (user) => completeSignIn(queryClient, user),
  })
}

export function useRegister() {
  const queryClient = useQueryClient()
  return useMutation({
    // Registration does not open a session, so sign straight in and ask for the email code.
    mutationFn: async (input: RegisterInput) => {
      await api.post('/auth/register', userSchema, input)
      const user = await login({ email: input.email, password: input.password, remember: false })
      await api.post('/auth/email/verification', acceptedSchema)
      return user
    },
    onSuccess: (user) => completeSignIn(queryClient, user),
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => api.post('/auth/logout', noContent),
    onSettled: () => {
      queryClient.setQueryData(authQueries.me().queryKey, null)
      queryClient.removeQueries({ queryKey: ['cart', 'account'] })
      queryClient.removeQueries({ queryKey: ['orders'] })
      queryClient.removeQueries({ queryKey: ['reservations'] })
    },
  })
}

export function useRequestVerification() {
  return useMutation({ mutationFn: () => api.post('/auth/email/verification', acceptedSchema) })
}

export function useVerifyEmail() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (code: string) => api.post('/auth/email/verify', userSchema, { code }),
    onSuccess: (user) => queryClient.setQueryData(authQueries.me().queryKey, user),
  })
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: (email: string) => api.post('/auth/password/forgot', acceptedSchema, { email }),
  })
}

export function useResetPassword() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: { email: string; code: string; new_password: string }) =>
      api.post('/auth/password/reset', noContent, input),
    // The reset signs out every session, including this browser's.
    onSuccess: () => queryClient.setQueryData(authQueries.me().queryKey, null),
  })
}
