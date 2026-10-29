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

/** A calendar date (YYYY-MM-DD) split for a date tile: weekday, day of month, month. */
export function formatDayParts(date: string, lang: Lang) {
  const day = new Date(`${date}T00:00:00Z`)
  const part = (options: Intl.DateTimeFormatOptions) =>
    new Intl.DateTimeFormat(LOCALES[lang], { ...options, timeZone: 'UTC' }).format(day)
  return {
    weekday: part({ weekday: 'short' }),
    day: day.getUTCDate(),
    month: part({ month: 'short' }),
    full: part({ weekday: 'long', day: 'numeric', month: 'numeric' }),
  }
}

/** "19:30:00" from the API as "19:30". */
export function formatClock(time: string): string {
  return time.slice(0, 5)
}

/** Fills `{name}` placeholders in a translated string. */
export function interpolate(template: string, values: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (match, key: string) =>
    key in values ? String(values[key]) : match,
  )
}
