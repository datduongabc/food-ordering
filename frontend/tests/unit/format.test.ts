import { describe, expect, it } from 'vitest'
import { formatDateTime, formatPrice, formatVnd, interpolate } from '@/lib/format'

describe('formatPrice', () => {
  it('converts the stored USD price to the VND amount charged', () => {
    expect(formatPrice('9.50')).toMatch(/^237\.500\s₫$/)
    expect(formatPrice(18)).toMatch(/^450\.000\s₫$/)
  })

  it('rounds to whole dong', () => {
    expect(formatPrice('0.01')).toMatch(/^250\s₫$/)
    expect(formatPrice('0.00002')).toMatch(/^1\s₫$/)
  })
})

describe('formatVnd', () => {
  it('uses Vietnamese grouping', () => {
    expect(formatVnd(50_000_000)).toMatch(/^50\.000\.000\s₫$/)
  })
})

describe('formatDateTime', () => {
  it('shows the restaurant time, whatever the browser time zone', () => {
    expect(formatDateTime('2026-10-29T11:30:00Z', 'vi')).toContain('18:30')
  })
})

describe('interpolate', () => {
  it('fills known placeholders and leaves unknown ones visible', () => {
    expect(interpolate('{a} và {b}', { a: 1 })).toBe('1 và {b}')
  })
})
