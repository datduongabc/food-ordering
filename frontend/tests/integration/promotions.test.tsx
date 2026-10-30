import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { admin } from '../support/adminFixtures'
import { apiError, mockApi, mockLayout, recordCalls } from '../support/api'
import { cartOf, customer, order, shakingBeef, springRolls } from '../support/fixtures'
import { renderApp } from '../support/render'

const quote = {
  code: 'GIAM20',
  kind: 'PERCENT',
  value: 20,
  subtotal: 475_000,
  discount: 95_000,
  total: 380_000,
}

describe('promo codes at checkout', () => {
  it('applies a code to the summary and sends it with the order', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: customer })
    mockApi('get', '/cart', cartOf([springRolls, 2]))
    const placed = order({ id: 1051, discount_amount: 95_000, promo_code: 'GIAM20' })
    const calls = recordCalls(
      ['post', '/promo-codes/check', quote],
      ['post', '/orders', placed, 201],
    )
    mockApi('get', '/orders', [placed])
    renderApp('/checkout')

    const field = await screen.findByLabelText('Mã giảm giá')
    await user.type(field, 'giam20{Enter}')

    expect(await screen.findByText('Đã áp dụng mã GIAM20: giảm 95.000 ₫.')).toBeInTheDocument()
    const summary = screen.getByRole('complementary', { name: 'Đơn hàng của quý khách' })
    expect(within(summary).getByText('Giảm giá (GIAM20)')).toBeInTheDocument()
    expect(within(summary).getByText(/380\.000/)).toBeInTheDocument()
    // Enter applied the code; it did not place the order.
    expect(calls.map((call) => call.path)).toEqual(['/promo-codes/check'])

    await user.type(screen.getByLabelText('Địa chỉ giao hàng'), '12 Nguyễn Huệ, Quận 1')
    await user.click(screen.getByRole('button', { name: 'Xác nhận đặt hàng' }))

    await waitFor(() => expect(calls).toHaveLength(2))
    expect(calls[0]?.body).toEqual({ code: 'giam20' })
    expect(calls[1]?.body).toMatchObject({ promo_code: 'GIAM20' })
  })

  it('explains a refused code in the customer’s language and can drop an applied one', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: customer })
    mockApi('get', '/cart', cartOf([springRolls, 2]))
    mockApi(
      'post',
      '/promo-codes/check',
      apiError('promo_min_subtotal', { amount_vnd: 500_000 }),
      400,
    )
    renderApp('/checkout')

    await user.type(await screen.findByLabelText('Mã giảm giá'), 'BIGORDER')
    await user.click(screen.getByRole('button', { name: 'Áp dụng' }))

    expect(await screen.findByText('Mã này áp dụng cho đơn từ 500.000 ₫.')).toBeInTheDocument()

    mockApi('post', '/promo-codes/check', quote)
    await user.clear(screen.getByLabelText('Mã giảm giá'))
    await user.type(screen.getByLabelText('Mã giảm giá'), 'GIAM20')
    await user.click(screen.getByRole('button', { name: 'Áp dụng' }))
    await user.click(await screen.findByRole('button', { name: 'Bỏ mã' }))

    expect(screen.queryByText('Giảm giá (GIAM20)')).not.toBeInTheDocument()
    expect(screen.getByLabelText('Mã giảm giá')).toHaveValue('')
  })
})

describe('past orders', () => {
  it('show what a code took off', async () => {
    mockLayout({ signedIn: customer })
    mockApi('get', '/orders', [
      order({
        subtotal_price: 475_000,
        discount_amount: 95_000,
        promo_code: 'GIAM20',
        total_price: 380_000,
      }),
    ])
    renderApp('/account')

    expect(await screen.findByText('Giảm giá (GIAM20)')).toBeInTheDocument()
    expect(screen.getByText('−95.000 ₫')).toBeInTheDocument()
    expect(screen.getByText('Tạm tính')).toBeInTheDocument()
  })

  it('can be ordered again, saying which dishes are gone', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: customer })
    mockApi('get', '/orders', [order({ status: 'COMPLETED', can_cancel: false, can_pay: false })])
    const calls = recordCalls([
      'post',
      '/orders/1048/reorder',
      {
        cart: cartOf([springRolls, 2]),
        added: 1,
        skipped: [shakingBeef.name],
      },
    ])
    const { router } = renderApp('/account')

    await user.click(await screen.findByRole('button', { name: 'Đặt lại' }))

    await waitFor(() => expect(router.state.location.pathname).toBe('/cart'))
    expect(calls).toHaveLength(1)
    expect(
      await screen.findByText('Đã thêm 1 món vào giỏ hàng. Không còn phục vụ: Bò lúc lắc.'),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Giỏ hàng, 2 món' })).toBeInTheDocument()
  })
})

