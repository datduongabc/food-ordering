import { keepPreviousData, queryOptions, useMutation, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { api } from '@/lib/api/client'
import {
  REVIEW_PAGE_SIZE,
  eligibilitySchema,
  reviewPageSchema,
  reviewSchema,
  topReviewSchema,
  type ReviewSort,
} from './schemas'

export interface ReviewFilters {
  page: number
  rating?: number
  sort: ReviewSort
}

const productPath = (slug: string) => `/products/${encodeURIComponent(slug)}/reviews`

export const reviewQueries = {
  forProduct: (slug: string, { page, rating, sort }: ReviewFilters) =>
    queryOptions({
      queryKey: ['reviews', 'product', slug, { page, rating, sort }],
      queryFn: () =>
        api.get(productPath(slug), reviewPageSchema, {
          page,
          rating,
          sort,
          page_size: REVIEW_PAGE_SIZE,
        }),
      placeholderData: keepPreviousData,
    }),
  eligibility: (slug: string) =>
    queryOptions({
      queryKey: ['reviews', 'eligibility', slug],
      queryFn: () => api.get(`${productPath(slug)}/eligibility`, eligibilitySchema),
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
  photos: File[]
}

/** Posts the review, then its photos one by one; a photo that fails leaves the review up. */
export function useCreateReview(slug: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ photos, ...input }: ReviewInput) => {
      const review = await api.post(productPath(slug), reviewSchema, input)
      let failedPhotos = 0
      for (const file of photos) {
        const form = new FormData()
        form.append('photo', file)
        try {
          await api.post(`/reviews/${review.id}/photos`, reviewSchema, form)
        } catch {
          failedPhotos += 1
        }
      }
      return { review, failedPhotos }
    },
    onSuccess: () => {
      // The review changes the dish's average rating, which every product query may show.
      void queryClient.invalidateQueries({ queryKey: ['reviews'] })
      void queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })
}
