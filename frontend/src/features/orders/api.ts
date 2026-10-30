import { queryOptions, useMutation, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { api } from '@/lib/api/client'
import { EMPTY_CART, ACCOUNT_CART_KEY } from '@/features/cart/useCart'
import { momoPaymentSchema, orderSchema, type CheckoutInput, type Order } from './schemas'

export const orderQueries = {
  list: () =>
    queryOptions({
      queryKey: ['orders', 'list'],
      queryFn: () => api.get('/orders', z.array(orderSchema)),
    }),
  detail: (id: number) =>
    queryOptions({
      queryKey: ['orders', 'detail', id],
      queryFn: () => api.get(`/orders/${id}`, orderSchema),
    }),
  /**
   * Opening the payment page starts a MoMo attempt. It is a POST, but modelling it as a query
   * gives one attempt per visit (deduplicated across re-renders) and a natural "try again".
   */
  momo: (orderId: number) =>
    queryOptions({
      queryKey: ['orders', 'momo', orderId],
      queryFn: async ({ client }) => {
        const attempt = await api.post(`/orders/${orderId}/payments/momo`, momoPaymentSchema)
        // Starting an attempt switches a cash order to MoMo; the cached order must not lag behind.
        await client.invalidateQueries({ queryKey: ['orders', 'detail', orderId] })
        await client.invalidateQueries({ queryKey: ['orders', 'list'] })
        return attempt
      },
      staleTime: Infinity,
      gcTime: 0,
      retry: false,
      refetchOnWindowFocus: false,
    }),
  /** Hands the result MoMo put on the return URL to the API, which checks its signature. */
  momoReturn: (params: Record<string, string>) =>
    queryOptions({
      queryKey: ['orders', 'momo-return', params],
      queryFn: async ({ client }) => {
        const order = await api.post('/payments/momo/return', orderSchema, params)
        client.setQueryData(['orders', 'detail', order.id], order)
        await client.invalidateQueries({ queryKey: ['orders', 'list'] })
        return order
      },
      staleTime: Infinity,
      retry: false,
      refetchOnWindowFocus: false,
    }),
}

/** Keeps the list and the detail view in step after any change to one order. */
function useStoreOrder() {
  const queryClient = useQueryClient()
  return (order: Order) => {
    queryClient.setQueryData(orderQueries.detail(order.id).queryKey, order)
    queryClient.setQueryData(orderQueries.list().queryKey, (orders?: Order[]) =>
      orders ? orders.map((existing) => (existing.id === order.id ? order : existing)) : orders,
    )
  }
}

export function usePlaceOrder() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: CheckoutInput) => api.post('/orders', orderSchema, input),
    onSuccess: async (order) => {
      // The server empties the cart as part of placing the order.
      queryClient.setQueryData(ACCOUNT_CART_KEY, EMPTY_CART)
      queryClient.setQueryData(orderQueries.detail(order.id).queryKey, order)
      await queryClient.invalidateQueries({ queryKey: orderQueries.list().queryKey })
    },
  })
}

export function useCancelOrder() {
  const store = useStoreOrder()
  return useMutation({
    mutationFn: (orderId: number) => api.post(`/orders/${orderId}/cancel`, orderSchema),
    onSuccess: store,
  })
}

export function useSwitchToCod() {
  const store = useStoreOrder()
  return useMutation({
    mutationFn: (orderId: number) => api.post(`/orders/${orderId}/payments/cod`, orderSchema),
    onSuccess: store,
  })
}

export function useCompleteSandboxPayment() {
  const store = useStoreOrder()
  return useMutation({
    mutationFn: (input: { momo_order_id: string; result: 'approved' | 'declined' }) =>
      api.post('/payments/momo/sandbox/complete', orderSchema, input),
    onSuccess: store,
  })
}
