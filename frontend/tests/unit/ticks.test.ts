import { describe, expect, it } from 'vitest'
import { niceTicks } from '@/features/admin/components/ticks'

describe('niceTicks', () => {
  it('has only a zero line when there is nothing to plot', () => {
    expect(niceTicks(0)).toEqual([0])
  })

  it('steps by 1, 2 or 5 times a power of ten and covers the maximum', () => {
    expect(niceTicks(1_150_000)).toEqual([0, 500_000, 1_000_000, 1_500_000])
    expect(niceTicks(800_000)).toEqual([0, 200_000, 400_000, 600_000, 800_000])
    expect(niceTicks(37)).toEqual([0, 10, 20, 30, 40])
  })
})
