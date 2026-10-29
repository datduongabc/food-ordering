import { queryOptions, useQuery } from '@tanstack/react-query'
import { api, isApiError } from '@/lib/api/client'
import { userSchema, type User } from './schemas'

export const authQueries = {
  me: () =>
    queryOptions({
      queryKey: ['auth', 'me'],
      // Anonymous visitors get a 401; that is an answer ("nobody"), not a failure.
      queryFn: async (): Promise<User | null> => {
        try {
          return await api.get('/auth/me', userSchema)
        } catch (error) {
          if (isApiError(error, 401)) return null
          throw error
        }
      },
      staleTime: 5 * 60 * 1000,
    }),
}

/** The signed-in user, `null` for visitors, `undefined` while the first check is running. */
export function useCurrentUser(): User | null | undefined {
  return useQuery(authQueries.me()).data
}
