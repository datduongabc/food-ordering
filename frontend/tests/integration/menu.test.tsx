import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw/http'
import { describe, expect, it } from 'vitest'
import { mockLayout } from '../support/api'
import { product, shakingBeef, springRolls } from '../support/fixtures'
import { renderApp } from '../support/render'
import { server } from '../support/server'

function page(items = [springRolls, shakingBeef], extra = {}) {
  return { items, page: 1, page_size: 12, total: items.length, total_pages: 1, ...extra }
}

/** Records the query string of every product list request. */
function mockProductList(respond = (_params: URLSearchParams) => page()) {
  const requests: URLSearchParams[] = []
  server.use(
    http.get('*/api/products', ({ request }) => {
      const params = new URL(request.url).searchParams
      requests.push(params)
      return HttpResponse.json(respond(params))
    }),
  )
  return requests
}

describe('menu page', () => {
  it('lists dishes with VND prices and Vietnamese labels', async () => {
    mockLayout()
    mockProductList()

    renderApp('/menu')

    const card = (await screen.findByRole('heading', { name: 'Shrimp Spring Rolls' })).closest(
      'article',
    )!
    expect(within(card).getByText(/^237\.500\s₫$/)).toBeInTheDocument()
    expect(within(card).getByText('Khai vị')).toBeInTheDocument()
    expect(within(card).getByRole('img', { name: 'Chưa có đánh giá' })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Đánh giá 4.5 trên 5' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 1, name: 'Thực đơn' })).toBeInTheDocument()
  })

  it('filters by category and sort through the URL', async () => {
    const user = userEvent.setup()
    mockLayout()
    const requests = mockProductList()
    const { router } = renderApp('/menu')

    await user.click(await screen.findByRole('button', { name: 'Món chính' }))
    await user.selectOptions(screen.getByRole('combobox', { name: 'Sắp xếp' }), 'price_desc')

    expect(router.state.location.search).toBe('?category=main_dishes&sort=price_desc')
    const last = requests.at(-1)!
    expect(last.get('category')).toBe('main_dishes')
    expect(last.get('sort')).toBe('price_desc')
    expect(screen.getByRole('button', { name: 'Món chính' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
  })

  it('pages through the menu', async () => {
    const user = userEvent.setup()
    mockLayout()
    const requests = mockProductList((params) =>
      page([product({ name: `Page ${params.get('page') ?? '1'} dish` })], {
        page: Number(params.get('page') ?? '1'),
        total_pages: 3,
      }),
    )
    renderApp('/menu')

    await screen.findByText('Page 1 dish')
    expect(screen.getByRole('button', { name: 'Trang trước' })).toBeDisabled()
    await user.click(screen.getByRole('button', { name: 'Trang 3' }))

    expect(await screen.findByText('Page 3 dish')).toBeInTheDocument()
    expect(requests.at(-1)!.get('page')).toBe('3')
    expect(screen.getByRole('button', { name: 'Trang sau' })).toBeDisabled()
  })

  it('searches and explains when nothing matches', async () => {
    const user = userEvent.setup()
    mockLayout()
    mockProductList()
    server.use(
      http.get('*/api/products/search', ({ request }) => {
        const q = new URL(request.url).searchParams.get('q')
        return HttpResponse.json(q === 'pho' ? [shakingBeef] : [])
      }),
    )
    renderApp('/menu')

    await user.type(await screen.findByRole('searchbox', { name: 'Tìm món ăn' }), 'pho')
    expect(await screen.findByText('Kết quả cho “pho”')).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Shaking Beef' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Shrimp Spring Rolls' })).not.toBeInTheDocument()

    await user.clear(screen.getByRole('searchbox'))
    await user.type(screen.getByRole('searchbox'), 'zzz')
    expect(await screen.findByText('Không tìm thấy món phù hợp')).toBeInTheDocument()
  })

  it('switches the whole interface to English', async () => {
    const user = userEvent.setup()
    mockLayout()
    mockProductList()
    renderApp('/menu')

    await screen.findByRole('heading', { name: 'Shrimp Spring Rolls' })
    await user.click(screen.getByRole('button', { name: 'EN' }))

    expect(screen.getByRole('heading', { level: 1, name: 'Our menu' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Main courses' })).toBeInTheDocument()
    expect(document.documentElement.lang).toBe('en')
    expect(window.localStorage.getItem('dateno_lang')).toBe('en')
  })

  it('offers a retry when the menu fails to load', async () => {
    const user = userEvent.setup()
    mockLayout()
    let fail = true
    server.use(
      http.get('*/api/products', () =>
        fail ? HttpResponse.json({ detail: 'boom' }, { status: 500 }) : HttpResponse.json(page()),
      ),
    )
    renderApp('/menu')

    expect(await screen.findByText('Không tải được nội dung.')).toBeInTheDocument()
    fail = false
    await user.click(screen.getByRole('button', { name: 'Thử lại' }))
    expect(await screen.findByRole('heading', { name: 'Shrimp Spring Rolls' })).toBeInTheDocument()
  })
})
