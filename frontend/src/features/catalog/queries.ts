import { keepPreviousData, queryOptions } from '@tanstack/react-query'
import { z } from 'zod'
import { api } from '@/lib/api/client'
import {
  categorySchema,
  locationSchema,
  productPageSchema,
  productSchema,
  type ProductSort,
} from './schemas'

export const MENU_PAGE_SIZE = 12
const STATIC_DATA = 10 * 60 * 1000

export interface ProductListParams {
  page: number
  sort: ProductSort
  category?: string
  pageSize?: number
}

export const catalogQueries = {
  categories: () =>
    queryOptions({
      queryKey: ['categories'],
      queryFn: () => api.get('/categories', z.array(categorySchema)),
      staleTime: STATIC_DATA,
    }),
  locations: () =>
    queryOptions({
      queryKey: ['locations'],
      queryFn: () => api.get('/locations', z.array(locationSchema)),
      staleTime: STATIC_DATA,
    }),
  products: ({ page, sort, category, pageSize = MENU_PAGE_SIZE }: ProductListParams) =>
    queryOptions({
      queryKey: ['products', 'list', { page, sort, category, pageSize }],
      queryFn: () =>
        api.get('/products', productPageSchema, { page, sort, category, page_size: pageSize }),
      placeholderData: keepPreviousData,
    }),
  search: (query: string) =>
    queryOptions({
      queryKey: ['products', 'search', query],
      queryFn: () => api.get('/products/search', z.array(productSchema), { q: query, limit: 20 }),
      enabled: query.length > 0,
      placeholderData: keepPreviousData,
    }),
  featured: () =>
    queryOptions({
      queryKey: ['products', 'featured'],
      queryFn: () => api.get('/products/featured', productSchema.nullable()),
    }),
  product: (slug: string) =>
    queryOptions({
      queryKey: ['products', 'detail', slug],
      queryFn: () => api.get(`/products/${encodeURIComponent(slug)}`, productSchema),
    }),
}
