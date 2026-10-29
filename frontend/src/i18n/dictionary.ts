import type { vi } from './vi'

export type Lang = 'vi' | 'en'
export const LANGS: readonly Lang[] = ['vi', 'en']

type Widen<T> = T extends string
  ? string
  : T extends Record<string, string>
    ? string extends keyof T
      ? Record<string, string>
      : { [K in keyof T]: string }
    : { [K in keyof T]: Widen<T[K]> }

/** Same keys as the Vietnamese dictionary, any string values. */
export type Dictionary = Widen<typeof vi>
