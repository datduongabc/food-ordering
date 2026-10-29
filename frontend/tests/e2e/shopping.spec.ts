import { expect, test } from '@playwright/test'
import { openMenu, signUpHere } from './support/session.ts'

test('a guest orders, signs up at checkout and pays with MoMo after a declined try', async ({
  page,
}) => {
  await page.goto('/menu/shrimp-pork-spring-rolls')
  await page.getByRole('button', { name: 'Tăng số lượng' }).click()
  await page.getByRole('button', { name: /^Thêm vào giỏ/ }).click()
  await page.getByRole('link', { name: 'Giỏ hàng, 2 món' }).click()

  await expect(page.getByRole('heading', { name: 'Giỏ hàng' })).toBeVisible()
  await expect(page.getByText('2 món trong giỏ')).toBeVisible()
  await page.getByRole('link', { name: 'Tiến hành đặt hàng' }).click()

  // Checkout needs an account; signing up returns straight to it with the cart merged.
  await expect(page).toHaveURL(/\/login\?next=%2Fcheckout/)
  await signUpHere(page)
  await expect(page.getByRole('heading', { name: 'Đặt hàng' })).toBeVisible()
  await expect(page.getByLabel('Người nhận')).toHaveValue('Trần Thị Bích')

  await page.getByLabel('Địa chỉ giao hàng').fill('102 Nguyễn Thị Thập, Quận 7')
  await page.getByText('Ví MoMo').click()
  await page.getByRole('button', { name: 'Đặt hàng và thanh toán MoMo' }).click()

  await expect(page.getByRole('heading', { name: 'Thanh toán bằng MoMo' })).toBeVisible()
  await expect(page.getByText(/không có giao dịch thật/)).toBeVisible()
  await page.getByRole('button', { name: 'Từ chối giao dịch' }).click()
  await expect(page.getByRole('heading', { name: 'Thanh toán chưa thành công' })).toBeVisible()

  await page.getByRole('button', { name: 'Thử lại' }).click()
  await page.getByRole('button', { name: 'Xác nhận thanh toán' }).click()
  await expect(page.getByText('Thanh toán thành công')).toBeVisible()
  await page.getByRole('link', { name: 'Xem đơn hàng' }).click()

  const detail = page.getByRole('region', { name: /^Đơn hàng #\d+$/ })
  await expect(detail.getByText('Đã xác nhận', { exact: true })).toBeVisible()
  await expect(detail.getByText('Đã thanh toán')).toBeVisible()
  await expect(detail.getByText('Đã nhận thanh toán MoMo, đơn hàng được xác nhận')).toBeVisible()
  await expect(page.getByRole('link', { name: 'Giỏ hàng, 0 món' })).toBeVisible()
})

test('a customer cancels a cash order, then books and cancels a table', async ({ page }) => {
  await page.goto('/login')
  await signUpHere(page, 'Lê Văn Cường')

  await page.goto('/menu')
  await page
    .locator('article')
    .first()
    .getByRole('button', { name: /^Thêm .* vào giỏ hàng$/ })
    .click()
  await expect(page.getByRole('link', { name: 'Giỏ hàng, 1 món' })).toBeVisible()
  await page.goto('/checkout')
  await page.getByLabel('Địa chỉ giao hàng').fill('12 Nguyễn Huệ, Quận 1')
  await page.getByRole('button', { name: 'Xác nhận đặt hàng' }).click()

  await expect(page.getByText(/^Đã đặt đơn hàng #\d+\.$/)).toBeVisible()
  const detail = page.getByRole('region', { name: /^Đơn hàng #\d+$/ })
  await expect(detail.getByText('Chờ xác nhận', { exact: true })).toBeVisible()
  await detail.getByRole('button', { name: 'Hủy đơn hàng' }).click()
  await detail.getByRole('button', { name: 'Hủy đơn', exact: true }).click()
  await expect(detail.getByText('Quý khách đã hủy đơn')).toBeVisible()
  await expect(detail.getByRole('button', { name: 'Hủy đơn hàng' })).toHaveCount(0)

  await openMenu(page)
  await page
    .getByRole('navigation', { name: 'Điều hướng chính' })
    .getByRole('link', { name: 'Đặt bàn' })
    .click()
  const booking = page.locator('#book')
  await expect(booking.getByLabel('Họ và tên')).toHaveValue('Lê Văn Cường')
  // Tomorrow always has every seating, whatever time the test runs.
  await booking
    .locator('label')
    .filter({ has: page.locator('input[type=radio]') })
    .nth(1)
    .click()
  await booking.getByLabel('Giờ').selectOption('19:30')
  await booking.getByLabel('Số khách').selectOption('4')
  await booking.getByLabel('Yêu cầu thêm (không bắt buộc)').fill('Cần ghế trẻ em')
  await booking.getByRole('button', { name: 'Xác nhận đặt bàn' }).click()

  await expect(booking.getByText('Cảm ơn quý khách!')).toBeVisible()
  await booking.getByRole('link', { name: 'Xem lịch đặt bàn' }).click()
  await expect(page.getByText(/19:30 · 4 khách/)).toBeVisible()
  await expect(page.getByText('Yêu cầu: Cần ghế trẻ em')).toBeVisible()
  await page.getByRole('button', { name: 'Hủy đặt bàn' }).click()
  await expect(page.getByText('Đã hủy lịch đặt bàn.')).toBeVisible()
  await expect(page.getByText('Đã hủy', { exact: true })).toBeVisible()
})
