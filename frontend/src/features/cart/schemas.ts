import { z } from 'zod'
import { productSchema } from '@/features/catalog/schemas'

export const MAX_QUANTITY = 99

export const cartSchema = z.object({
  items: z.array(
    z.object({
      product: productSchema,
      quantity: z.number().int(),
      subtotal: z.string(),
    }),
  ),
  total_count: z.number().int(),
  total_price: z.string(),
})

export const guestLineSchema = z.object({
  product_id: z.number().int(),
  quantity: z.number().int().min(1).max(MAX_QUANTITY),
})

export type Cart = z.infer<typeof cartSchema>
export type CartLine = Cart['items'][number]
export type GuestLine = z.infer<typeof guestLineSchema>
