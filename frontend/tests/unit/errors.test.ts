import { describe, expect, it } from 'vitest'
import { en } from '@/i18n/en'
import { errorMessage } from '@/i18n/errors'
import { vi } from '@/i18n/vi'
import { ApiError } from '@/lib/api/client'

function apiError(code: string | undefined, params: Record<string, unknown> = {}) {
  return new ApiError(400, code, params, 'English detail')
}

describe('errorMessage', () => {
  it('translates the code instead of showing the English detail', () => {
    expect(errorMessage(apiError('email_taken'), vi)).toBe('Email này đã được đăng ký.')
    expect(errorMessage(apiError('email_taken'), en)).toBe('This email is already registered.')
  })

  it('fills params, joining lists', () => {
    const error = apiError('dishes_unavailable_at_branch', {
      branch: 'DaTeNO - District 7',
      dishes: ['Pho', 'Spring Rolls'],
    })
    expect(errorMessage(error, vi)).toBe(
      'Pho, Spring Rolls hiện không phục vụ tại DaTeNO - District 7. Vui lòng chọn chi nhánh khác hoặc bỏ món khỏi giỏ hàng.',
    )
  })

  it('translates status params and formats VND params', () => {
    expect(
      errorMessage(apiError('order_not_payable', { order_id: 5, status: 'CANCELLED' }), vi),
    ).toBe('Đơn hàng #5 đang ở trạng thái “Đã hủy” nên không thể thanh toán.')
    expect(
      errorMessage(
        apiError('momo_amount_out_of_range', { min_vnd: 1000, max_vnd: 50_000_000 }),
        vi,
      ),
    ).toMatch(/^MoMo chỉ nhận thanh toán từ 1\.000\s₫ đến 50\.000\.000\s₫\./)
  })

  it('falls back to a generic sentence for unknown codes and non-API errors', () => {
    expect(errorMessage(apiError('something_new'), vi)).toBe(vi.errors.generic)
    expect(errorMessage(apiError(undefined), vi)).toBe(vi.errors.generic)
    expect(errorMessage(new Error('boom'), vi)).toBe(vi.errors.generic)
  })

  it('explains network failures (fetch rejects with TypeError)', () => {
    expect(errorMessage(new TypeError('Failed to fetch'), vi)).toBe(vi.errors.network)
  })
})
