import { useCallback } from 'react'
import { ApiError } from '@/lib/api/client'
import { formatVnd, interpolate } from '@/lib/format'
import { isLocalizedText } from '@/lib/localized'
import { useI18n } from './context'
import type { Dictionary, Lang } from './dictionary'

// Params can hold catalog text ({vi, en}), enum values, money or waits, which need the current
// language or formatting before they are shown.
function displayParam(key: string, value: unknown, t: Dictionary, lang: Lang): string {
  if (Array.isArray(value)) return value.map((item) => displayParam(key, item, t, lang)).join(', ')
  if (isLocalizedText(value)) return value[lang]
  if ((key === 'from' || key === 'to' || key === 'status') && typeof value === 'string') {
    return t.orderStatus[value] ?? value
  }
  if (key.endsWith('_vnd') && typeof value === 'number') return formatVnd(value)
  // Waits run up to an hour; past a minute, rounding up to whole minutes reads better.
  if (key === 'seconds' && typeof value === 'number') {
    return value < 60
      ? interpolate(t.common.seconds, { count: value })
      : interpolate(t.common.minutes, { count: Math.ceil(value / 60) })
  }
  return String(value)
}

export function errorMessage(error: unknown, t: Dictionary, lang: Lang): string {
  if (error instanceof ApiError) {
    const template = error.code ? t.errors[error.code] : undefined
    if (!template) return t.errors.generic ?? ''
    const values = Object.fromEntries(
      Object.entries(error.params).map(([key, value]) => [key, displayParam(key, value, t, lang)]),
    )
    return interpolate(template, values)
  }
  if (error instanceof TypeError) return t.errors.network ?? ''
  return t.errors.generic ?? ''
}

/** Turns any thrown error into a sentence in the current language. */
export function useErrorMessage(): (error: unknown) => string {
  const { t, lang } = useI18n()
  return useCallback((error: unknown) => errorMessage(error, t, lang), [t, lang])
}
