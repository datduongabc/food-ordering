import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw/http'
import { describe, expect, it } from 'vitest'
import { apiError, mockApi, mockLayout } from '../support/api'
import { cartOf, customer, springRolls } from '../support/fixtures'
import { renderApp } from '../support/render'
import { server } from '../support/server'

const SLUG = springRolls.slug

function mockDish(reviews: unknown[] = []) {
  mockApi('get', `/products/${SLUG}`, springRolls)
  mockApi('get', `/products/${SLUG}/reviews`, reviews)
}

describe('dish page', () => {
  it('shows the dish, its branches and an empty review state', async () => {
    mockLayout()
    mockDish()

    renderApp(`/menu/${SLUG}`)

    expect(await screen.findByRole('heading', { level: 1, name: 'Shrimp Spring Rolls' }))
    expect(within(screen.getByRole('main')).getByText('DaTeNO - District 1')).toBeInTheDocument()
    expect(
      await screen.findByText('Món này chưa có đánh giá. Hãy là người đầu tiên chia sẻ cảm nhận.'),
    ).toBeInTheDocument()
    expect(
      within(screen.getByRole('complementary')).getByRole('link', { name: 'Đăng nhập' }),
    ).toHaveAttribute('href', `/login?next=${encodeURIComponent(`/menu/${SLUG}#reviews`)}`)
  })

  it('says so when the dish does not exist', async () => {
    mockLayout()
    mockApi('get', '/products/gone', apiError('dish_not_found'), 404)

    renderApp('/menu/gone')

    expect(await screen.findByText('Không tìm thấy món ăn')).toBeInTheDocument()
  })

  it('adds the chosen quantity to a guest cart and updates the header', async () => {
    const user = userEvent.setup()
    mockLayout()
    mockDish()
    server.use(
      http.post('*/api/cart/preview', async ({ request }) => {
        const body = (await request.json()) as { items: { quantity: number }[] }
        return HttpResponse.json(cartOf([springRolls, body.items[0]?.quantity ?? 0]))
      }),
    )
    renderApp(`/menu/${SLUG}`)

    await user.click(await screen.findByRole('button', { name: 'Tăng số lượng' }))
    await user.click(screen.getByRole('button', { name: /^Thêm vào giỏ · 475\.000\s₫$/ }))

    expect(await screen.findByText('Đã thêm Shrimp Spring Rolls vào giỏ hàng.')).toBeInTheDocument()
    expect(JSON.parse(window.localStorage.getItem('dateno_guest_cart')!)).toEqual([
      { product_id: springRolls.id, quantity: 2 },
    ])
    await waitFor(() =>
      expect(screen.getByRole('link', { name: 'Giỏ hàng, 2 món' })).toBeInTheDocument(),
    )
  })

  it('adds to the account cart for signed-in customers', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: customer })
    mockDish()
    let posted: unknown
    server.use(
      http.post('*/api/cart/items', async ({ request }) => {
        posted = await request.json()
        return HttpResponse.json(cartOf([springRolls, 1]))
      }),
    )
    renderApp(`/menu/${SLUG}`)

    await user.click(await screen.findByRole('button', { name: /^Thêm vào giỏ/ }))

    await waitFor(() => expect(posted).toEqual({ product_id: springRolls.id, quantity: 1 }))
    expect(await screen.findByRole('link', { name: 'Giỏ hàng, 1 món' })).toBeInTheDocument()
    expect(window.localStorage.getItem('dateno_guest_cart')).toBeNull()
  })
})

describe('review form', () => {
  it('validates in Vietnamese, then posts the review', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: customer })
    mockDish()
    let posted: unknown
    server.use(
      http.post(`*/api/products/${SLUG}/reviews`, async ({ request }) => {
        posted = await request.json()
        return HttpResponse.json(
          { id: 1, rating: 4, comment: 'Ngon', created_at: '2026-10-29T03:00:00Z', user_name: 'A' },
          { status: 201 },
        )
      }),
    )
    renderApp(`/menu/${SLUG}`)

    await user.click(await screen.findByRole('button', { name: 'Gửi đánh giá' }))
    expect(await screen.findByText('Vui lòng nhập nhận xét.')).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Nhận xét' })).toHaveAttribute(
      'aria-invalid',
      'true',
    )

    await user.click(screen.getByRole('button', { name: '4 sao' }))
    await user.type(screen.getByRole('textbox', { name: 'Nhận xét' }), '  Ngon  ')
    await user.click(screen.getByRole('button', { name: 'Gửi đánh giá' }))

    expect(await screen.findByText('Cảm ơn quý khách!')).toBeInTheDocument()
    expect(posted).toEqual({ rating: 4, comment: 'Ngon' })
  })

  it('translates the server refusing a second review', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: customer })
    mockDish()
    mockApi('post', `/products/${SLUG}/reviews`, apiError('already_reviewed'), 409)
    renderApp(`/menu/${SLUG}`)

    await user.type(await screen.findByRole('textbox', { name: 'Nhận xét' }), 'Again')
    await user.click(screen.getByRole('button', { name: 'Gửi đánh giá' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Quý khách đã đánh giá món này.')
  })
})
