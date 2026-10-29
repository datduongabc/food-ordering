import { useCallback } from 'react'
import type { LocalizedText } from '@/lib/localized'
import { useI18n } from './context'

/** Picks the current language out of a `{vi, en}` value from the API. */
export function useLocalize(): (text: LocalizedText) => string {
  const { lang } = useI18n()
  return useCallback((text: LocalizedText) => text[lang], [lang])
}
