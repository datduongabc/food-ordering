import type {
  AdminOrder,
  AdminProduct,
  AdminReservation,
  AdminUser,
  Page,
} from '@/features/admin/schemas'
import type { User } from '@/features/auth/schemas'
import { customer, order, reservation, springRolls } from './fixtures'

export const admin: User = { ...customer, id: 1, name: 'Quản lý Hà', role: 'ADMIN' }

export function page<T>(items: T[], overrides: Partial<Page<T>> = {}): Page<T> {
  return { items, page: 1, page_size: 20, total: items.length, total_pages: 1, ...overrides }
}

export function adminOrder(overrides: Partial<AdminOrder> = {}): AdminOrder {
  const base = order({ id: 31, delivery_note: 'Gọi trước khi giao' })
  return {
    ...base,
    customer: { id: 7, name: 'Nguyen Van A', email: 'a@example.com', phone: '0901234567' },
    momo_order_id: null,
    momo_trans_id: null,
    events: base.events.map((event) => ({ ...event, actor_name: null })),
    ...overrides,
  }
}

export const adminDish: AdminProduct = {
  ...springRolls,
  created_at: '2026-10-01T03:00:00Z',
  deleted_at: null,
}

export function adminUser(overrides: Partial<AdminUser> = {}): AdminUser {
  return { ...customer, deleted_at: null, ...overrides }
}

export function adminReservation(overrides: Partial<AdminReservation> = {}): AdminReservation {
  return { ...reservation(), user_id: customer.id, ...overrides }
}
