import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw/http'
import { describe, expect, it } from 'vitest'
import { guestCart } from '@/features/cart/guestCart'
import { apiError, mockApi, mockLayout, recordCalls } from '../support/api'
import {
  cartOf,
  customer,
  district1,
  district7,
  order,
  shakingBeef,
  springRolls,
} from '../support/fixtures'
import { renderApp } from '../support/render'
import { server } from '../support/server'

const VND = (text: string) => new RegExp(`^${text.replace('.', '\\.')}\\s₫$`)

describe('cart page', () => {
  it('prices a guest cart, changes quantities and removes dishes', async () => {
    const user = userEvent.setup()
    mockLayout()
    guestCart.add(springRolls.id, 1)
    guestCart.add(shakingBeef.id, 1)
    server.use(
      http.post('*/api/cart/preview', async ({ request }) => {
        const body = (await request.json()) as { items: { product_id: number; quantity: number }[] }
        const dishes = [springRolls, shakingBeef]
        return HttpResponse.json(
          cartOf(
            ...body.items.map(
              (line) =>
                [dishes.find((dish) => dish.id === line.product_id)!, line.quantity] as [
                  typeof springRolls,
                  number,
                ],
            ),
          ),
        )
      }),
    )
    renderApp('/cart')

    expect(await screen.findByText('2 món trong giỏ')).toBeInTheDocument()
    const summary = screen.getByRole('complementary', { name: 'Tóm tắt đơn hàng' })
    expect(within(summary).getAllByText(VND('687.500'))).toHaveLength(2)
    expect(screen.getByText(/giỏ hàng được lưu trên trình duyệt này/)).toBeInTheDocument()

    await user.click(
      within(screen.getByRole('group', { name: 'Số lượng Gỏi cuốn tôm thịt' })).getByRole(
        'button',
        { name: 'Tăng số lượng' },
      ),
    )
    expect(await screen.findByText('3 món trong giỏ')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Xóa Bò lúc lắc khỏi giỏ hàng' }))
    expect(await screen.findByText('2 món trong giỏ')).toBeInTheDocument()
    expect(screen.queryByText('Bò lúc lắc')).not.toBeInTheDocument()
    expect(guestCart.lines()).toEqual([{ product_id: springRolls.id, quantity: 2 }])
    guestCart.clear()
  })

  it('points an empty cart at the menu', async () => {
    mockLayout({ signedIn: customer })
    renderApp('/cart')
    expect(await screen.findByText('Giỏ hàng đang trống')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Xem thực đơn' })).toHaveAttribute('href', '/menu')
  })
})

describe('checkout', () => {
  it('sends visitors to sign in first', async () => {
    mockLayout()
    const { router } = renderApp('/checkout')
    await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
    expect(router.state.location.search).toBe('?next=%2Fcheckout')
    expect(await screen.findByRole('heading', { name: 'Đăng nhập' })).toBeInTheDocument()
  })

  it('places a cash order with the prefilled details and opens it', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: customer })
    mockApi('get', '/cart', cartOf([springRolls, 2]))
    const placed = order({ id: 1050 })
    const calls = recordCalls(['post', '/orders', placed, 201])
    mockApi('get', '/orders', [placed])
    const { router } = renderApp('/checkout')

    expect(await screen.findByLabelText('Người nhận')).toHaveValue(customer.name)
    await user.click(screen.getByRole('button', { name: 'Xác nhận đặt hàng' }))
    expect(await screen.findByText('Địa chỉ cần ít nhất 5 ký tự.')).toBeInTheDocument()
    expect(calls).toHaveLength(0)

    await user.type(screen.getByLabelText('Địa chỉ giao hàng'), '12 Nguyễn Huệ, Quận 1')
    await user.type(screen.getByLabelText('Ghi chú (không bắt buộc)'), 'Ít cay')
    await user.click(screen.getByRole('button', { name: 'Xác nhận đặt hàng' }))

    expect(await screen.findByText('Đã đặt đơn hàng #1050.')).toBeInTheDocument()
    expect(calls[0]?.body).toEqual({
      delivery_name: customer.name,
      delivery_phone: customer.phone,
      delivery_address: '12 Nguyễn Huệ, Quận 1',
      delivery_note: 'Ít cay',
      location_id: district1.id,
      payment_method: 'COD',
    })
    expect(await screen.findByRole('heading', { name: 'Đơn hàng #1050' })).toBeInTheDocument()
    expect(router.state.location.search).toBe('?order=1050')
    expect(screen.getByRole('link', { name: 'Giỏ hàng, 0 món' })).toBeInTheDocument()
  })

  it('warns about dishes a branch does not serve and starts on one that does', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: customer })
    mockApi('get', '/locations', [district1, district7])
    const everywhere = { ...springRolls, locations: [district1, district7] }
    mockApi(
      'get',
      '/cart',
      cartOf([everywhere, 1], [{ ...shakingBeef, locations: [district7] }, 1]),
    )
    renderApp('/checkout')

    expect(await screen.findByRole('radio', { name: /DaTeNO - Quận 7/ })).toBeChecked()
    await user.click(screen.getByRole('radio', { name: /DaTeNO - Quận 1/ }))

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Bò lúc lắc hiện không phục vụ tại DaTeNO - Quận 1.',
    )
    expect(screen.getByRole('button', { name: 'Xác nhận đặt hàng' })).toBeDisabled()
  })

  it('goes to the MoMo page for online payment', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: customer })
    mockApi('get', '/cart', cartOf([springRolls, 1]))
    mockApi('post', '/orders', order({ id: 7, payment_method: 'MOMO' }), 201)
    mockApi('post', '/orders/7/payments/momo', {
      order_id: 7,
      momo_order_id: 'DATENO_7_a',
      amount: 237_500,
      mode: 'sandbox',
    })
    const { router } = renderApp('/checkout')

    await user.type(await screen.findByLabelText('Địa chỉ giao hàng'), '12 Nguyễn Huệ')
    await user.click(screen.getByRole('radio', { name: /Ví MoMo/ }))
    await user.click(screen.getByRole('button', { name: 'Đặt hàng và thanh toán MoMo' }))

    await waitFor(() => expect(router.state.location.pathname).toBe('/orders/7/pay'))
    expect(await screen.findByText(VND('237.500'))).toBeInTheDocument()
  })
})

