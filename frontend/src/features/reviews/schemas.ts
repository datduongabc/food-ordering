import { z } from 'zod'
import { localizedTextSchema } from '@/lib/localized'

export const reviewSchema = z.object({
  id: z.number(),
  rating: z.number().int().min(1).max(5),
  comment: z.string(),
  created_at: z.string(),
  user_name: z.string(),
})

export const topReviewSchema = reviewSchema.extend({
  product_name: localizedTextSchema,
  product_slug: z.string(),
})

export const COMMENT_MAX = 2000

export type Review = z.infer<typeof reviewSchema>
export type TopReview = z.infer<typeof topReviewSchema>
