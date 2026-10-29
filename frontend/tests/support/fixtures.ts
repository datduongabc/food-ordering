import type { Category, Location, Product } from '@/features/catalog/schemas'
import type { Cart } from '@/features/cart/schemas'
import type { User } from '@/features/auth/schemas'

export const starters: Category = {
  id: 1,
  name: { vi: 'Khai vị', en: 'Starters' },
  slug: 'starters',
}
export const mains: Category = {
  id: 2,
  name: { vi: 'Món chính', en: 'Main Dishes' },
  slug: 'main_dishes',
}

export const district1: Location = {
  id: 1,
  name: { vi: 'DaTeNO - Quận 1', en: 'DaTeNO - District 1' },
  address: { vi: '123 Lê Lợi, Quận 1', en: '123 Le Loi Street, District 1' },
  map_url: 'https://www.google.com/maps/search/?api=1&query=123+Le+Loi+Street%2C+District+1',
}

let nextId = 100

export function product(overrides: Partial<Product> = {}): Product {
  const id = overrides.id ?? nextId++
  return {
    id,
    name: { vi: `Món ${id}`, en: `Dish ${id}` },
    slug: `dish-${id}`,
    description: { vi: 'Món ăn ngon.', en: 'A tasty dish.' },
    price: 250_000,
    average_rating: null,
    category: starters,
    locations: [district1],
    image_url: `/media/products/dish-${id}.webp`,
    ...overrides,
  }
}

export const springRolls = product({
  id: 1,
  name: { vi: 'Gỏi cuốn tôm thịt', en: 'Shrimp Spring Rolls' },
  slug: 'shrimp-spring-rolls',
  price: 237_500,
})

export const shakingBeef = product({
  id: 2,
  name: { vi: 'Bò lúc lắc', en: 'Shaking Beef' },
  slug: 'shaking-beef',
  price: 450_000,
  category: mains,
  average_rating: '4.50',
})

export function cartOf(...lines: [Product, number][]): Cart {
  const items = lines.map(([dish, quantity]) => ({
    product: dish,
    quantity,
    subtotal: dish.price * quantity,
  }))
  return {
    items,
    total_count: items.reduce((sum, line) => sum + line.quantity, 0),
    total_price: items.reduce((sum, line) => sum + line.subtotal, 0),
  }
}

export const customer: User = {
  id: 7,
  name: 'Nguyen Van A',
  email: 'a@example.com',
  phone: '0901234567',
  role: 'CUSTOMER',
  is_email_verified: true,
  created_at: '2026-10-01T03:00:00Z',
}
