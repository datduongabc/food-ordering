import { expect, test, type Page } from '@playwright/test'
import { emailedCode, uniqueEmail, uniquePhone } from './support/email.ts'
import { openUserMenu } from './support/session.ts'

async function signOut(page: Page) {
  await openUserMenu(page)
  await page.getByRole('button', { name: 'Đăng xuất' }).click()
  await expect(page.getByText('Đã đăng xuất.')).toBeVisible()
}

test('a guest signs up, verifies the email and keeps the cart across sessions', async ({
  page,
}) => {
  const email = uniqueEmail('signup')
  const password = 'mat-khau-123'

  await page.goto('/menu/shrimp-pork-spring-rolls')
  await page.getByRole('button', { name: /^Thêm vào giỏ/ }).click()
  await expect(page.getByRole('link', { name: 'Giỏ hàng, 1 món' })).toBeVisible()

  await page.getByRole('link', { name: 'Đăng nhập', exact: true }).last().click()
  await page.getByRole('link', { name: 'Đăng ký' }).click()
  await expect(page.getByRole('heading', { name: 'Tạo tài khoản' })).toBeVisible()
  await page.getByLabel('Họ và tên').fill('Trần Thị Bích')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Số điện thoại').fill(uniquePhone())
  await page.getByLabel('Mật khẩu').fill(password)
  await page.getByRole('button', { name: 'Tạo tài khoản' }).click()

  await expect(page.getByRole('heading', { name: 'Xác thực email' })).toBeVisible()
  await page.getByLabel('Mã xác thực').fill(await emailedCode(email))
  await page.getByRole('button', { name: 'Xác thực' }).click()

  // Back on the dish, signed in, with the dish picked as a guest now in the account cart.
  await expect(page).toHaveURL(/\/menu\/shrimp-pork-spring-rolls/)
  await expect(page.getByText('Email đã được xác thực.')).toBeVisible()
  await expect(page.getByRole('link', { name: 'Giỏ hàng, 1 món' })).toBeVisible()

  await signOut(page)
  await expect(page.getByRole('link', { name: 'Giỏ hàng, 0 món' })).toBeVisible()

  await page.goto('/login')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Mật khẩu').fill(password)
  await page.getByRole('button', { name: 'Đăng nhập' }).click()
  await expect(page).toHaveURL(/\/$/)
  await expect(page.getByRole('link', { name: 'Giỏ hàng, 1 món' })).toBeVisible()
})

test('wrong passwords are explained and a forgotten one can be reset', async ({ page }) => {
  const email = uniqueEmail('reset')
  await page.goto('/register')
  await page.getByLabel('Họ và tên').fill('Lê Văn Cường')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Số điện thoại').fill(uniquePhone())
  await page.getByLabel('Mật khẩu').fill('mat-khau-cu-1')
  await page.getByRole('button', { name: 'Tạo tài khoản' }).click()
  await page.getByRole('link', { name: 'Để sau, tiếp tục xem thực đơn' }).click()
  await signOut(page)

  await page.goto('/login')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Mật khẩu').fill('sai-mat-khau')
  await page.getByRole('button', { name: 'Đăng nhập' }).click()
  await expect(page.getByRole('alert')).toHaveText('Email hoặc mật khẩu không đúng.')

  await page.getByRole('link', { name: 'Quên mật khẩu?' }).click()
  await expect(page.getByRole('heading', { name: 'Quên mật khẩu' })).toBeVisible()
  await page.getByLabel('Email').fill(email)
  await page.getByRole('button', { name: 'Gửi mã' }).click()
  await expect(page.getByText(`Nếu ${email} đã được đăng ký`)).toBeVisible()

  // The first email was the sign-up verification code; the reset code is the second.
  await page.getByLabel('Mã xác thực').fill(await emailedCode(email, 2))
  await page.getByLabel('Mật khẩu mới').fill('mat-khau-moi-2')
  await page.getByRole('button', { name: 'Đổi mật khẩu' }).click()
  await expect(page.getByRole('heading', { name: 'Đã đổi mật khẩu' })).toBeVisible()

  await page.getByRole('link', { name: 'Đăng nhập ngay' }).click()
  await expect(page.getByRole('heading', { name: 'Đăng nhập' })).toBeVisible()
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Mật khẩu').fill('mat-khau-moi-2')
  await page.getByRole('button', { name: 'Đăng nhập' }).click()
  // Navigating closes the dropdown, so only open it once the redirect has happened.
  await expect(page).toHaveURL(/\/$/)
  await openUserMenu(page)
  await expect(page.getByRole('link', { name: 'Tài khoản' })).toBeVisible()
})
