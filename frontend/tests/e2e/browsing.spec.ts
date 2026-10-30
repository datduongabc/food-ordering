import { expect, test } from '@playwright/test'
import { openMenu } from './support/session.ts'

test.describe('browsing the seeded menu', () => {
  test('home page leads to the menu and a dish', async ({ page }) => {
    await page.goto('/')

    await expect(page.getByRole('heading', { level: 1 })).toHaveText(
      'Ẩm thực Việt trọn vị, phục vụ tận tâm.',
    )
    await expect(page.getByText('Món nổi bật')).toBeVisible()
    const directions = page.getByRole('link', { name: /Chỉ đường/ })
    await expect(directions).toHaveCount(3)
    await expect(directions.first()).toHaveAttribute(
      'href',
      /^https:\/\/www\.google\.com\/maps\/search\/\?api=1&query=123\+L%C3%AA\+L%E1%BB%A3i/,
    )

    await page.getByRole('link', { name: 'Xem thực đơn' }).click()
    await expect(page).toHaveURL(/\/menu$/)
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Thực đơn')
    await expect(page.locator('article')).toHaveCount(12)

    const firstDish = page.locator('article h2 a').first()
    const name = await firstDish.textContent()
    await firstDish.click()
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(name ?? '')
    await expect(page.getByText(/₫/).first()).toBeVisible()
  })

  test('filters, sorts, pages and searches the real catalog', async ({ page }) => {
    await page.goto('/menu')

    await page.getByRole('button', { name: 'Món chính' }).click()
    await expect(page).toHaveURL(/category=main_dishes/)
    await expect(page.locator('article').first().getByText('Món chính')).toBeVisible()

    await page.getByRole('combobox', { name: 'Sắp xếp' }).selectOption('price_asc')
    await expect(page).toHaveURL(/sort=price_asc/)
    // The previous results stay on screen until the sorted page arrives, so poll.
    await expect
      .poll(async () => {
        const prices = await page.locator('article').evaluateAll((cards) =>
          cards.map((card) => {
            const text = card.querySelector('[class*="price"]')?.textContent ?? ''
            return Number(text.replace(/\D/g, ''))
          }),
        )
        return prices.length > 1 && prices.every((price, i) => i === 0 || prices[i - 1]! <= price)
      })
      .toBe(true)

    await page.goto('/menu')
    await page.getByRole('button', { name: 'Trang 2' }).click()
    await expect(page).toHaveURL(/page=2/)
    await expect(page.getByRole('button', { name: 'Trang 2' })).toHaveAttribute(
      'aria-current',
      'page',
    )

    await page.getByRole('searchbox', { name: 'Tìm món ăn' }).fill('zzzz-no-dish')
    await expect(page.getByText('Không tìm thấy món phù hợp')).toBeVisible()
  })

  test('remembers English across pages and reloads', async ({ page }) => {
    await page.goto('/menu')
    await expect(page.getByRole('heading', { name: 'Gỏi cuốn tôm thịt' })).toBeVisible()
    // On phones the language switch sits in the menu.
    await openMenu(page)
    await page.getByRole('button', { name: 'EN' }).click()
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Our menu')
    // Dish names come from the API in both languages and switch with the interface.
    await expect(page.getByRole('heading', { name: 'Shrimp & Pork Spring Rolls' })).toBeVisible()
    await expect(page.getByText('DaTeNO - District 1', { exact: true })).toBeVisible()

    await page.reload()
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Our menu')
    await page.getByRole('link', { name: 'RESTAURANT DaTeNO' }).click()
    await expect(page.getByRole('link', { name: 'View the menu' })).toBeVisible()
    await expect(page.locator('html')).toHaveAttribute('lang', 'en')
  })

  test('a guest cart survives a reload', async ({ page }) => {
    await page.goto('/menu')
    const card = page.locator('article').first()
    const name = (await card.locator('h2').textContent()) ?? ''

    await card.getByRole('button', { name: `Thêm ${name} vào giỏ hàng` }).click()
    await expect(page.getByRole('status').filter({ hasText: 'Đã thêm' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Giỏ hàng, 1 món' })).toBeVisible()

    await page.reload()
    await expect(page.getByRole('link', { name: 'Giỏ hàng, 1 món' })).toBeVisible()
  })

  test('shows the stored VND price and totals by quantity', async ({ page }) => {
    // Caesar salad is seeded at 312.500 ₫, carried over from its old 12.50 USD price.
    await page.goto('/menu/caesar-salad')
    await expect(page.getByText(/^312\.500\s₫$/)).toBeVisible()

    await page.getByRole('button', { name: 'Tăng số lượng' }).click()
    await expect(page.getByRole('button', { name: /^Thêm vào giỏ · 625\.000\s₫$/ })).toBeVisible()
  })

  test('unknown pages and dishes are explained', async ({ page }) => {
    await page.goto('/khong-co-trang-nay')
    await expect(page.getByText('Không tìm thấy trang')).toBeVisible()

    await page.goto('/menu/khong-co-mon-nay')
    await expect(page.getByText('Không tìm thấy món ăn')).toBeVisible()
  })
})
