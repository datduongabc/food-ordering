import type { Lang } from '@/i18n/dictionary'

const vndFormatter = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' })

export function formatVnd(amount: number): string {
  return vndFormatter.format(amount)
}

const LOCALES: Record<Lang, string> = { vi: 'vi-VN', en: 'en-GB' }
const TIME_ZONE = 'Asia/Ho_Chi_Minh'

export function formatDateTime(iso: string, lang: Lang): string {
  return new Intl.DateTimeFormat(LOCALES[lang], {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: TIME_ZONE,
  }).format(new Date(iso))
}

export function formatDate(iso: string, lang: Lang): string {
  return new Intl.DateTimeFormat(LOCALES[lang], {
    dateStyle: 'medium',
    timeZone: TIME_ZONE,
  }).format(new Date(iso))
}

/** Fills `{name}` placeholders in a translated string. */
export function interpolate(template: string, values: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (match, key: string) =>
    key in values ? String(values[key]) : match,
  )
}
