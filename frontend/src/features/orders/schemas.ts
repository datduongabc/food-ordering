import { z } from 'zod'
import { locationSchema } from '@/features/catalog/schemas'
import { localizedTextSchema } from '@/lib/localized'

export const ORDER_STATUSES = ['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED'] as const
export const PAYMENT_METHODS = ['COD', 'MOMO'] as const
export const PAYMENT_STATUSES = ['UNPAID', 'PAID', 'FAILED', 'REFUNDED'] as const

export const orderStatusSchema = z.enum(ORDER_STATUSES)
export const paymentMethodSchema = z.enum(PAYMENT_METHODS)
export const paymentStatusSchema = z.enum(PAYMENT_STATUSES)

export const orderEventSchema = z.object({
  from_status: orderStatusSchema.nullable(),
  to_status: orderStatusSchema,
  actor: z.enum(['customer', 'staff', 'system']),
  note: z.string(),
  created_at: z.string(),
})

export const orderItemSchema = z.object({
  product_id: z.number(),
  product_name: localizedTextSchema,
  product_slug: z.string(),
  image_url: z.string(),
  price_at_purchase: z.number().int(),
  quantity: z.number().int(),
  subtotal: z.number().int(),
})

export const orderSchema = z.object({
  id: z.number(),
  status: orderStatusSchema,
  payment_method: paymentMethodSchema,
  payment_status: paymentStatusSchema,
  total_price: z.number().int(),
  created_at: z.string(),
  location: locationSchema.nullable(),
  delivery_name: z.string().nullable(),
  delivery_phone: z.string().nullable(),
  delivery_address: z.string().nullable(),
  delivery_note: z.string().nullable(),
  items: z.array(orderItemSchema),
  events: z.array(orderEventSchema),
  can_cancel: z.boolean(),
  can_pay: z.boolean(),
})

export const momoPaymentSchema = z.object({
  order_id: z.number(),
  momo_order_id: z.string(),
  amount: z.number().int(),
  mode: z.string(),
})

export type Order = z.infer<typeof orderSchema>
export type OrderEvent = z.infer<typeof orderEventSchema>
export type OrderStatus = z.infer<typeof orderStatusSchema>
export type PaymentMethod = z.infer<typeof paymentMethodSchema>
export type PaymentStatus = z.infer<typeof paymentStatusSchema>
export type MomoPayment = z.infer<typeof momoPaymentSchema>

export interface CheckoutInput {
  payment_method: PaymentMethod
  location_id: number
  delivery_name: string
  delivery_phone: string
  delivery_address: string
  delivery_note: string
}
