import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw/http'
import { describe, expect, it } from 'vitest'
import { admin, adminDish, adminOrder, adminUser, page } from '../support/adminFixtures'
import { apiError, mockApi, mockLayout, recordCalls } from '../support/api'
import { customer, district1, district7, mains, springRolls, starters } from '../support/fixtures'
import { renderApp } from '../support/render'
import { server } from '../support/server'

describe('admin pages', () => {
  it('turn customers away and hide the admin link from them', async () => {
    mockLayout({ signedIn: customer })
    renderApp('/admin')

    expect(await screen.findByText('Trang dành cho quản trị viên')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Quản trị' })).not.toBeInTheDocument()
  })

  it('show the dashboard figures and reload the charts for another period', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi('get', '/admin/dashboard', {
      completed_revenue: 1_250_000,
      completed_orders: 4,
      average_order_value: 312_500,
      total_orders: 9,
      pending_orders: 3,
      active_products: 31,
      customers: 12,
      total_reservations: 5,
      pending_reservations: 2,
    })
    const requestedDays: string[] = []
    server.use(
      http.get('*/api/admin/stats/revenue', ({ request }) => {
        const days = new URL(request.url).searchParams.get('days')!
        requestedDays.push(days)
        return HttpResponse.json({
          days: [
            { date: '2026-10-28', orders: 2, revenue: 0 },
            { date: '2026-10-29', orders: 3, revenue: 950_000 },
          ],
          total_orders: 5,
          total_revenue: 950_000,
        })
      }),
    )
    mockApi('get', '/admin/stats/top-dishes', {
      by_quantity: [{ product_id: 1, name: springRolls.name, slug: 'x', quantity: 6, revenue: 1 }],
      by_revenue: [],
      least_sold: [],
    })
    mockApi('get', '/admin/stats/payments', {
      cod_orders: 6,
      momo_orders: 3,
      momo: { paid: 2, failed: 1, success_rate: 0.6667 },
    })
    mockApi('get', '/admin/stats/ratings', { lowest_rated: [], latest_reviews: [] })
    renderApp('/admin')

    expect(await screen.findByText('Đơn chờ xác nhận')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Quản trị' })).toHaveAttribute('aria-current', 'page')
    expect(screen.getByText('Từ 4 đơn hoàn thành')).toBeInTheDocument()
    expect(screen.getByText('Trên tổng 9 đơn')).toBeInTheDocument()
    // The chart's values are readable as a table, not only as bar heights.
    const table = await screen.findByRole('table', { name: 'Bảng doanh thu theo ngày' })
    expect(within(table).getAllByRole('row')).toHaveLength(3)
    expect(await screen.findByText('6 phần')).toBeInTheDocument()
    expect(screen.getByText('67%')).toBeInTheDocument()
    expect(screen.getByText('2 thành công · 1 thất bại')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: '30 ngày' }))
    await expect.poll(() => requestedDays).toContain('30')
  })

  it('confirm an order with a note and ask before cancelling one', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi('get', '/admin/orders', page([adminOrder()]))
    const calls = recordCalls([
      'post',
      '/admin/orders/31/status',
      adminOrder({ status: 'CONFIRMED' }),
    ])
    renderApp('/admin/orders')

    const detail = await screen.findByRole('region', { name: 'Đơn hàng #31' })
    expect(within(detail).getByText('a@example.com · 0901234567')).toBeInTheDocument()
    expect(within(detail).getByText('Ghi chú: Gọi trước khi giao')).toBeInTheDocument()
    await user.type(within(detail).getByLabelText(/Ghi chú cho khách/), 'Giao lúc 19:00')
    await user.click(within(detail).getByRole('button', { name: 'Xác nhận đơn' }))

    expect(await screen.findByText('Đơn hàng #31: Đã xác nhận.')).toBeInTheDocument()
    expect(calls[0]!.body).toEqual({ status: 'CONFIRMED', note: 'Giao lúc 19:00' })

    await user.click(within(detail).getByRole('button', { name: 'Hủy đơn' }))
    expect(within(detail).getByRole('alertdialog')).toHaveTextContent('Hủy đơn hàng #31?')
    expect(calls).toHaveLength(1)
  })

  it('check a new dish before saving it and show a taken URL under its field', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi('get', '/admin/products', [adminDish])
    mockApi('get', '/categories', [starters, mains])
    mockApi('get', '/locations', [district1, district7])
    const calls = recordCalls([
      'post',
      '/admin/products',
      apiError('slug_taken', { slug: 'banh-xeo' }),
      409,
    ])
    renderApp('/admin/products/new')

    await user.click(await screen.findByRole('button', { name: 'Lưu thay đổi' }))
    expect(screen.getAllByText('Vui lòng nhập thông tin này.')).toHaveLength(4)
    expect(screen.getByText('Vui lòng chọn danh mục.')).toBeInTheDocument()
    expect(calls).toHaveLength(0)

    await user.type(screen.getByLabelText('Tên tiếng Việt'), 'Bánh xèo')
    await user.type(screen.getByLabelText('Tên tiếng Anh'), 'Sizzling Crepe')
    await user.type(screen.getByLabelText('Mô tả tiếng Việt'), 'Giòn rụm.')
    await user.type(screen.getByLabelText('Mô tả tiếng Anh'), 'Crispy.')
    await user.type(screen.getByLabelText('Giá (VND)'), '95.000')
    await user.selectOptions(screen.getByLabelText('Danh mục'), 'Món chính')
    await user.type(screen.getByLabelText('Đường dẫn (không bắt buộc)'), 'banh-xeo')
    await user.click(screen.getByLabelText('DaTeNO - Quận 7'))
    await user.click(screen.getByRole('button', { name: 'Lưu thay đổi' }))

    expect(
      await screen.findByText('Đường dẫn “banh-xeo” đã được món khác sử dụng.'),
    ).toBeInTheDocument()
    expect(calls[0]!.body).toEqual({
      name: { vi: 'Bánh xèo', en: 'Sizzling Crepe' },
      description: { vi: 'Giòn rụm.', en: 'Crispy.' },
      slug: 'banh-xeo',
      price: 95_000,
      category_id: mains.id,
      location_ids: [district1.id],
    })
  })

  it('hide a dish from the menu', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi('get', '/admin/products', [adminDish])
    const calls = recordCalls([
      'post',
      `/admin/products/${springRolls.id}/hide`,
      { ...adminDish, deleted_at: '2026-10-29T12:00:00Z' },
    ])
    renderApp('/admin/products')

    await user.click(await screen.findByRole('button', { name: 'Ẩn món Gỏi cuốn tôm thịt' }))

    expect(await screen.findByText('Đã ẩn Gỏi cuốn tôm thịt khỏi thực đơn.')).toBeInTheDocument()
    expect(calls).toHaveLength(1)
  })

  it('keep admins from deactivating themselves and confirm before deactivating others', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi(
      'get',
      '/admin/users',
      page([adminUser({ id: admin.id, name: admin.name, role: 'ADMIN' }), adminUser()]),
    )
    const calls = recordCalls(['post', '/admin/users/7/deactivate', adminUser()])
    renderApp('/admin/users')

    const me = (await screen.findByText('Quản lý Hà')).closest('tr')!
    expect(within(me).getByText('(bạn)')).toBeInTheDocument()
    expect(within(me).queryByRole('button', { name: /Vô hiệu hóa/ })).not.toBeInTheDocument()

    const other = screen.getByText('Nguyen Van A').closest('tr')!
    await user.click(within(other).getByRole('button', { name: 'Vô hiệu hóa Nguyen Van A' }))
    expect(within(other).getByRole('alertdialog')).toHaveTextContent(
      'Vô hiệu hóa tài khoản Nguyen Van A?',
    )
    await user.click(within(other).getByRole('button', { name: 'Vô hiệu hóa' }))
    expect(await screen.findByText('Đã vô hiệu hóa Nguyen Van A.')).toBeInTheDocument()
    expect(calls).toHaveLength(1)
  })

  it('show why a role change was refused under the role field', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi(
      'get',
      '/admin/users',
      page([adminUser({ id: admin.id, name: admin.name, role: 'ADMIN' })]),
    )
    const calls = recordCalls([
      'patch',
      `/admin/users/${admin.id}`,
      apiError('cannot_demote_self'),
      400,
    ])
    renderApp('/admin/users')

    await user.click(await screen.findByRole('button', { name: 'Sửa Quản lý Hà' }))
    const form = screen.getByRole('form', { name: 'Sửa người dùng: Quản lý Hà' })
    await user.selectOptions(within(form).getByLabelText('Vai trò'), 'Khách hàng')
    await user.click(within(form).getByRole('button', { name: 'Lưu thay đổi' }))

    expect(
      await within(form).findByText('Quý khách không thể tự gỡ quyền quản trị của mình.'),
    ).toBeInTheDocument()
    // A blank password field leaves the password alone.
    expect(calls[0]!.body).not.toHaveProperty('password')
  })
})
