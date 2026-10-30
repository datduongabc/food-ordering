import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw/http'
import { describe, expect, it, vi } from 'vitest'
import type { AuditEntry } from '@/features/admin/schemas'
import { admin, page } from '../support/adminFixtures'
import { mockLayout } from '../support/api'
import { renderApp } from '../support/render'
import { server } from '../support/server'

function linkQuery(name: string, index = 0) {
  const href = screen.getAllByRole('link', { name })[index]!.getAttribute('href')!
  const url = new URL(href, 'http://localhost')
  return { path: url.pathname, query: Object.fromEntries(url.searchParams) }
}

describe('admin reports', () => {
  it('builds download links for the last 30 days, with an optional status', async () => {
    vi.useFakeTimers({ now: new Date('2026-10-29T20:00:00Z'), toFake: ['Date'] })
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    renderApp('/admin/reports')

    expect(await screen.findByRole('heading', { name: 'Báo cáo' })).toBeInTheDocument()
    // 20:00 UTC is already the 30th in Vietnam.
    expect(linkQuery('Tải CSV')).toEqual({
      path: '/api/admin/exports/orders.csv',
      query: { from: '2026-10-01', to: '2026-10-30', lang: 'vi' },
    })
    expect(linkQuery('Tải CSV', 1).path).toBe('/api/admin/exports/revenue.csv')

    await user.click(screen.getByRole('button', { name: 'Hoàn thành' }))
    expect(linkQuery('Tải CSV').query.status).toBe('COMPLETED')
    vi.useRealTimers()
  })

  it('refuses a range that ends before it starts', async () => {
    mockLayout({ signedIn: admin })
    renderApp('/admin/reports?from=2026-10-10&to=2026-10-01')

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Ngày kết thúc phải sau ngày bắt đầu',
    )
    expect(screen.queryByRole('link', { name: 'Tải CSV' })).not.toBeInTheDocument()
  })
})

function entry(overrides: Partial<AuditEntry> = {}): AuditEntry {
  return {
    id: 1,
    actor_id: 1,
    actor_name: 'Quản lý Hà',
    action: 'product.update',
    target_type: 'product',
    target_id: 3,
    target_label: 'Phở bò',
    changes: { price: [45_000, 50_000] },
    created_at: '2026-10-29T05:00:00Z',
    ...overrides,
  }
}

describe('admin activity log', () => {
  it('shows who changed what, and filters by kind of record', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    const actions: (string | null)[] = []
    server.use(
      http.get('*/api/admin/audit-log', ({ request }) => {
        actions.push(new URL(request.url).searchParams.get('action'))
        return HttpResponse.json(
          page([
            entry(),
            entry({
              id: 2,
              actor_id: null,
              actor_name: 'Nhân viên cũ',
              action: 'user.update',
              target_type: 'user',
              target_label: 'lan@example.com',
              changes: { role: ['CUSTOMER', 'ADMIN'], password: ['••••••', '••••••'] },
            }),
            entry({
              id: 3,
              action: 'order.status',
              target_label: '#12',
              changes: { status: ['PENDING', 'CONFIRMED'], note: [null, 'Gọi trước'] },
            }),
            entry({ id: 4, action: 'product.hide', changes: {} }),
          ]),
        )
      }),
    )
    renderApp('/admin/audit')

    const rows = await screen.findAllByRole('row')
    const [, price, account, order, hidden] = rows.map((row) => within(row))
    expect(price!.getByText('Sửa món')).toBeInTheDocument()
    expect(price!.getByText('Phở bò')).toBeInTheDocument()
    expect(price!.getByText(/45\.000/)).toBeInTheDocument()
    expect(price!.getByText(/50\.000/)).toBeInTheDocument()
    expect(account!.getByText('(tài khoản đã xóa)')).toBeInTheDocument()
    expect(account!.getByText('Mật khẩu')).toBeInTheDocument()
    expect(order!.getByText('Chờ xác nhận')).toBeInTheDocument()
    expect(order!.getByText('Gọi trước')).toBeInTheDocument()
    expect(hidden!.getByText('Ẩn món')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Người dùng' }))
    await vi.waitFor(() => expect(actions).toEqual([null, 'user']))
  })

  it('says when there is nothing yet', async () => {
    mockLayout({ signedIn: admin })
    server.use(http.get('*/api/admin/audit-log', () => HttpResponse.json(page([]))))
    renderApp('/admin/audit')

    expect(await screen.findByText('Chưa có thao tác nào.')).toBeInTheDocument()
  })
})
