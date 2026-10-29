import { useMemo } from 'react'
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, noContent } from '@/lib/api/client'
import { useCurrentUser } from '@/features/auth/queries'
import { guestCart, useGuestCartLines } from './guestCart'
import { cartSchema, type Cart, type GuestLine } from './schemas'

export const ACCOUNT_CART_KEY = ['cart', 'account'] as const

export const EMPTY_CART: Cart = { items: [], total_count: 0, total_price: 0 }

function previewGuestCart(lines: readonly GuestLine[]): Promise<Cart> {
  if (lines.length === 0) return Promise.resolve(EMPTY_CART)
  return api.post('/cart/preview', cartSchema, { items: lines })
}

/**
 * One cart API for visitors and signed-in customers. Visitors' lines live in localStorage and
 * are priced by the server; customers' lines live in the database.
 */
export function useCart() {
  const user = useCurrentUser()
  const guestLines = useGuestCartLines()
  const signedIn = Boolean(user)

  const query = useQuery({
    queryKey: signedIn ? ACCOUNT_CART_KEY : ['cart', 'guest', guestLines],
    queryFn: () => (signedIn ? api.get('/cart', cartSchema) : previewGuestCart(guestLines)),
    // Wait for the session check so a customer's cart is never briefly shown as the guest cart.
    enabled: user !== undefined,
    placeholderData: keepPreviousData,
  })

  return { cart: query.data, isPending: query.isPending, error: query.error, signedIn }
}

type CartAction =
  | { type: 'add'; productId: number; quantity: number }
  | { type: 'set'; productId: number; quantity: number }
  | { type: 'remove'; productId: number }
  | { type: 'clear' }

async function runAccountAction(action: CartAction): Promise<Cart> {
  switch (action.type) {
    case 'add':
      return api.post('/cart/items', cartSchema, {
        product_id: action.productId,
        quantity: action.quantity,
      })
    case 'set':
      return api.put(`/cart/items/${action.productId}`, cartSchema, { quantity: action.quantity })
    case 'remove':
      return api.delete(`/cart/items/${action.productId}`, cartSchema)
    case 'clear':
      await api.delete('/cart', noContent)
      return EMPTY_CART
  }
}

function runGuestAction(action: CartAction) {
  switch (action.type) {
    case 'add':
      return guestCart.add(action.productId, action.quantity)
    case 'set':
      return guestCart.setQuantity(action.productId, action.quantity)
    case 'remove':
      return guestCart.remove(action.productId)
    case 'clear':
      return guestCart.clear()
  }
}

export function useCartActions() {
  const user = useCurrentUser()
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: async (action: CartAction) => {
      if (!user) {
        runGuestAction(action)
        return null
      }
      return runAccountAction(action)
    },
    onSuccess: (cart) => {
      if (cart) queryClient.setQueryData(ACCOUNT_CART_KEY, cart)
    },
  })

  const { mutateAsync, isPending } = mutation
  return useMemo(
    () => ({
      add: (productId: number, quantity = 1) => mutateAsync({ type: 'add', productId, quantity }),
      setQuantity: (productId: number, quantity: number) =>
        mutateAsync({ type: 'set', productId, quantity }),
      remove: (productId: number) => mutateAsync({ type: 'remove', productId }),
      clear: () => mutateAsync({ type: 'clear' }),
      isPending,
    }),
    [mutateAsync, isPending],
  )
}
