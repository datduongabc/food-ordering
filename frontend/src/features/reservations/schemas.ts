import { z } from 'zod'
import { locationSchema } from '@/features/catalog/schemas'

export const reservationSchema = z.object({
  id: z.number(),
  location: locationSchema,
  customer_name: z.string(),
  customer_phone: z.string(),
  reservation_date: z.iso.date(),
  reservation_time: z.iso.time(),
  guest_count: z.number().int(),
  special_requests: z.string(),
  status: z.enum(['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED']),
  created_at: z.string(),
  cancelled_at: z.string().nullable(),
  can_cancel: z.boolean(),
})

export const reservationPolicySchema = z.object({
  timezone: z.string(),
  today: z.iso.date(),
  last_bookable_date: z.iso.date(),
  max_guests: z.number().int(),
  opening_time: z.iso.time(),
  last_seating_time: z.iso.time(),
})

export type Reservation = z.infer<typeof reservationSchema>
export type ReservationPolicy = z.infer<typeof reservationPolicySchema>

export interface ReservationInput {
  location_id: number
  customer_name: string
  customer_phone: string
  reservation_date: string
  reservation_time: string
  guest_count: number
  special_requests: string
}
