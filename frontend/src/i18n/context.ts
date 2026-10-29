import { createContext, use } from 'react'
import type { Dictionary, Lang } from './dictionary'

export interface I18nValue {
  lang: Lang
  t: Dictionary
  setLang: (lang: Lang) => void
}

export const I18nContext = createContext<I18nValue | null>(null)

export function useI18n(): I18nValue {
  const value = use(I18nContext)
  if (!value) throw new Error('useI18n must be used inside <I18nProvider>')
  return value
}
