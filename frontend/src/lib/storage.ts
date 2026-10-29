// Storage can throw (private mode, blocked site data), and losing a preference or a guest
// cart must never break the page, so every access is guarded.

export function readStorage(key: string): string | null {
  try {
    return window.localStorage.getItem(key)
  } catch {
    return null
  }
}

export function writeStorage(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value)
  } catch {
    // Ignored: the value simply will not survive a reload.
  }
}

export function removeStorage(key: string): void {
  try {
    window.localStorage.removeItem(key)
  } catch {
    // Ignored for the same reason as writeStorage.
  }
}
