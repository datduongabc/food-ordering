import { resolve } from 'node:path'
import { expect, test, type Page } from '@playwright/test'
import { ADMIN } from './support/accounts.ts'
import { openUserMenu, signUpHere } from './support/session.ts'

const PHOTO = resolve(import.meta.dirname, '../../../backend/media/products/placeholder.webp')

async function signInAsAdmin(page: Page) {
  await page.context().clearCookies()
  await page.goto('/login?next=%2Fadmin')
  await page.getByLabel('Email').fill(ADMIN.email)
  await page.getByLabel('Mật khẩu').fill(ADMIN.password)
  await page.getByRole('button', { name: 'Đăng nhập' }).click()
  await expect(page.getByRole('heading', { name: 'Tổng quan', level: 1 })).toBeVisible()
}

test('staff move an order and a booking along, then manage dishes and accounts', async ({
  page,
}, testInfo) => {
  // Desktop and mobile share one database, so each run adds a dish of its own.
  const dish = `Bánh xèo ${testInfo.project.name}`
  const slug = `banh-xeo-${testInfo.project.name}`
  // A customer orders for delivery and books a table.
  await page.goto('/login')
  const customerEmail = await signUpHere(page, 'Ngô Thị Lan')
  await page.goto('/menu')
  await page
    .locator('article')
    .first()
    .getByRole('button', { name: /^Thêm .* vào giỏ hàng$/ })
    .click()
  await expect(page.getByRole('link', { name: 'Giỏ hàng, 1 món' })).toBeVisible()
  await page.goto('/checkout')
  await page.getByLabel('Địa chỉ giao hàng').fill('8 Pasteur, Quận 1')
  await page.getByRole('button', { name: 'Xác nhận đặt hàng' }).click()
  const placed = await page.getByText(/^Đã đặt đơn hàng #\d+\.$/).textContent()
  const orderId = placed!.match(/#(\d+)/)![1]!

  await page.goto('/#book')
  const booking = page.locator('#book')
  await booking
    .locator('label')
    .filter({ has: page.locator('input[type=radio]') })
    .nth(1)
    .click()
  await booking.getByLabel('Giờ').selectOption('18:00')
  await booking.getByRole('button', { name: 'Xác nhận đặt bàn' }).click()
  await expect(booking.getByText('Cảm ơn quý khách!')).toBeVisible()

  await signInAsAdmin(page)

  // Orders: confirm with a note, then deliver; cash is collected on delivery.
  await page.getByRole('link', { name: 'Đơn chờ xác nhận' }).click()
  await page.getByRole('button', { name: new RegExp(`^#${orderId} `) }).click()
  const order = page.getByRole('region', { name: `Đơn hàng #${orderId}` })
  await expect(order.getByText('Ngô Thị Lan', { exact: true })).toBeVisible()
  await order.getByLabel('Ghi chú cho khách (không bắt buộc)').fill('Giao trong 30 phút')
  await order.getByRole('button', { name: 'Xác nhận đơn' }).click()
  await expect(page.getByText(`Đơn hàng #${orderId}: Đã xác nhận.`)).toBeVisible()

  await page.getByRole('button', { name: 'Tất cả' }).click()
  await page.getByRole('button', { name: new RegExp(`^#${orderId} `) }).click()
  await expect(order.getByText(`Đã xác nhận · ${ADMIN.name}`)).toBeVisible()
  await expect(order.getByText('Giao trong 30 phút')).toBeVisible()
  await order.getByRole('button', { name: 'Đã giao xong' }).click()
  await expect(order.getByText('Hoàn thành', { exact: true })).toBeVisible()
  await expect(order.getByText('Đã thanh toán')).toBeVisible()
  await expect(order.getByText('Đơn hàng đã kết thúc, không thể đổi trạng thái.')).toBeVisible()

  // Bookings: confirm the table.
  await page
    .getByRole('navigation', { name: 'Mục quản trị' })
    .getByRole('link', { name: 'Đặt bàn' })
    .click()
  const row = page.getByRole('row').filter({ hasText: 'Ngô Thị Lan' })
  await row.getByRole('button', { name: 'Xác nhận' }).click()
  await expect(row.getByText('Đã xác nhận')).toBeVisible()
  await expect(row.getByRole('button', { name: 'Khách đã đến' })).toBeVisible()

  // Dishes: add one, give it a photo, hide it from the menu and put it back.
  await page
    .getByRole('navigation', { name: 'Mục quản trị' })
    .getByRole('link', { name: 'Món ăn' })
    .click()
  await page.getByRole('link', { name: '+ Thêm món' }).click()
  await page.getByLabel('Tên tiếng Việt').fill(dish)
  await page.getByLabel('Tên tiếng Anh').fill(`Sizzling Crepe ${testInfo.project.name}`)
  await page.getByLabel('Mô tả tiếng Việt').fill('Bánh xèo giòn nhân tôm, thịt và giá.')
  await page.getByLabel('Mô tả tiếng Anh').fill('Crispy crepe with shrimp, pork and bean sprouts.')
  await page.getByLabel('Giá (VND)').fill('95.000')
  await page.getByLabel('Danh mục').selectOption({ index: 1 })
  await page.getByLabel('Đường dẫn (không bắt buộc)').fill(slug)
  await page.getByRole('button', { name: 'Lưu thay đổi' }).click()
  await expect(page.getByText(`Đã thêm ${dish}.`)).toBeVisible()
  await expect(page.getByRole('heading', { name: `Sửa món: ${dish}` })).toBeVisible()
  await page.getByLabel('Chọn ảnh').setInputFiles(PHOTO)
  await page.getByRole('button', { name: 'Tải ảnh lên' }).click()
  await expect(page.getByText('Đã cập nhật ảnh món.')).toBeVisible()

  await page.getByRole('link', { name: '← Danh sách món' }).click()
  await page.getByLabel('Tìm món').fill(`banh xeo ${testInfo.project.name}`)
  await page.getByRole('button', { name: `Ẩn món ${dish}` }).click()
  await expect(page.getByText(`Đã ẩn ${dish} khỏi thực đơn.`)).toBeVisible()
  await expect(page.getByRole('row').filter({ hasText: dish })).toHaveCount(0)
  // The filter lives in the URL, so the box ticks once the navigation settles.
  await page.getByLabel('Hiện cả món đã ẩn').click()
  await expect(page.getByLabel('Hiện cả món đã ẩn')).toBeChecked()
  await page.getByRole('button', { name: `Bán lại ${dish}` }).click()
  await expect(page.getByText(`Đã đưa ${dish} trở lại thực đơn.`)).toBeVisible()
  await page.goto(`/menu/${slug}`)
  await expect(page.getByRole('heading', { name: dish })).toBeVisible()

  // Accounts: deactivate the customer, then restore them.
  await page.goto('/admin/users')
  await page.getByLabel('Tìm theo tên, email, số điện thoại').fill(customerEmail)
  const customer = page.getByRole('row').filter({ hasText: customerEmail })
  await customer.getByRole('button', { name: 'Vô hiệu hóa Ngô Thị Lan' }).click()
  await customer.getByRole('button', { name: 'Vô hiệu hóa', exact: true }).click()
  await expect(page.getByText('Đã vô hiệu hóa Ngô Thị Lan.')).toBeVisible()
  // The filter lives in the URL, so the box ticks once the navigation settles.
  await page.getByLabel('Hiện cả tài khoản đã vô hiệu hóa').click()
  await expect(page.getByLabel('Hiện cả tài khoản đã vô hiệu hóa')).toBeChecked()
  await customer.getByRole('button', { name: 'Khôi phục Ngô Thị Lan' }).click()
  await expect(page.getByText('Đã khôi phục Ngô Thị Lan.')).toBeVisible()
})

test('customers cannot open the admin pages', async ({ page }) => {
  await page.goto('/login')
  await signUpHere(page, 'Đỗ Minh Quân')
  await page.goto('/admin')
  await expect(page.getByText('Trang dành cho quản trị viên')).toBeVisible()
  await openUserMenu(page)
  await expect(page.getByRole('link', { name: 'Tài khoản', exact: true })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Quản trị' })).toHaveCount(0)
})

test('staff create a promo code, a customer pays less with it and orders the same again', async ({
  page,
}) => {
  const code = `E2E${Date.now().toString(36).toUpperCase()}`
  await signInAsAdmin(page)
  await page.goto('/admin/promo-codes')
  await page.getByRole('button', { name: '+ Thêm mã' }).click()
  await page.getByLabel('Mã', { exact: true }).fill(code.toLowerCase())
  await page.getByLabel('Phần trăm giảm').fill('10')
  await page.getByRole('button', { name: 'Lưu thay đổi' }).click()
  await expect(page.getByText(`Đã tạo mã ${code}.`)).toBeVisible()

  await page.context().clearCookies()
  await page.goto('/login')
  await signUpHere(page, 'Phan Thị Mai')
  await page.goto('/menu')
  await page
    .locator('article')
    .first()
    .getByRole('button', { name: /^Thêm .* vào giỏ hàng$/ })
    .click()
  await expect(page.getByRole('link', { name: 'Giỏ hàng, 1 món' })).toBeVisible()
  await page.goto('/checkout')
  await page.getByLabel('Địa chỉ giao hàng').fill('3 Lê Lợi, Quận 1')
  await page.getByLabel('Mã giảm giá').fill(code)
  await page.getByRole('button', { name: 'Áp dụng' }).click()
  await expect(page.getByText(`Đã áp dụng mã ${code}`)).toBeVisible()
  await page.getByRole('button', { name: 'Xác nhận đặt hàng' }).click()

  const detail = page.getByRole('region', { name: /^Đơn hàng #\d+$/ })
  await expect(detail.getByText(`Giảm giá (${code})`)).toBeVisible()
  await detail.getByRole('button', { name: 'Đặt lại' }).click()
  await expect(page).toHaveURL(/\/cart$/)
  await expect(page.getByRole('link', { name: 'Giỏ hàng, 1 món' })).toBeVisible()
})

test('a customer reviews a delivered dish with a photo and staff reply, then hide it', async ({
  page,
}, testInfo) => {
  const comment = `Nước dùng đậm đà (${testInfo.project.name} ${Date.now()})`
  await page.goto('/login')
  const email = await signUpHere(page, 'Lý Văn Tâm')
  await page.goto('/menu')
  const card = page.locator('article').first()
  const dish = (await card.getByRole('heading').textContent())!.trim()
  await card.getByRole('button', { name: /^Thêm .* vào giỏ hàng$/ }).click()
  await expect(page.getByRole('link', { name: 'Giỏ hàng, 1 món' })).toBeVisible()
  await page.goto('/checkout')
  await page.getByLabel('Địa chỉ giao hàng').fill('5 Hai Bà Trưng, Quận 1')
  await page.getByRole('button', { name: 'Xác nhận đặt hàng' }).click()
  const placed = await page.getByText(/^Đã đặt đơn hàng #\d+\.$/).textContent()
  const orderId = placed!.match(/#(\d+)/)![1]!

  // Not delivered yet, so the dish page explains instead of offering the form.
  await page.goto('/menu')
  await page.getByRole('link', { name: dish, exact: true }).first().click()
  await expect(
    page.getByText('Quý khách có thể đánh giá sau khi nhận được đơn hàng có món này.'),
  ).toBeVisible()

  await signInAsAdmin(page)
  await page.goto('/admin/orders')
  await page.getByRole('button', { name: new RegExp(`^#${orderId} `) }).click()
  const order = page.getByRole('region', { name: `Đơn hàng #${orderId}` })
  await order.getByRole('button', { name: 'Xác nhận đơn' }).click()
  await expect(page.getByText(`Đơn hàng #${orderId}: Đã xác nhận.`)).toBeVisible()
  await page.getByRole('button', { name: new RegExp(`^#${orderId} `) }).click()
  await order.getByRole('button', { name: 'Đã giao xong' }).click()
  await expect(order.getByText('Hoàn thành', { exact: true })).toBeVisible()

  // The delivered order links to the review form.
  await page.context().clearCookies()
  await page.goto('/login?next=%2Faccount')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Mật khẩu').fill('mat-khau-123')
  await page.getByRole('button', { name: 'Đăng nhập' }).click()
  await page.getByRole('link', { name: `Đánh giá ${dish}` }).click()
  await page.getByRole('button', { name: '4 sao', exact: true }).click()
  await page.getByRole('textbox', { name: 'Nhận xét' }).fill(comment)
  await page.getByLabel(/Ảnh món ăn/).setInputFiles(PHOTO)
  await page.getByRole('button', { name: 'Gửi đánh giá' }).click()
  await expect(page.getByText('Đánh giá đã được ghi nhận.')).toBeVisible()

  const mine = page.getByRole('listitem').filter({ hasText: comment })
  await expect(mine.getByText('Đã mua')).toBeVisible()
  await expect(mine.getByRole('img', { name: 'Ảnh món ăn của Lý Văn Tâm' })).toBeVisible()

  // Staff reply, then hide it; it leaves the dish page.
  await signInAsAdmin(page)
  await page.goto('/admin/reviews')
  const review = page.getByRole('listitem').filter({ hasText: comment })
  await review.getByRole('button', { name: 'Phản hồi' }).click()
  await review.getByLabel('Phản hồi công khai của nhà hàng').fill('Cảm ơn anh Tâm!')
  await review.getByRole('button', { name: 'Lưu thay đổi' }).click()
  await expect(page.getByText('Đã lưu phản hồi.')).toBeVisible()
  await expect(review.getByText('Cảm ơn anh Tâm!')).toBeVisible()
  await review.getByRole('button', { name: 'Ẩn' }).click()
  await expect(page.getByText('Đã ẩn đánh giá của Lý Văn Tâm.')).toBeVisible()

  await page.goto('/menu')
  await page.getByRole('link', { name: dish, exact: true }).first().click()
  await expect(page.getByRole('heading', { name: 'Đánh giá của khách hàng' })).toBeVisible()
  await expect(page.getByText(comment)).toHaveCount(0)
})