describe('admin promo codes', () => {
  const promo = {
    id: 3,
    code: 'GIAM20',
    kind: 'PERCENT',
    value: 20,
    max_discount: 100_000,
    min_subtotal: 200_000,
    starts_on: null,
    ends_on: '2026-01-31',
    usage_limit: 50,
    per_customer_limit: 1,
    created_at: '2026-01-01T03:00:00Z',
    disabled_at: null,
    uses: 12,
  }

  it('lists codes with their terms and use', async () => {
    mockLayout({ signedIn: admin })
    mockApi('get', '/admin/promo-codes', [promo])
    renderApp('/admin/promo-codes')

    const row = (await screen.findByText('GIAM20')).closest('tr')!
    expect(within(row).getByText('Giảm 20%, tối đa 100.000 ₫')).toBeInTheDocument()
    expect(within(row).getByText('Đơn từ 200.000 ₫')).toBeInTheDocument()
    expect(within(row).getByText('1 lượt/khách')).toBeInTheDocument()
    expect(within(row).getByText('12 / 50')).toBeInTheDocument()
    expect(within(row).getByText('Hết hạn')).toBeInTheDocument()
  })

  it('creates a fixed-amount code after checking the form', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi('get', '/admin/promo-codes', [])
    const calls = recordCalls([
      'post',
      '/admin/promo-codes',
      { ...promo, id: 4, code: 'TRU50K', kind: 'AMOUNT', value: 50_000 },
      201,
    ])
    renderApp('/admin/promo-codes')

    await user.click(await screen.findByRole('button', { name: '+ Thêm mã' }))
    await user.type(screen.getByLabelText('Mã'), 'tru50k')
    await user.type(screen.getByLabelText('Phần trăm giảm'), '150')
    await user.click(screen.getByRole('button', { name: 'Lưu thay đổi' }))
    expect(await screen.findByText('Phần trăm từ 1 đến 100.')).toBeInTheDocument()

    await user.selectOptions(screen.getByLabelText('Loại giảm giá'), 'AMOUNT')
    const amount = screen.getByLabelText('Số tiền giảm (VND)')
    await user.clear(amount)
    await user.type(amount, '50000')
    await user.type(screen.getByLabelText('Đến hết ngày'), '2026-12-31')
    await user.click(screen.getByRole('button', { name: 'Lưu thay đổi' }))

    expect(await screen.findByText('Đã tạo mã TRU50K.')).toBeInTheDocument()
    expect(calls[0]?.body).toEqual({
      code: 'TRU50K',
      kind: 'AMOUNT',
      value: 50_000,
      max_discount: null,
      min_subtotal: 0,
      starts_on: null,
      ends_on: '2026-12-31',
      usage_limit: null,
      per_customer_limit: 1,
    })
  })

  it('shows a taken code on the code field', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi('get', '/admin/promo-codes', [promo])
    mockApi('put', '/admin/promo-codes/3', apiError('promo_code_taken', { code: 'OLD' }), 409)
    renderApp('/admin/promo-codes')

    await user.click(await screen.findByRole('button', { name: 'Sửa GIAM20' }))
    const code = screen.getByLabelText('Mã')
    await user.clear(code)
    await user.type(code, 'OLD')
    await user.click(screen.getByRole('button', { name: 'Lưu thay đổi' }))

    expect(await screen.findByText('Mã “OLD” đã tồn tại.')).toBeInTheDocument()
  })
})
