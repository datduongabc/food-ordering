import type { Category, Location, Product } from '@/features/catalog/schemas'
import type { Cart } from '@/features/cart/schemas'
import type { User } from '@/features/auth/schemas'

export const starters: Category = { id: 1, name: 'Starters', slug: 'starters' }
export const mains: Category = { id: 2, name: 'Main Dishes', slug: 'main_dishes' }

export const district1: Location = {
  id: 1,
  name: 'DaTeNO - District 1',
  address: '123 Le Loi Street, District 1',
  map_url: 'https://www.google.com/maps/search/?api=1&query=123+Le+Loi+Street%2C+District+1',
}

let nextId = 100

export function product(overrides: Partial<Product> = {}): Product {
  const id = overrides.id ?? nextId++
  return {
    id,
    name: `Dish ${id}`,
    slug: `dish-${id}`,
    description: 'A tasty dish.',
    price: '10.00',
    average_rating: null,
    category: starters,
    locations: [district1],
    image_url: `/media/products/dish-${id}.webp`,
    ...overrides,
  }
}

export const springRolls = product({
  id: 1,
  name: 'Shrimp Spring Rolls',
  slug: 'shrimp-spring-rolls',
  price: '9.50',
})

export const shakingBeef = product({
  id: 2,
  name: 'Shaking Beef',
  slug: 'shaking-beef',
  price: '18.00',
  category: mains,
  average_rating: '4.50',
})

export function cartOf(...lines: [Product, number][]): Cart {
  const items = lines.map(([dish, quantity]) => ({
    product: dish,
    quantity,
    subtotal: (Number(dish.price) * quantity).toFixed(2),
  }))
  return {
    items,
    total_count: items.reduce((sum, line) => sum + line.quantity, 0),
    total_price: items.reduce((sum, line) => sum + Number(line.subtotal), 0).toFixed(2),
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
