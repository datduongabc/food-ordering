import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw/http'
import { describe, expect, it } from 'vitest'
import { guestCart } from '@/features/cart/guestCart'
import { apiError, mockApi, mockLayout } from '../support/api'
import { cartOf, customer, springRolls } from '../support/fixtures'
import { renderApp } from '../support/render'
import { server } from '../support/server'

/** Records the JSON body of each call to these endpoints, in order. */
function recordCalls(...handlers: [string, string, unknown, number?][]) {
  const calls: { path: string; body: unknown }[] = []
  for (const [method, path, response, status = 200] of handlers) {
    server.use(
      http[method as 'post'](`*/api${path}`, async ({ request }) => {
        const text = await request.text()
        calls.push({ path, body: text ? JSON.parse(text) : null })
        return HttpResponse.json(response as never, { status })
      }),
    )
  }
  return calls
}

describe('sign up', () => {
  it('validates every field in Vietnamese before calling the API', async () => {
    const user = userEvent.setup()
    mockLayout()
    renderApp('/register')

    await user.click(await screen.findByRole('button', { name: 'Tạo tài khoản' }))

    expect(screen.getByLabelText('Họ và tên')).toHaveAccessibleDescription(
      'Vui lòng nhập thông tin này.',
    )
    expect(screen.getByLabelText('Số điện thoại')).toHaveAccessibleDescription(
      'Số điện thoại gồm 10 chữ số.',
    )
    expect(screen.getByLabelText('Mật khẩu')).toHaveAccessibleDescription(
      'Mật khẩu cần tối thiểu 8 ký tự.',
    )
  })

  it('registers, signs in, merges the guest cart and asks for the email code', async () => {
    const user = userEvent.setup()
    mockLayout()
    window.localStorage.setItem(
      'dateno_guest_cart',
      JSON.stringify([{ product_id: springRolls.id, quantity: 2 }]),
    )
    guestCart.reload()
    mockApi('post', '/cart/preview', cartOf([springRolls, 2]))
    const calls = recordCalls(
      ['post', '/auth/register', { ...customer, is_email_verified: false }, 201],
      ['post', '/auth/login', { ...customer, is_email_verified: false }],
      ['post', '/auth/email/verification', { detail: 'sent' }, 202],
      ['post', '/cart/merge', cartOf([springRolls, 2])],
    )
    const { router } = renderApp('/register?next=/menu')

    await user.type(await screen.findByLabelText('Họ và tên'), 'Nguyen Van A')
    await user.type(screen.getByLabelText('Email'), 'A@Example.com ')
    await user.type(screen.getByLabelText('Số điện thoại'), '0901 234 567')
    await user.type(screen.getByLabelText('Mật khẩu'), 'secret-pass')
    await user.click(screen.getByRole('button', { name: 'Tạo tài khoản' }))

    expect(await screen.findByRole('heading', { name: 'Xác thực email' })).toBeInTheDocument()
    expect(router.state.location.pathname + router.state.location.search).toBe(
      '/verify-email?next=%2Fmenu',
    )
    expect(calls.map((call) => call.path)).toEqual([
      '/auth/register',
      '/auth/login',
      '/auth/email/verification',
      '/cart/merge',
    ])
    expect(calls[0]?.body).toEqual({
      name: 'Nguyen Van A',
      email: 'a@example.com',
      phone: '0901234567',
      password: 'secret-pass',
    })
    expect(calls[3]?.body).toEqual({ items: [{ product_id: springRolls.id, quantity: 2 }] })
    expect(window.localStorage.getItem('dateno_guest_cart')).toBeNull()
  })

  it('shows "email already registered" under the email field', async () => {
    const user = userEvent.setup()
    mockLayout()
    mockApi('post', '/auth/register', apiError('email_taken'), 409)
    renderApp('/register')

    await user.type(await screen.findByLabelText('Họ và tên'), 'A')
    await user.type(screen.getByLabelText('Email'), 'a@example.com')
    await user.type(screen.getByLabelText('Số điện thoại'), '0901234567')
    await user.type(screen.getByLabelText('Mật khẩu'), 'secret-pass')
    await user.click(screen.getByRole('button', { name: 'Tạo tài khoản' }))

    await waitFor(() =>
      expect(screen.getByLabelText('Email')).toHaveAccessibleDescription(
        'Email này đã được đăng ký.',
      ),
    )
    expect(screen.getByLabelText('Email')).toHaveFocus()
  })
})

