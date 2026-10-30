import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw/http'
import { beforeEach, describe, expect, it } from 'vitest'
import { apiError, mockApi, mockLayout } from '../support/api'
import { cartOf, customer, review, reviewPage, springRolls } from '../support/fixtures'
import { renderApp } from '../support/render'
import { server } from '../support/server'

const SLUG = springRolls.slug

function mockDish(
  page = reviewPage([]),
  eligibility: { can_review: boolean; reason: string | null } = { can_review: true, reason: null },
) {
  mockApi('get', `/products/${SLUG}`, springRolls)
  mockApi('get', `/products/${SLUG}/reviews`, page)
  mockApi('get', `/products/${SLUG}/reviews/eligibility`, eligibility)
}

describe('dish page', () => {
  it('shows the dish, its branches and an empty review state', async () => {
    mockLayout()
    mockDish()

    renderApp(`/menu/${SLUG}`)

    expect(await screen.findByRole('heading', { level: 1, name: 'Gỏi cuốn tôm thịt' }))
    expect(within(screen.getByRole('main')).getByText('DaTeNO - Quận 1')).toBeInTheDocument()
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

    expect(await screen.findByText('Đã thêm Gỏi cuốn tôm thịt vào giỏ hàng.')).toBeInTheDocument()
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

describe('reviews', () => {
  // An earlier test leaves a guest cart behind, which the header prices again.
  beforeEach(() => mockApi('post', '/cart/preview', cartOf()))

  const reviews = [
    review({
      id: 1,
      rating: 5,
      comment: 'Tuyệt vời',
      user_name: 'Chi',
      photos: [
        { id: 3, url: '/media/reviews/1-a.webp', thumbnail_url: '/media/reviews/thumbs/1-a.webp' },
      ],
      reply: 'Cảm ơn Chi!',
      replied_at: '2026-10-29T05:00:00Z',
    }),
    review({ id: 2, rating: 4, comment: 'Ngon', user_name: 'Dung', verified_purchase: false }),
    review({ id: 3, rating: 1, comment: 'Nguội', user_name: 'Em' }),
  ]

  it('shows the breakdown, badges, photos and the restaurant reply', async () => {
    mockLayout()
    mockDish(reviewPage(reviews))

    renderApp(`/menu/${SLUG}`)

    expect(await screen.findByText('3.3')).toBeInTheDocument()
    expect(screen.getByText('3 đánh giá')).toBeInTheDocument()
    const bars = screen.getByRole('list', { name: 'Phân bố số sao' })
    expect(within(bars).getByRole('button', { name: '5 sao: 1 đánh giá' })).toBeInTheDocument()
    expect(within(bars).getByRole('button', { name: '3 sao: 0 đánh giá' })).toBeInTheDocument()

    const chi = screen.getByText('Tuyệt vời').closest('li')!
    expect(within(chi).getByText('Đã mua')).toBeInTheDocument()
    expect(within(chi).getByRole('img', { name: 'Ảnh món ăn của Chi' })).toHaveAttribute(
      'src',
      '/media/reviews/thumbs/1-a.webp',
    )
    expect(within(chi).getByText('Phản hồi từ nhà hàng')).toBeInTheDocument()
    expect(within(chi).getByText('Cảm ơn Chi!')).toBeInTheDocument()
    const dung = screen.getByText('Ngon').closest('li')!
    expect(within(dung).queryByText('Đã mua')).not.toBeInTheDocument()
  })

  it('filters by stars, sorts and pages through the server', async () => {
    const user = userEvent.setup()
    mockLayout()
    const asked: URLSearchParams[] = []
    mockApi('get', `/products/${SLUG}`, springRolls)
    server.use(
      http.get(`*/api/products/${SLUG}/reviews`, ({ request }) => {
        const params = new URL(request.url).searchParams
        asked.push(params)
        const rating = params.get('rating')
        const items = rating ? reviews.filter((r) => r.rating === Number(rating)) : reviews
        return HttpResponse.json({ ...reviewPage(items, { all: reviews, totalPages: 2 }) })
      }),
    )
    renderApp(`/menu/${SLUG}`)

    await user.click(await screen.findByRole('button', { name: '1★' }))
    await waitFor(() => expect(screen.queryByText('Tuyệt vời')).not.toBeInTheDocument())
    expect(screen.getByText('Nguội')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '1★' })).toHaveAttribute('aria-pressed', 'true')

    await user.selectOptions(screen.getByRole('combobox', { name: 'Sắp xếp' }), 'Sao thấp nhất')
    await user.click(screen.getByRole('button', { name: 'Trang 2' }))

    await waitFor(() => expect(asked.at(-1)?.get('page')).toBe('2'))
    expect(asked.at(-1)?.get('rating')).toBe('1')
    expect(asked.at(-1)?.get('sort')).toBe('lowest')
  })

  it('tells customers without a delivered order why they cannot review yet', async () => {
    mockLayout({ signedIn: customer })
    mockDish(reviewPage([]), { can_review: false, reason: 'not_purchased' })

    renderApp(`/menu/${SLUG}`)

    expect(
      await screen.findByText('Quý khách có thể đánh giá sau khi nhận được đơn hàng có món này.'),
    ).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Gửi đánh giá' })).not.toBeInTheDocument()
  })

  it('thanks customers who already reviewed the dish', async () => {
    mockLayout({ signedIn: customer })
    mockDish(reviewPage([]), { can_review: false, reason: 'already_reviewed' })

    renderApp(`/menu/${SLUG}`)

    expect(
      await screen.findByText('Quý khách đã đánh giá món này. Cảm ơn quý khách đã chia sẻ!'),
    ).toBeInTheDocument()
  })
})

describe('review form', () => {
  it('validates in Vietnamese, then posts the review and its photos', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: customer })
    mockDish()
    let posted: unknown
    const uploads: string[] = []
    server.use(
      http.post(`*/api/products/${SLUG}/reviews`, async ({ request }) => {
        posted = await request.json()
        return HttpResponse.json(review({ id: 41, rating: 4, comment: 'Ngon' }), { status: 201 })
      }),
      http.post('*/api/reviews/41/photos', async ({ request }) => {
        uploads.push(await ((await request.formData()).get('photo') as File).text())
        return HttpResponse.json(review({ id: 41 }), { status: 201 })
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
    const picker = screen.getByLabelText(/Ảnh món ăn/)
    const files = ['a', 'b', 'c', 'd'].map(
      (name) => new File([name], `${name}.jpg`, { type: 'image/jpeg' }),
    )
    await user.upload(picker, files)
    expect(screen.getAllByRole('button', { name: /^Bỏ ảnh/ })).toHaveLength(3)
    await user.click(screen.getByRole('button', { name: 'Bỏ ảnh 2' }))
    await user.click(screen.getByRole('button', { name: 'Gửi đánh giá' }))

    expect(await screen.findByText('Cảm ơn quý khách!')).toBeInTheDocument()
    expect(posted).toEqual({ rating: 4, comment: 'Ngon' })
    expect(uploads).toEqual(['a', 'c'])
  })

  it('keeps the review when a photo is refused', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: customer })
    mockDish()
    mockApi('post', `/products/${SLUG}/reviews`, review({ id: 42 }), 201)
    mockApi('post', '/reviews/42/photos', apiError('image_type_not_allowed'), 400)
    renderApp(`/menu/${SLUG}`)

    await user.type(await screen.findByRole('textbox', { name: 'Nhận xét' }), 'Ngon')
    await user.upload(
      screen.getByLabelText(/Ảnh món ăn/),
      new File(['x'], 'a.jpg', { type: 'image/jpeg' }),
    )
    await user.click(screen.getByRole('button', { name: 'Gửi đánh giá' }))

    expect(
      await screen.findByText('Đánh giá đã được đăng nhưng 1 ảnh chưa tải lên được.'),
    ).toBeInTheDocument()
  })

  it('translates the server refusing a review without a purchase', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: customer })
    mockDish()
    mockApi('post', `/products/${SLUG}/reviews`, apiError('review_needs_purchase'), 403)
    renderApp(`/menu/${SLUG}`)

    await user.type(await screen.findByRole('textbox', { name: 'Nhận xét' }), 'Again')
    await user.click(screen.getByRole('button', { name: 'Gửi đánh giá' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Chỉ khách đã nhận đơn có món này mới có thể đánh giá.',
    )
  })
})
