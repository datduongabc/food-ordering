import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { en } from './en'
import { vi } from './vi'
import { I18nContext } from './context'
import type { Dictionary, Lang } from './dictionary'
import { readStorage, writeStorage } from '@/lib/storage'

const STORAGE_KEY = 'dateno_lang'
const DICTIONARIES: Record<Lang, Dictionary> = { vi, en }

function initialLang(): Lang {
  return readStorage(STORAGE_KEY) === 'en' ? 'en' : 'vi'
}

export function I18nProvider({ children, lang: fixedLang }: { children: ReactNode; lang?: Lang }) {
  const [lang, setLangState] = useState<Lang>(() => fixedLang ?? initialLang())

  const setLang = useCallback((next: Lang) => {
    setLangState(next)
    writeStorage(STORAGE_KEY, next)
  }, [])

  useEffect(() => {
    document.documentElement.lang = lang
    document.title = DICTIONARIES[lang].meta.title
  }, [lang])

  const value = useMemo(() => ({ lang, t: DICTIONARIES[lang], setLang }), [lang, setLang])
  return <I18nContext value={value}>{children}</I18nContext>
}
