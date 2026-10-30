import { keepPreviousData, queryOptions, useMutation, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { api } from '@/lib/api/client'
import type { OrderStatus } from '@/features/orders/schemas'
import {
  ADMIN_PAGE_SIZE,
  adminOrderSchema,
  adminProductSchema,
  adminReservationSchema,
  adminUserSchema,
  auditEntrySchema,
  type AuditGroup,
  dashboardSchema,
  pageSchema,
  paymentStatsSchema,
  ratingStatsSchema,
  revenueTrendSchema,
  topDishesSchema,
  type ProductInput,
  type ReservationStatus,
  type UserInput,
} from './schemas'

export interface OrderFilters {
  status?: OrderStatus
  page: number
}

export interface ReservationFilters {
  status?: ReservationStatus
  date?: string
  page: number
}

export interface UserFilters {
  q?: string
  includeDeactivated: boolean
  page: number
}

export const adminQueries = {
  dashboard: () =>
    queryOptions({
      queryKey: ['admin', 'dashboard'],
      queryFn: () => api.get('/admin/dashboard', dashboardSchema),
    }),
  revenue: (days: number) =>
    queryOptions({
      queryKey: ['admin', 'stats', 'revenue', days],
      queryFn: () => api.get('/admin/stats/revenue', revenueTrendSchema, { days }),
      placeholderData: keepPreviousData,
    }),
  topDishes: (days: number) =>
    queryOptions({
      queryKey: ['admin', 'stats', 'top-dishes', days],
      queryFn: () => api.get('/admin/stats/top-dishes', topDishesSchema, { days }),
      placeholderData: keepPreviousData,
    }),
  payments: (days: number) =>
    queryOptions({
      queryKey: ['admin', 'stats', 'payments', days],
      queryFn: () => api.get('/admin/stats/payments', paymentStatsSchema, { days }),
      placeholderData: keepPreviousData,
    }),
  ratings: () =>
    queryOptions({
      queryKey: ['admin', 'stats', 'ratings'],
      queryFn: () => api.get('/admin/stats/ratings', ratingStatsSchema),
    }),
  products: () =>
    queryOptions({
      queryKey: ['admin', 'products'],
      queryFn: () => api.get('/admin/products', z.array(adminProductSchema)),
    }),
  orders: ({ status, page }: OrderFilters) =>
    queryOptions({
      queryKey: ['admin', 'orders', 'list', { status, page }],
      queryFn: () =>
        api.get('/admin/orders', pageSchema(adminOrderSchema), {
          status,
          page,
          page_size: ADMIN_PAGE_SIZE,
        }),
      placeholderData: keepPreviousData,
    }),
  reservations: ({ status, date, page }: ReservationFilters) =>
    queryOptions({
      queryKey: ['admin', 'reservations', { status, date, page }],
      queryFn: () =>
        api.get('/admin/reservations', pageSchema(adminReservationSchema), {
          status,
          date,
          page,
          page_size: ADMIN_PAGE_SIZE,
        }),
      placeholderData: keepPreviousData,
    }),
  users: ({ q, includeDeactivated, page }: UserFilters) =>
    queryOptions({
      queryKey: ['admin', 'users', { q, includeDeactivated, page }],
      queryFn: () =>
        api.get('/admin/users', pageSchema(adminUserSchema), {
          q,
          include_deactivated: includeDeactivated || undefined,
          page,
          page_size: ADMIN_PAGE_SIZE,
        }),
      placeholderData: keepPreviousData,
    }),
  auditLog: ({ group, page }: { group?: AuditGroup; page: number }) =>
    queryOptions({
      queryKey: ['admin', 'audit', { group, page }],
      queryFn: () =>
        api.get('/admin/audit-log', pageSchema(auditEntrySchema), {
          action: group,
          page,
          page_size: ADMIN_PAGE_SIZE,
        }),
      placeholderData: keepPreviousData,
    }),
}

/** A CSV download is a plain link: the browser sends the session cookie and saves the file. */
export function exportUrl(
  report: 'orders' | 'revenue',
  query: Record<string, string | undefined>,
): string {
  const search = new URLSearchParams(
    Object.entries(query).filter((entry): entry is [string, string] => Boolean(entry[1])),
  )
  return `/api/admin/exports/${report}.csv?${search}`
}

/**
 * Any staff change can move the dashboard's numbers, so every admin query is refreshed.
 * Dish changes also reach the public menu.
 */
function useAdminMutation<TInput, TResult>(
  mutationFn: (input: TInput) => Promise<TResult>,
  { catalog = false, session = false } = {},
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin'] })
      if (catalog) await queryClient.invalidateQueries({ queryKey: ['products'] })
      // An admin may edit their own account, which the header shows.
      if (session) await queryClient.invalidateQueries({ queryKey: ['auth', 'me'] })
    },
  })
}

export function useChangeOrderStatus() {
  return useAdminMutation((input: { id: number; status: OrderStatus; note: string }) =>
    api.post(`/admin/orders/${input.id}/status`, adminOrderSchema, {
      status: input.status,
      note: input.note,
    }),
  )
}

export function useChangeReservationStatus() {
  return useAdminMutation((input: { id: number; status: ReservationStatus }) =>
    api.post(`/admin/reservations/${input.id}/status`, adminReservationSchema, {
      status: input.status,
    }),
  )
}

export function useSaveProduct() {
  return useAdminMutation(
    (input: { id?: number; values: ProductInput }) =>
      input.id === undefined
        ? api.post('/admin/products', adminProductSchema, input.values)
        : api.patch(`/admin/products/${input.id}`, adminProductSchema, input.values),
    { catalog: true },
  )
}

export function useUploadProductImage() {
  return useAdminMutation(
    (input: { id: number; file: File }) => {
      const form = new FormData()
      form.append('image', input.file)
      return api.put(`/admin/products/${input.id}/image`, adminProductSchema, form)
    },
    { catalog: true },
  )
}

export function useSetProductHidden() {
  return useAdminMutation(
    (input: { id: number; hidden: boolean }) =>
      api.post(
        `/admin/products/${input.id}/${input.hidden ? 'hide' : 'restore'}`,
        adminProductSchema,
      ),
    { catalog: true },
  )
}

export function useSaveUser() {
  return useAdminMutation(
    (input: { id?: number; values: UserInput }) =>
      input.id === undefined
        ? api.post('/admin/users', adminUserSchema, input.values)
        : api.patch(`/admin/users/${input.id}`, adminUserSchema, input.values),
    { session: true },
  )
}

export function useSetUserActive() {
  return useAdminMutation((input: { id: number; active: boolean }) =>
    api.post(
      `/admin/users/${input.id}/${input.active ? 'restore' : 'deactivate'}`,
      adminUserSchema,
    ),
  )
}
