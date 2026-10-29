import { useCallback } from 'react'
import { ApiError } from '@/lib/api/client'
import { formatVnd, interpolate } from '@/lib/format'
import { useI18n } from './context'
import type { Dictionary } from './dictionary'

// Params that hold enum values or money need translating/formatting before they are shown.
function displayParam(key: string, value: unknown, t: Dictionary): string {
  if (Array.isArray(value)) return value.map(String).join(', ')
  if ((key === 'from' || key === 'to' || key === 'status') && typeof value === 'string') {
    return t.orderStatus[value] ?? value
  }
  if (key.endsWith('_vnd') && typeof value === 'number') return formatVnd(value)
  return String(value)
}

export function errorMessage(error: unknown, t: Dictionary): string {
  if (error instanceof ApiError) {
    const template = error.code ? t.errors[error.code] : undefined
    if (!template) return t.errors.generic ?? ''
    const values = Object.fromEntries(
      Object.entries(error.params).map(([key, value]) => [key, displayParam(key, value, t)]),
    )
    return interpolate(template, values)
  }
  if (error instanceof TypeError) return t.errors.network ?? ''
  return t.errors.generic ?? ''
}

/** Turns any thrown error into a sentence in the current language. */
export function useErrorMessage(): (error: unknown) => string {
  const { t } = useI18n()
  return useCallback((error: unknown) => errorMessage(error, t), [t])
}
