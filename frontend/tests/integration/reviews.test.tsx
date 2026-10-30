import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { admin } from '../support/adminFixtures'
import { mockApi, mockLayout, recordCalls } from '../support/api'
import { customer, order, review, springRolls } from '../support/fixtures'
import { renderApp } from '../support/render'

describe('review links on orders', () => {
  it('offers a review of each dish once the order is delivered', async () => {
    mockLayout({ signedIn: customer })
    mockApi('get', '/orders', [order({ status: 'COMPLETED', can_cancel: false, can_pay: false })])

    renderApp('/account')

    expect(await screen.findByRole('link', { name: 'Đánh giá Gỏi cuốn tôm thịt' })).toHaveAttribute(
      'href',
      `/menu/${springRolls.slug}#reviews`,
    )
  })

  it('does not before delivery', async () => {
    mockLayout({ signedIn: customer })
    mockApi('get', '/orders', [order()])

    renderApp('/account')

    expect(await screen.findByText('Gỏi cuốn tôm thịt')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /^Đánh giá / })).not.toBeInTheDocument()
  })
})

describe('admin reviews', () => {
  const adminReview = (overrides: Partial<ReturnType<typeof review>> & { hidden_at?: string }) => ({
    ...review(overrides),
    product_name: springRolls.name,
    product_slug: springRolls.slug,
    hidden_at: overrides.hidden_at ?? null,
  })
  const page = (items: unknown[]) => ({
    items,
    page: 1,
    page_size: 20,
    total: items.length,
    total_pages: 1,
  })

  it('hides a review and filters by visibility and stars', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    const rude = adminReview({ id: 7, rating: 1, comment: 'Tệ', user_name: 'Khach X' })
    mockApi('get', '/admin/reviews', page([rude]))
    const calls = recordCalls([
      'post',
      '/admin/reviews/7/hide',
      { ...rude, hidden_at: '2026-10-30T03:00:00Z' },
    ])
    const { router } = renderApp('/admin/reviews')

    const card = (await screen.findByText('Tệ')).closest('li')!
    await user.click(within(card).getByRole('button', { name: 'Ẩn' }))

    await waitFor(() => expect(calls).toHaveLength(1))
    expect(await screen.findByText('Đã ẩn đánh giá của Khach X.')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Đã ẩn' }))
    await user.click(screen.getByRole('button', { name: '1★' }))
    expect(router.state.location.search).toBe('?visibility=hidden&rating=1')
  })

  it('replies to a review and shows hidden ones as such', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    const hidden = adminReview({
      id: 8,
      comment: 'Spam',
      hidden_at: '2026-10-30T03:00:00Z',
      photos: [
        { id: 1, url: '/media/reviews/8-a.webp', thumbnail_url: '/media/reviews/thumbs/8-a.webp' },
      ],
    })
    mockApi('get', '/admin/reviews', page([hidden]))
    const calls = recordCalls([
      'put',
      '/admin/reviews/8/reply',
      { ...hidden, reply: 'Cảm ơn', replied_at: '2026-10-30T03:00:00Z' },
    ])
    renderApp('/admin/reviews')

    const card = (await screen.findByText('Spam')).closest('li')!
    expect(within(card).getByText('Đã ẩn', { selector: 'span' })).toBeInTheDocument()
    expect(within(card).getByRole('button', { name: 'Hiện lại' })).toBeInTheDocument()
    expect(within(card).getByRole('img', { name: /Ảnh món ăn của/ })).toBeInTheDocument()

    await user.click(within(card).getByRole('button', { name: 'Phản hồi' }))
    await user.type(
      within(card).getByRole('textbox', { name: 'Phản hồi công khai của nhà hàng' }),
      'Cảm ơn',
    )
    await user.click(within(card).getByRole('button', { name: 'Lưu thay đổi' }))

    await waitFor(() => expect(calls[0]?.body).toEqual({ reply: 'Cảm ơn' }))
    expect(await screen.findByText('Đã lưu phản hồi.')).toBeInTheDocument()
  })
})
