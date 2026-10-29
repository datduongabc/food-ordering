import { describe, expect, it } from 'vitest'
import { safeNext } from '@/features/auth/validation'

describe('safeNext', () => {
  it.each(['/menu', '/menu/pho-bo#reviews', '/account?tab=orders'])('follows %s', (path) => {
    expect(safeNext(path)).toBe(path)
  })

  it.each([null, '', 'menu', 'https://evil.example', '//evil.example', '/\\evil.example'])(
    'refuses %s and falls back home',
    (path) => {
      expect(safeNext(path)).toBe('/')
    },
  )
})
