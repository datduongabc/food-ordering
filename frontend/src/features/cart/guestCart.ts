import { useSyncExternalStore } from 'react'
import { z } from 'zod'
import { readStorage, removeStorage, writeStorage } from '@/lib/storage'
import { guestLineSchema, MAX_QUANTITY, type GuestLine } from './schemas'

// Visitors who have not signed in keep their cart in the browser; the server prices it via
// /cart/preview and folds it into the account cart (/cart/merge) when they sign in.
const STORAGE_KEY = 'dateno_guest_cart'
const EMPTY: readonly GuestLine[] = []

let snapshot: readonly GuestLine[] = load()
const listeners = new Set<() => void>()

function load(): readonly GuestLine[] {
  const raw = readStorage(STORAGE_KEY)
  if (!raw) return EMPTY
  try {
    const parsed = z.array(guestLineSchema).safeParse(JSON.parse(raw))
    return parsed.success ? parsed.data : EMPTY
  } catch {
    return EMPTY
  }
}

function emit(next: readonly GuestLine[]) {
  snapshot = next
  for (const listener of listeners) listener()
}

function save(next: readonly GuestLine[]) {
  if (next.length === 0) removeStorage(STORAGE_KEY)
  else writeStorage(STORAGE_KEY, JSON.stringify(next))
  emit(next)
}

function onStorage(event: StorageEvent) {
  // Keeps several open tabs showing the same cart.
  if (event.key === STORAGE_KEY || event.key === null) emit(load())
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  if (listeners.size === 1) window.addEventListener('storage', onStorage)
  return () => {
    listeners.delete(listener)
    if (listeners.size === 0) window.removeEventListener('storage', onStorage)
  }
}

export const guestCart = {
  lines: () => snapshot,
  add(productId: number, quantity: number) {
    const existing = snapshot.find((line) => line.product_id === productId)
    if (!existing) {
      save([...snapshot, { product_id: productId, quantity: Math.min(quantity, MAX_QUANTITY) }])
      return
    }
    guestCart.setQuantity(productId, existing.quantity + quantity)
  },
  setQuantity(productId: number, quantity: number) {
    const capped = Math.min(quantity, MAX_QUANTITY)
    save(
      snapshot.map((line) =>
        line.product_id === productId ? { ...line, quantity: capped } : line,
      ),
    )
  },
  remove(productId: number) {
    save(snapshot.filter((line) => line.product_id !== productId))
  },
  clear() {
    save(EMPTY)
  },
  /** Re-reads storage; tests use it after seeding localStorage directly. */
  reload() {
    emit(load())
  },
}

export function useGuestCartLines(): readonly GuestLine[] {
  return useSyncExternalStore(subscribe, guestCart.lines, () => EMPTY)
}
