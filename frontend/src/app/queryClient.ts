import { QueryClient } from '@tanstack/react-query'
import { ApiError } from '@/lib/api/client'

const MAX_RETRIES = 2

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30 * 1000,
        // A 4xx will not change by asking again; only network errors and 5xx are retried.
        retry: (failureCount, error) =>
          !(error instanceof ApiError && error.status < 500) && failureCount < MAX_RETRIES,
      },
    },
  })
}
