import { z } from 'zod'
import { userSchema } from '@/features/auth/schemas'
import { productSchema } from '@/features/catalog/schemas'
import { orderEventSchema, orderSchema } from '@/features/orders/schemas'
import { reservationSchema } from '@/features/reservations/schemas'
import { localizedTextSchema } from '@/lib/localized'

export function pageSchema<T extends z.ZodType>(item: T) {
  return z.object({
    items: z.array(item),
    page: z.number(),
    page_size: z.number(),
    total: z.number(),
    total_pages: z.number(),
  })
}

export interface Page<T> {
  items: T[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

export const ADMIN_PAGE_SIZE = 20

// --- Dashboard and statistics ---

export const dashboardSchema = z.object({
  completed_revenue: z.number().int(),
  completed_orders: z.number().int(),
  average_order_value: z.number().int(),
  total_orders: z.number().int(),
  pending_orders: z.number().int(),
  active_products: z.number().int(),
  customers: z.number().int(),
  total_reservations: z.number().int(),
  pending_reservations: z.number().int(),
})

export const revenueTrendSchema = z.object({
  days: z.array(
    z.object({ date: z.iso.date(), orders: z.number().int(), revenue: z.number().int() }),
  ),
  total_orders: z.number().int(),
  total_revenue: z.number().int(),
})

const dishSalesSchema = z.object({
  product_id: z.number(),
  name: localizedTextSchema,
  slug: z.string(),
  quantity: z.number().int(),
  revenue: z.number().int(),
})

export const topDishesSchema = z.object({
  by_quantity: z.array(dishSalesSchema),
  by_revenue: z.array(dishSalesSchema),
  least_sold: z.array(dishSalesSchema),
})

export const paymentStatsSchema = z.object({
  cod_orders: z.number().int(),
  momo_orders: z.number().int(),
  momo: z.object({
    paid: z.number().int(),
    failed: z.number().int(),
    success_rate: z.number().nullable(),
  }),
})

export const ratingStatsSchema = z.object({
  lowest_rated: z.array(
    z.object({
      product_id: z.number(),
      name: localizedTextSchema,
      slug: z.string(),
      average_rating: z.string(),
      review_count: z.number().int(),
    }),
  ),
  latest_reviews: z.array(
    z.object({
      id: z.number(),
      rating: z.number().int(),
      comment: z.string(),
      created_at: z.string(),
      user_name: z.string(),
      product_name: localizedTextSchema,
      product_slug: z.string(),
    }),
  ),
})

// --- Products ---

export const adminProductSchema = productSchema.extend({
  created_at: z.string(),
  deleted_at: z.string().nullable(),
})

export interface ProductInput {
  name: { vi: string; en: string }
  slug?: string
  description: { vi: string; en: string }
  price: number
  category_id: number
  location_ids: number[]
}

// --- Orders ---

export const adminOrderSchema = orderSchema.extend({
  customer: z.object({ id: z.number(), name: z.string(), email: z.string(), phone: z.string() }),
  momo_order_id: z.string().nullable(),
  momo_trans_id: z.string().nullable(),
  events: z.array(orderEventSchema.extend({ actor_name: z.string().nullable() })),
})

// --- Reservations ---

export const RESERVATION_STATUSES = ['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED'] as const

export const adminReservationSchema = reservationSchema.extend({ user_id: z.number().nullable() })

// --- Users ---

export const ROLES = ['CUSTOMER', 'ADMIN'] as const

export const adminUserSchema = userSchema.extend({ deleted_at: z.string().nullable() })

export interface UserInput {
  name: string
  email: string
  phone: string
  role: Role
  email_verified: boolean
  password?: string
}

export type Dashboard = z.infer<typeof dashboardSchema>
export type RevenueTrend = z.infer<typeof revenueTrendSchema>
export type DishSales = z.infer<typeof dishSalesSchema>
export type AdminProduct = z.infer<typeof adminProductSchema>
export type AdminOrder = z.infer<typeof adminOrderSchema>
export type AdminReservation = z.infer<typeof adminReservationSchema>
export type ReservationStatus = (typeof RESERVATION_STATUSES)[number]
export type AdminUser = z.infer<typeof adminUserSchema>
export type Role = (typeof ROLES)[number]
