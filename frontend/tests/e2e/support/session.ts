import { expect, type Page } from '@playwright/test'
import { emailedCode, uniqueEmail, uniquePhone } from './email.ts'

export async function openMenu(page: Page) {
  // On phones the navigation sits behind the menu button.
  const toggle = page.getByRole('button', { name: 'Điều hướng chính' })
  if (await toggle.isVisible()) await toggle.click()
}

/** Opens the account dropdown, where sign-in, the account page and sign-out live. */
export async function openUserMenu(page: Page) {
  await page.getByRole('button', { name: 'Tài khoản của bạn' }).click()
}

/** Creates a verified customer from the sign-up page the browser is on, through the real UI. */
export async function signUpHere(page: Page, name = 'Trần Thị Bích') {
  const email = uniqueEmail('shopper')
  await page.getByRole('link', { name: 'Đăng ký' }).click()
  await page.getByLabel('Họ và tên').fill(name)
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Số điện thoại').fill(uniquePhone())
  await page.getByLabel('Mật khẩu').fill('mat-khau-123')
  await page.getByRole('button', { name: 'Tạo tài khoản' }).click()
  await expect(page.getByRole('heading', { name: 'Xác thực email' })).toBeVisible()
  await page.getByLabel('Mã xác thực').fill(await emailedCode(email))
  await page.getByRole('button', { name: 'Xác thực' }).click()
  await expect(page.getByText('Email đã được xác thực.')).toBeVisible()
  return email
}