describe('sign in', () => {
  it('signs in and returns to the page that asked for it', async () => {
    const user = userEvent.setup()
    mockLayout()
    mockApi('get', '/cart', cartOf())
    const calls = recordCalls(['post', '/auth/login', customer])
    const { router } = renderApp('/login?next=/menu/shrimp-spring-rolls%23reviews')

    await user.type(await screen.findByLabelText('Email'), 'a@example.com')
    await user.type(screen.getByLabelText('Mật khẩu'), 'secret-pass')
    await user.click(screen.getByRole('checkbox', { name: 'Ghi nhớ đăng nhập' }))
    await user.click(screen.getByRole('button', { name: 'Đăng nhập' }))

    await waitFor(() => expect(router.state.location.pathname).toBe('/menu/shrimp-spring-rolls'))
    expect(router.state.location.hash).toBe('#reviews')
    expect(calls[0]?.body).toEqual({
      email: 'a@example.com',
      password: 'secret-pass',
      remember: true,
    })
    expect(screen.getByRole('link', { name: 'Tài khoản' })).toBeInTheDocument()
  })

  it('translates wrong credentials and lockouts', async () => {
    const user = userEvent.setup()
    mockLayout()
    mockApi('post', '/auth/login', apiError('login_locked', { minutes: 12 }), 429)
    renderApp('/login')

    await user.type(await screen.findByLabelText('Email'), 'a@example.com')
    await user.type(screen.getByLabelText('Mật khẩu'), 'x')
    await user.click(screen.getByRole('button', { name: 'Đăng nhập' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Tài khoản tạm khóa do đăng nhập sai nhiều lần. Vui lòng thử lại sau 12 phút.',
    )
  })

  it('sends signed-in visitors on instead of showing the form', async () => {
    mockLayout({ signedIn: customer })
    const { router } = renderApp('/login?next=/menu')
    await waitFor(() => expect(router.state.location.pathname).toBe('/menu'))
  })

  it('ignores a next parameter that points at another site', async () => {
    const user = userEvent.setup()
    mockLayout()
    mockApi('post', '/auth/login', customer)
    const { router } = renderApp('/login?next=//evil.example')

    await user.type(await screen.findByLabelText('Email'), 'a@example.com')
    await user.type(screen.getByLabelText('Mật khẩu'), 'secret-pass')
    await user.click(screen.getByRole('button', { name: 'Đăng nhập' }))

    await waitFor(() => expect(router.state.location.pathname).toBe('/'))
  })
})

describe('email verification', () => {
  it('rejects a wrong code under the field, then accepts the right one', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: { ...customer, is_email_verified: false } })
    let attempts = 0
    server.use(
      http.post('*/api/auth/email/verify', () =>
        ++attempts === 1
          ? HttpResponse.json(apiError('invalid_code'), { status: 400 })
          : HttpResponse.json(customer),
      ),
    )
    const { router } = renderApp('/verify-email?next=/menu')

    expect(await screen.findByText(/a@example\.com/)).toBeInTheDocument()
    await user.type(screen.getByLabelText('Mã xác thực'), '111111')
    await user.click(screen.getByRole('button', { name: 'Xác thực' }))
    await waitFor(() =>
      expect(screen.getByLabelText('Mã xác thực')).toHaveAccessibleDescription(
        'Mã xác thực không đúng hoặc đã hết hạn. Vui lòng yêu cầu mã mới.',
      ),
    )

    await user.clear(screen.getByLabelText('Mã xác thực'))
    await user.type(screen.getByLabelText('Mã xác thực'), '222222')
    await user.click(screen.getByRole('button', { name: 'Xác thực' }))

    await waitFor(() => expect(router.state.location.pathname).toBe('/menu'))
    expect(screen.getByText('Email đã được xác thực.')).toBeInTheDocument()
  })

  it('sends visitors to sign in first', async () => {
    mockLayout()
    const { router } = renderApp('/verify-email')
    await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
  })
})

describe('password reset', () => {
  it('requests a code, then sets a new password', async () => {
    const user = userEvent.setup()
    mockLayout()
    const calls = recordCalls(['post', '/auth/password/forgot', { detail: 'sent' }, 202])
    server.use(
      http.post('*/api/auth/password/reset', async ({ request }) => {
        calls.push({ path: '/auth/password/reset', body: await request.json() })
        return new HttpResponse(null, { status: 204 })
      }),
    )
    renderApp('/login')

    await user.click(await screen.findByRole('link', { name: 'Quên mật khẩu?' }))
    await screen.findByRole('heading', { name: 'Quên mật khẩu' })
    await user.type(screen.getByLabelText('Email'), 'a@example.com')
    await user.click(screen.getByRole('button', { name: 'Gửi mã' }))

    expect(
      await screen.findByText(
        'Nếu a@example.com đã được đăng ký, mã xác thực sẽ được gửi đến hộp thư trong ít phút.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toHaveValue('a@example.com')
    await user.type(screen.getByLabelText('Mã xác thực'), '123456')
    await user.type(screen.getByLabelText('Mật khẩu mới'), 'new-secret-1')
    await user.click(screen.getByRole('button', { name: 'Đổi mật khẩu' }))

    expect(await screen.findByRole('heading', { name: 'Đã đổi mật khẩu' })).toBeInTheDocument()
    expect(calls.map((call) => call.body)).toEqual([
      { email: 'a@example.com' },
      { email: 'a@example.com', code: '123456', new_password: 'new-secret-1' },
    ])
  })
})

describe('sign out', () => {
  it('signs out from the header', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: customer })
    mockApi('get', '/products/featured', null)
    mockApi('get', '/products', { items: [], page: 1, page_size: 5, total: 0, total_pages: 0 })
    mockApi('get', '/reviews/top', [])
    server.use(http.post('*/api/auth/logout', () => new HttpResponse(null, { status: 204 })))
    renderApp('/')

    await user.click(await screen.findByRole('button', { name: 'Đăng xuất' }))

    expect(await screen.findByRole('link', { name: 'Đăng nhập' })).toBeInTheDocument()
    expect(screen.getByText('Đã đăng xuất.')).toBeInTheDocument()
  })
})
