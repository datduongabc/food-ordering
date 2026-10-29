import type { BadgeTone } from '@/components/ui/Badge'
import type { OrderStatus, PaymentStatus } from './schemas'

export const ORDER_TONE: Record<OrderStatus, BadgeTone> = {
  PENDING: 'amber',
  CONFIRMED: 'blue',
  COMPLETED: 'green',
  CANCELLED: 'stone',
}

export const PAYMENT_TONE: Record<PaymentStatus, BadgeTone> = {
  UNPAID: 'amber',
  PAID: 'green',
  FAILED: 'red',
  REFUNDED: 'stone',
}
