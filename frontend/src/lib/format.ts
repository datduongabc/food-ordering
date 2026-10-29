import type { Lang } from '@/i18n/dictionary'

// Menu prices are stored in USD (inherited from the PHP data); the restaurant charges in VND
// at the same fixed rate the backend uses for MoMo (MOMO_USD_TO_VND_RATE).
export const USD_TO_VND = 25_000

const vndFormatter = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' })

export function formatVnd(amount: number): string {
  return vndFormatter.format(amount)
}

/** Formats a USD decimal string from the API as the VND amount the customer pays. */
export function formatPrice(usd: string | number): string {
  return formatVnd(Math.round(Number(usd) * USD_TO_VND))
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
