import { fireEvent, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw/http'
import { describe, expect, it } from 'vitest'
import { admin, adminOrder, adminReservation, page } from '../support/adminFixtures'
import { apiError, mockApi, mockLayout, recordCalls } from '../support/api'
import { springRolls } from '../support/fixtures'
import { renderApp } from '../support/render'
import { server } from '../support/server'

/** Answers `path` with `body` and remembers each request's query string. */
function recordQueries(path: string, body: unknown) {
  const queries: URLSearchParams[] = []
  server.use(
    http.get(`*/api${path}`, ({ request }) => {
      queries.push(new URL(request.url).searchParams)
      return HttpResponse.json(body as never)
    }),
  )
  return queries
}

const staffConfirmed = {
  from_status: 'PENDING' as const,
  to_status: 'CONFIRMED' as const,
  actor: 'staff' as const,
  actor_name: 'Quản lý Hà',
  note: 'Giao lúc 19:00',
  created_at: '2026-10-29T12:00:00Z',
}

describe('admin orders', () => {
  it('filter by status, page through and pick an order from the list', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    const queries = recordQueries(
      '/admin/orders',
      page([adminOrder(), adminOrder({ id: 32, payment_method: 'MOMO' })], {
        total: 25,
        total_pages: 2,
      }),
    )
    renderApp('/admin/orders')

    expect(await screen.findByRole('region', { name: 'Đơn hàng #31' })).toBeInTheDocument()
    expect(screen.getByText('25 kết quả')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /^#32(?!\d)/ }))
    expect(await screen.findByRole('region', { name: 'Đơn hàng #32' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Chờ xác nhận' }))
    await expect.poll(() => queries.at(-1)?.get('status')).toBe('PENDING')

    await user.click(screen.getByRole('button', { name: 'Trang 2' }))
    await expect.poll(() => queries.at(-1)?.get('page')).toBe('2')
    expect(queries.at(-1)?.get('status')).toBe('PENDING')
  })

  it('say when no order has the chosen status', async () => {
    mockLayout({ signedIn: admin })
    mockApi('get', '/admin/orders', page([]))
    renderApp('/admin/orders?status=CANCELLED')

    expect(await screen.findByText('Chưa có đơn hàng nào ở trạng thái này.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Đã hủy' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('name who moved an order and show its MoMo payment', async () => {
    mockLayout({ signedIn: admin })
    const confirmed = adminOrder({
      status: 'CONFIRMED',
      payment_method: 'MOMO',
      payment_status: 'PAID',
      momo_order_id: 'DATENO_31_ab12',
      momo_trans_id: null,
      events: [
        { ...adminOrder().events[0]!, actor_name: null },
        { ...staffConfirmed, actor: 'system', actor_name: null, note: '' },
        { ...staffConfirmed, from_status: 'CONFIRMED', to_status: 'CONFIRMED' },
      ],
    })
    mockApi('get', '/admin/orders', page([confirmed]))
    renderApp('/admin/orders')

    const detail = await screen.findByRole('region', { name: 'Đơn hàng #31' })
    expect(within(detail).getByText('Chờ xác nhận · Khách hàng')).toBeInTheDocument()
    expect(within(detail).getByText('Đã xác nhận · Hệ thống')).toBeInTheDocument()
    expect(within(detail).getByText('Đã xác nhận · Quản lý Hà')).toBeInTheDocument()
    expect(within(detail).getByText('Giao lúc 19:00')).toBeInTheDocument()
    expect(
      within(detail).getByText('Mã MoMo: DATENO_31_ab12 · giao dịch chưa có'),
    ).toBeInTheDocument()
  })

  it('deliver a confirmed order', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi('get', '/admin/orders', page([adminOrder({ status: 'CONFIRMED' })]))
    const calls = recordCalls([
      'post',
      '/admin/orders/31/status',
      adminOrder({ status: 'COMPLETED', payment_status: 'PAID' }),
    ])
    renderApp('/admin/orders')

    const detail = await screen.findByRole('region', { name: 'Đơn hàng #31' })
    expect(within(detail).queryByRole('button', { name: 'Xác nhận đơn' })).not.toBeInTheDocument()
    await user.click(within(detail).getByRole('button', { name: 'Đã giao xong' }))

    expect(await screen.findByText('Đơn hàng #31: Hoàn thành.')).toBeInTheDocument()
    expect(calls[0]!.body).toEqual({ status: 'COMPLETED', note: '' })
  })

  it('warn about the refund before cancelling a paid MoMo order, and allow backing out', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi(
      'get',
      '/admin/orders',
      page([adminOrder({ status: 'CONFIRMED', payment_method: 'MOMO', payment_status: 'PAID' })]),
    )
    const calls = recordCalls([
      'post',
      '/admin/orders/31/status',
      adminOrder({ status: 'CANCELLED', payment_status: 'REFUNDED' }),
    ])
    renderApp('/admin/orders')

    const detail = await screen.findByRole('region', { name: 'Đơn hàng #31' })
    await user.click(within(detail).getByRole('button', { name: 'Hủy đơn' }))
    const dialog = within(detail).getByRole('alertdialog')
    expect(dialog).toHaveTextContent('Số tiền đã thanh toán sẽ được hoàn lại.')
    expect(dialog).toHaveTextContent('cần hoàn lại qua cổng MoMo')

    await user.click(within(dialog).getByRole('button', { name: 'Giữ đơn hàng' }))
    expect(within(detail).queryByRole('alertdialog')).not.toBeInTheDocument()

    await user.click(within(detail).getByRole('button', { name: 'Hủy đơn' }))
    await user.click(
      within(within(detail).getByRole('alertdialog')).getByRole('button', { name: 'Hủy đơn' }),
    )
    expect(await screen.findByText('Đơn hàng #31: Đã hủy.')).toBeInTheDocument()
    expect(calls[0]!.body).toEqual({ status: 'CANCELLED', note: '' })
  })

  it('explain a refused change and lock finished orders', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi(
      'get',
      '/admin/orders',
      page([adminOrder(), adminOrder({ id: 40, status: 'COMPLETED' })]),
    )
    recordCalls([
      'post',
      '/admin/orders/31/status',
      apiError('invalid_status_transition', { from: 'CANCELLED', to: 'CONFIRMED' }),
      409,
    ])
    renderApp('/admin/orders')

    const detail = await screen.findByRole('region', { name: 'Đơn hàng #31' })
    await user.click(within(detail).getByRole('button', { name: 'Xác nhận đơn' }))
    expect(
      await screen.findByText('Không thể chuyển trạng thái từ “Đã hủy” sang “Đã xác nhận”.'),
    ).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /^#40(?!\d)/ }))
    const finished = await screen.findByRole('region', { name: 'Đơn hàng #40' })
    expect(
      within(finished).getByText('Đơn hàng đã kết thúc, không thể đổi trạng thái.'),
    ).toBeInTheDocument()
    expect(within(finished).queryByRole('textbox')).not.toBeInTheDocument()
  })
})

describe('admin bookings', () => {
  it('list bookings and filter them by status and date', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    const queries = recordQueries(
      '/admin/reservations',
      page([adminReservation({ special_requests: 'Ghế trẻ em' })], { total: 30, total_pages: 2 }),
    )
    renderApp('/admin/reservations')

    const row = (await screen.findByText('Nguyen Van A')).closest('tr')!
    expect(within(row).getByText('19:00')).toBeInTheDocument()
    expect(within(row).getByText(/4 khách/)).toBeInTheDocument()
    expect(within(row).getByText('Yêu cầu: Ghế trẻ em')).toBeInTheDocument()
    expect(within(row).getByText('Chờ xác nhận')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Đã xác nhận' }))
    await expect.poll(() => queries.at(-1)?.get('status')).toBe('CONFIRMED')

    fireEvent.change(screen.getByLabelText('Ngày đến'), { target: { value: '2026-10-31' } })
    await expect.poll(() => queries.at(-1)?.get('date')).toBe('2026-10-31')

    await user.click(screen.getByRole('button', { name: 'Trang 2' }))
    await expect.poll(() => queries.at(-1)?.get('page')).toBe('2')

    await user.click(screen.getByRole('button', { name: 'Mọi ngày' }))
    expect(screen.getByLabelText('Ngày đến')).toHaveValue('')
    expect(screen.queryByRole('button', { name: 'Mọi ngày' })).not.toBeInTheDocument()
  })

  it('ignore a malformed date in the URL', async () => {
    mockLayout({ signedIn: admin })
    const queries = recordQueries('/admin/reservations', page([]))
    renderApp('/admin/reservations?date=tomorrow&status=NOPE')

    expect(await screen.findByText('Không có lượt đặt bàn nào phù hợp.')).toBeInTheDocument()
    expect(queries[0]!.has('date')).toBe(false)
    expect(queries[0]!.has('status')).toBe(false)
    expect(screen.getByRole('button', { name: 'Tất cả' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('offer only the next steps for each booking and record them', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi(
      'get',
      '/admin/reservations',
      page([
        adminReservation({ id: 1 }),
        adminReservation({ id: 2, customer_name: 'Tran Thi B', status: 'CONFIRMED' }),
        adminReservation({ id: 3, customer_name: 'Le Van C', status: 'COMPLETED' }),
      ]),
    )
    const calls = recordCalls(
      ['post', '/admin/reservations/1/status', adminReservation({ status: 'CONFIRMED' })],
      ['post', '/admin/reservations/2/status', apiError('reservation_not_found'), 404],
    )
    renderApp('/admin/reservations')

    const pending = (await screen.findByText('Nguyen Van A')).closest('tr')!
    const confirmed = screen.getByText('Tran Thi B').closest('tr')!
    const done = screen.getByText('Le Van C').closest('tr')!
    expect(within(done).queryByRole('button')).not.toBeInTheDocument()
    expect(within(confirmed).getByRole('button', { name: 'Khách đã đến' })).toBeInTheDocument()

    await user.click(within(pending).getByRole('button', { name: 'Xác nhận' }))
    expect(await screen.findByText('Đặt bàn #1: Đã xác nhận.')).toBeInTheDocument()
    expect(calls[0]!.body).toEqual({ status: 'CONFIRMED' })

    await user.click(within(confirmed).getByRole('button', { name: 'Hủy' }))
    expect(await screen.findByText('Không tìm thấy lịch đặt bàn.')).toBeInTheDocument()
  })
})

describe('admin overview', () => {
  function mockStats({ days = 7, reviews = true } = {}) {
    mockApi('get', '/admin/dashboard', {
      completed_revenue: 0,
      completed_orders: 0,
      average_order_value: 0,
      total_orders: 0,
      pending_orders: 0,
      active_products: 30,
      customers: 0,
      total_reservations: 0,
      pending_reservations: 0,
    })
    mockApi('get', '/admin/stats/revenue', {
      days: Array.from({ length: days }, (_, index) => ({
        date: `2026-10-${String(index + 1).padStart(2, '0')}`,
        orders: index === days - 1 ? 3 : 0,
        revenue: index === days - 1 ? 950_000 : 0,
      })),
      total_orders: 3,
      total_revenue: 950_000,
    })
    mockApi('get', '/admin/stats/top-dishes', { by_quantity: [], by_revenue: [], least_sold: [] })
    mockApi('get', '/admin/stats/payments', {
      cod_orders: 0,
      momo_orders: 0,
      momo: { paid: 0, failed: 0, success_rate: null },
    })
    mockApi(
      'get',
      '/admin/stats/ratings',
      reviews
        ? {
            lowest_rated: [
              {
                product_id: springRolls.id,
                name: springRolls.name,
                slug: springRolls.slug,
                average_rating: '2.50',
                review_count: 4,
              },
            ],
            latest_reviews: [
              {
                id: 9,
                rating: 2,
                comment: 'Hơi nguội.',
                created_at: '2026-10-29T10:00:00Z',
                user_name: 'Tran Thi B',
                product_name: springRolls.name,
                product_slug: springRolls.slug,
              },
            ],
          }
        : { lowest_rated: [], latest_reviews: [] },
    )
  }

  it('show a day in the tooltip when pointing at its column', async () => {
    mockLayout({ signedIn: admin })
    mockStats()
    renderApp('/admin')

    await screen.findByRole('table', { name: 'Bảng doanh thu theo ngày' })
    expect(screen.getByText('Chưa có giao dịch')).toBeInTheDocument()
    const columns = document.querySelectorAll('[data-active]')
    expect(columns).toHaveLength(7)

    fireEvent.mouseEnter(columns[6]!)
    expect(screen.getByText('3 đơn đã đặt')).toBeInTheDocument()
    fireEvent.mouseLeave(columns[6]!.parentElement!.parentElement!)
    expect(screen.queryByText('3 đơn đã đặt')).not.toBeInTheDocument()
  })

  it('label only some days over a month and list the lowest-rated dishes', async () => {
    mockLayout({ signedIn: admin })
    mockStats({ days: 30 })
    renderApp('/admin?days=30')

    await screen.findByRole('table', { name: 'Bảng doanh thu theo ngày' })
    expect(screen.getByRole('button', { name: '30 ngày' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByText('Món bị chấm thấp nhất')).toBeInTheDocument()
    expect(screen.getByText('4 đánh giá')).toBeInTheDocument()
    expect(screen.getByText('Tran Thi B về Gỏi cuốn tôm thịt')).toBeInTheDocument()
    expect(screen.getByText('Hơi nguội.')).toBeInTheDocument()
  })

  it('say when there are no reviews and show a failed summary with a retry', async () => {
    mockLayout({ signedIn: admin })
    mockStats({ reviews: false })
    mockApi('get', '/admin/dashboard', apiError('admin_required'), 403)
    renderApp('/admin')

    expect(await screen.findByText('Chưa có đánh giá nào.')).toBeInTheDocument()
    expect(
      await screen.findByText('Chỉ quản trị viên mới có quyền thực hiện thao tác này.'),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Thử lại' })).toBeInTheDocument()
  })
})
