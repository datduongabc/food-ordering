import { beforeEach, describe, expect, it } from 'vitest'
import { guestCart } from '@/features/cart/guestCart'

const KEY = 'dateno_guest_cart'

describe('guestCart', () => {
  beforeEach(() => {
    window.localStorage.clear()
    guestCart.reload()
  })

  it('adds dishes and merges repeated adds into one line', () => {
    guestCart.add(1, 2)
    guestCart.add(2, 1)
    guestCart.add(1, 3)

    expect(guestCart.lines()).toEqual([
      { product_id: 1, quantity: 5 },
      { product_id: 2, quantity: 1 },
    ])
    expect(JSON.parse(window.localStorage.getItem(KEY) ?? '[]')).toEqual(guestCart.lines())
  })

  it('caps quantities at the 99 the API accepts', () => {
    guestCart.add(1, 98)
    guestCart.add(1, 5)
    expect(guestCart.lines()).toEqual([{ product_id: 1, quantity: 99 }])
  })

  it('removes lines and forgets an emptied cart', () => {
    guestCart.add(1, 1)
    guestCart.remove(1)
    expect(guestCart.lines()).toEqual([])
    expect(window.localStorage.getItem(KEY)).toBeNull()
  })

  it.each(['not json', '{"product_id":1}', '[{"product_id":1,"quantity":0}]'])(
    'ignores corrupted storage %s',
    (raw) => {
      window.localStorage.setItem(KEY, raw)
      guestCart.reload()
      expect(guestCart.lines()).toEqual([])
    },
  )
})