describe('MoMo sandbox payment', () => {
  function mockAttempts() {
    let attempt = 0
    server.use(
      http.post('*/api/orders/7/payments/momo', () =>
        HttpResponse.json({
          order_id: 7,
          momo_order_id: `DATENO_7_${++attempt}`,
          amount: 475_000,
          mode: 'sandbox',
        }),
      ),
    )
  }

  it('lets a declined payment be retried with a fresh attempt', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: customer })
    mockAttempts()
    const calls = recordCalls([
      'post',
      '/payments/momo/sandbox/complete',
      order({ id: 7, payment_method: 'MOMO', payment_status: 'FAILED' }),
    ])
    renderApp('/orders/7/pay')

    expect(await screen.findByText('Thanh toán đơn hàng DaTeNO #7')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Từ chối giao dịch' }))
    expect(await screen.findByRole('heading', { name: 'Thanh toán chưa thành công' }))

    server.use(
      http.post('*/api/payments/momo/sandbox/complete', async ({ request }) => {
        calls.push({ path: 'complete', body: await request.json() })
        return HttpResponse.json(
          order({ id: 7, payment_method: 'MOMO', payment_status: 'PAID', status: 'CONFIRMED' }),
        )
      }),
    )
    await user.click(screen.getByRole('button', { name: 'Thử lại' }))
    await user.click(await screen.findByRole('button', { name: 'Xác nhận thanh toán' }))

    expect(await screen.findByRole('heading', { name: 'Đơn hàng #7 đã được thanh toán' }))
    expect(calls.map((call) => call.body)).toEqual([
      { momo_order_id: 'DATENO_7_1', result: 'declined' },
      { momo_order_id: 'DATENO_7_2', result: 'approved' },
    ])
    expect(screen.getByRole('link', { name: 'Xem đơn hàng' })).toHaveAttribute(
      'href',
      '/account?order=7',
    )
  })

  it('explains why an order cannot be paid', async () => {
    mockLayout({ signedIn: customer })
    mockApi('post', '/orders/7/payments/momo', apiError('order_already_paid', { order_id: 7 }), 409)
    renderApp('/orders/7/pay')
    expect(await screen.findByText('Đơn hàng #7 đã được thanh toán.')).toBeInTheDocument()
  })
})

