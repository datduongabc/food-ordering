import { describe, expect, it } from 'vitest'
import { formatDateTime, formatVnd, interpolate } from '@/lib/format'

describe('formatVnd', () => {
  it('uses Vietnamese grouping and the dong sign', () => {
    expect(formatVnd(237_500)).toMatch(/^237\.500\s₫$/)
    expect(formatVnd(50_000_000)).toMatch(/^50\.000\.000\s₫$/)
  })

  it('shows small amounts without decimals', () => {
    expect(formatVnd(500)).toMatch(/^500\s₫$/)
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
