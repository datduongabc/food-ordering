import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { mockApi, mockLayout } from '../support/api'
import { district1, shakingBeef, springRolls } from '../support/fixtures'
import { renderApp } from '../support/render'

function mockHome(reviews: unknown[]) {
  mockApi('get', '/products/featured', shakingBeef)
  mockApi('get', '/products', {
    items: [springRolls],
    page: 1,
    page_size: 4,
    total: 1,
    total_pages: 1,
  })
  mockApi('get', '/reviews/top', reviews)
}

describe('home page', () => {
  it('shows the featured dish, picks and branches with working map links', async () => {
    mockLayout()
    mockHome([])

    renderApp('/')

    expect(await screen.findByText('Món nổi bật')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Shaking Beef' })).toHaveAttribute(
      'href',
      '/menu/shaking-beef',
    )
    expect(await screen.findByRole('heading', { name: 'Shrimp Spring Rolls' })).toBeInTheDocument()
    const directions = await screen.findByRole('link', { name: /Chỉ đường/ })
    expect(directions).toHaveAttribute('href', district1.map_url)
    expect(directions).toHaveAttribute('target', '_blank')
    expect(screen.queryByText('Khách hàng nói gì về chúng tôi')).not.toBeInTheDocument()
  })

  it('shows real reviews once there are some', async () => {
    mockLayout()
    mockHome([
      {
        id: 1,
        rating: 5,
        comment: 'Rất ngon!',
        created_at: '2026-10-28T03:00:00Z',
        user_name: 'Chi',
        product_name: 'Shaking Beef',
        product_slug: 'shaking-beef',
      },
    ])

    renderApp('/')

    expect(await screen.findByText('Rất ngon!')).toBeInTheDocument()
    expect(screen.getByText('Chi')).toBeInTheDocument()
  })
})
