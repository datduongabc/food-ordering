import { queryOptions, useMutation, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { api } from '@/lib/api/client'
import { reviewSchema, topReviewSchema } from './schemas'

export const reviewQueries = {
  forProduct: (slug: string) =>
    queryOptions({
      queryKey: ['reviews', 'product', slug],
      queryFn: () =>
        api.get(`/products/${encodeURIComponent(slug)}/reviews`, z.array(reviewSchema)),
    }),
  top: (limit = 3) =>
    queryOptions({
      queryKey: ['reviews', 'top', limit],
      queryFn: () => api.get('/reviews/top', z.array(topReviewSchema), { limit }),
    }),
}

export interface ReviewInput {
  rating: number
  comment: string
}

export function useCreateReview(slug: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: ReviewInput) =>
      api.post(`/products/${encodeURIComponent(slug)}/reviews`, reviewSchema, input),
    onSuccess: () => {
      // The review changes the dish's average rating, which every product query may show.
      void queryClient.invalidateQueries({ queryKey: ['reviews'] })
      void queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })
}
