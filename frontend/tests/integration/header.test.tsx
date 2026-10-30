import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { admin } from '../support/adminFixtures'
import { mockLayout } from '../support/api'
import { renderApp } from '../support/render'

const ACCOUNT_BUTTON = { name: 'Tài khoản của bạn' }

describe('account dropdown', () => {
  it('offers sign-in and sign-up to guests, and the main navigation holds no account links', async () => {
    const user = userEvent.setup()
    mockLayout()
    const { router } = renderApp('/cart')

    const button = await screen.findByRole('button', ACCOUNT_BUTTON)
    expect(button).toHaveAttribute('aria-expanded', 'false')
    expect(screen.getByRole('navigation', { name: 'Điều hướng chính' })).not.toHaveTextContent(
      'Đăng nhập',
    )

    await user.click(button)
    expect(button).toHaveAttribute('aria-expanded', 'true')
    await user.click(screen.getByRole('link', { name: 'Đăng ký' }))

    await waitFor(() => expect(router.state.location.pathname).toBe('/register'))
    expect(button).toHaveAttribute('aria-expanded', 'false')
  })

  it('shows an admin who they are, with admin, account and sign-out', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    renderApp('/cart')

    await user.click(await screen.findByRole('button', ACCOUNT_BUTTON))

    expect(screen.getByText(admin.email)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Quản trị' })).toHaveAttribute('href', '/admin')
    expect(screen.getByRole('link', { name: 'Tài khoản' })).toHaveAttribute('href', '/account')
    expect(screen.getByRole('button', { name: 'Đăng xuất' })).toBeInTheDocument()
  })

  it('closes on Escape, returning focus, and on a click elsewhere', async () => {
    const user = userEvent.setup()
    mockLayout()
    renderApp('/cart')
    const button = await screen.findByRole('button', ACCOUNT_BUTTON)

    await user.click(button)
    await user.keyboard('{Escape}')
    expect(button).toHaveAttribute('aria-expanded', 'false')
    expect(button).toHaveFocus()

    await user.click(button)
    await user.click(document.body)
    expect(button).toHaveAttribute('aria-expanded', 'false')
  })
})