describe('account orders', () => {
  it('shows the chosen order with a timeline in the customer’s words', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: customer })
    mockApi('get', '/orders', [
      order({
        id: 2,
        status: 'CONFIRMED',
        payment_method: 'MOMO',
        payment_status: 'PAID',
        can_cancel: false,
        can_pay: false,
        events: [
          {
            from_status: null,
            to_status: 'PENDING',
            actor: 'customer',
            note: '',
            created_at: '2026-10-29T11:00:00Z',
          },
          {
            from_status: 'PENDING',
            to_status: 'CONFIRMED',
            actor: 'system',
            note: '',
            created_at: '2026-10-29T11:05:00Z',
          },
        ],
      }),
      order({
        id: 1,
        status: 'CANCELLED',
        can_cancel: false,
        can_pay: false,
        events: [
          {
            from_status: null,
            to_status: 'PENDING',
            actor: 'customer',
            note: '',
            created_at: '2026-10-28T11:00:00Z',
          },
          {
            from_status: 'PENDING',
            to_status: 'CANCELLED',
            actor: 'staff',
            note: 'Hết tôm',
            created_at: '2026-10-28T11:10:00Z',
          },
        ],
      }),
    ])
    renderApp('/account')

    const first = await screen.findByRole('region', { name: 'Đơn hàng #2' })
    expect(
      within(first).getByText('Đã nhận thanh toán MoMo, đơn hàng được xác nhận'),
    ).toBeInTheDocument()
    expect(within(first).getByText('Đã thanh toán')).toBeInTheDocument()
    expect(within(first).getByText(/không thể hủy trực tuyến/)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /^#1/ }))
    const second = await screen.findByRole('region', { name: 'Đơn hàng #1' })
    expect(within(second).getByText('Nhà hàng đã hủy đơn')).toBeInTheDocument()
    expect(within(second).getByText('Nhà hàng ghi chú: Hết tôm')).toBeInTheDocument()
  })

  it('cancels a pending order after confirmation', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: customer })
    mockApi('get', '/orders', [order({ id: 5 })])
    mockApi(
      'post',
      '/orders/5/cancel',
      order({
        id: 5,
        status: 'CANCELLED',
        can_cancel: false,
        can_pay: false,
        events: [
          ...order().events,
          {
            from_status: 'PENDING',
            to_status: 'CANCELLED',
            actor: 'customer',
            note: '',
            created_at: '2026-10-29T12:00:00Z',
          },
        ],
      }),
    )
    renderApp('/account')

    const detail = await screen.findByRole('region', { name: 'Đơn hàng #5' })
    await user.click(within(detail).getByRole('button', { name: 'Hủy đơn hàng' }))
    expect(within(detail).getByRole('alertdialog')).toHaveTextContent(
      'Hủy đơn hàng #5? Thao tác này không thể hoàn tác.',
    )
    await user.click(within(detail).getByRole('button', { name: /^Hủy đơn$/ }))

    expect(await screen.findByText('Đã hủy đơn hàng #5.')).toBeInTheDocument()
    expect(within(detail).getByText('Quý khách đã hủy đơn')).toBeInTheDocument()
    expect(within(detail).queryByRole('button', { name: 'Hủy đơn hàng' })).not.toBeInTheDocument()
  })

  it('says when there are no orders yet', async () => {
    mockLayout({ signedIn: customer })
    mockApi('get', '/orders', [])
    renderApp('/account')
    expect(await screen.findByText('Quý khách chưa có đơn hàng nào')).toBeInTheDocument()
  })
})
