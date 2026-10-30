import { z } from 'zod'
import { localizedTextSchema } from '@/lib/localized'

export const reviewPhotoSchema = z.object({
  id: z.number(),
  url: z.string(),
  thumbnail_url: z.string(),
})

export const reviewSchema = z.object({
  id: z.number(),
  rating: z.number().int().min(1).max(5),
  comment: z.string(),
  created_at: z.string(),
  user_name: z.string(),
  verified_purchase: z.boolean(),
  reply: z.string().nullable(),
  replied_at: z.string().nullable(),
  photos: z.array(reviewPhotoSchema),
})

export const topReviewSchema = reviewSchema.extend({
  product_name: localizedTextSchema,
  product_slug: z.string(),
})

export const ratingSummarySchema = z.object({
  average: z.string().nullable(),
  count: z.number().int(),
  distribution: z.array(z.object({ stars: z.number().int(), count: z.number().int() })),
})

export const reviewPageSchema = z.object({
  items: z.array(reviewSchema),
  page: z.number(),
  page_size: z.number(),
  total: z.number(),
  total_pages: z.number(),
  summary: ratingSummarySchema,
})

export const eligibilitySchema = z.object({
  can_review: z.boolean(),
  reason: z.enum(['not_purchased', 'already_reviewed']).nullable(),
})

export const REVIEW_SORTS = ['newest', 'highest', 'lowest'] as const
export const REVIEW_PAGE_SIZE = 5
export const COMMENT_MAX = 2000
export const MAX_PHOTOS = 3

export type Review = z.infer<typeof reviewSchema>
export type TopReview = z.infer<typeof topReviewSchema>
export type ReviewPage = z.infer<typeof reviewPageSchema>
export type ReviewSort = (typeof REVIEW_SORTS)[number]
