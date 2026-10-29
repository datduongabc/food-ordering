import { z } from 'zod'

export const categorySchema = z.object({
  id: z.number(),
  name: z.string(),
  slug: z.string(),
})

export const locationSchema = z.object({
  id: z.number(),
  name: z.string(),
  address: z.string(),
  map_url: z.url(),
})

export const productSchema = z.object({
  id: z.number(),
  name: z.string(),
  slug: z.string(),
  description: z.string(),
  price: z.string(),
  average_rating: z.string().nullable(),
  category: categorySchema.nullable(),
  locations: z.array(locationSchema),
  image_url: z.string(),
})

export const productPageSchema = z.object({
  items: z.array(productSchema),
  page: z.number(),
  page_size: z.number(),
  total: z.number(),
  total_pages: z.number(),
})

export const PRODUCT_SORTS = [
  'default',
  'price_asc',
  'price_desc',
  'rating_desc',
  'rating_asc',
] as const
export const productSortSchema = z.enum(PRODUCT_SORTS)

export type Category = z.infer<typeof categorySchema>
export type Location = z.infer<typeof locationSchema>
export type Product = z.infer<typeof productSchema>
export type ProductPage = z.infer<typeof productPageSchema>
export type ProductSort = z.infer<typeof productSortSchema>
