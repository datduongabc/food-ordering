import type { Category, Location, Product } from '@/features/catalog/schemas'
import type { Cart } from '@/features/cart/schemas'
import type { User } from '@/features/auth/schemas'
import type { Order } from '@/features/orders/schemas'
import type { Reservation, ReservationPolicy } from '@/features/reservations/schemas'
import type { Review, ReviewPage } from '@/features/reviews/schemas'

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
    review_count: 0,
    category: starters,
    locations: [district1],
    image_url: `/media/products/dish-${id}.webp`,
    thumbnail_url: `/media/products/thumbs/dish-${id}.webp`,
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
  review_count: 12,
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

export const district7: Location = {
  id: 2,
  name: { vi: 'DaTeNO - Quận 7', en: 'DaTeNO - District 7' },
  address: { vi: '456 Nguyễn Văn Linh, Quận 7', en: '456 Nguyen Van Linh, District 7' },
  map_url: 'https://www.google.com/maps/search/?api=1&query=456+Nguyen+Van+Linh',
}

export const policy: ReservationPolicy = {
  timezone: 'Asia/Ho_Chi_Minh',
  today: '2026-10-29',
  last_bookable_date: '2026-11-01',
  max_guests: 10,
  opening_time: '10:00:00',
  last_seating_time: '21:00:00',
}

export function order(overrides: Partial<Order> = {}): Order {
  const id = overrides.id ?? 1048
  return {
    id,
    status: 'PENDING',
    payment_method: 'COD',
    payment_status: 'UNPAID',
    subtotal_price: 475_000,
    discount_amount: 0,
    promo_code: null,
    total_price: 475_000,
    created_at: '2026-10-29T11:42:00Z',
    location: district1,
    delivery_name: 'Nguyen Van A',
    delivery_phone: '0901234567',
    delivery_address: '12 Nguyễn Huệ, Quận 1',
    delivery_note: '',
    items: [
      {
        product_id: springRolls.id,
        product_name: springRolls.name,
        product_slug: springRolls.slug,
        image_url: springRolls.image_url,
        thumbnail_url: springRolls.thumbnail_url,
        price_at_purchase: springRolls.price,
        quantity: 2,
        subtotal: springRolls.price * 2,
      },
    ],
    events: [
      {
        from_status: null,
        to_status: 'PENDING',
        actor: 'customer',
        note: '',
        created_at: '2026-10-29T11:42:00Z',
      },
    ],
    can_cancel: true,
    can_pay: true,
    ...overrides,
  }
}

export function reservation(overrides: Partial<Reservation> = {}): Reservation {
  return {
    id: 1,
    location: district1,
    customer_name: 'Nguyen Van A',
    customer_phone: '0901234567',
    reservation_date: '2026-10-31',
    reservation_time: '19:00:00',
    guest_count: 4,
    special_requests: '',
    status: 'PENDING',
    created_at: '2026-10-29T10:00:00Z',
    cancelled_at: null,
    can_cancel: true,
    ...overrides,
  }
}

export function review(overrides: Partial<Review> = {}): Review {
  return {
    id: nextId++,
    rating: 5,
    comment: 'Rất ngon.',
    created_at: '2026-10-29T03:00:00Z',
    user_name: 'Tran Thi B',
    verified_purchase: true,
    reply: null,
    replied_at: null,
    photos: [],
    ...overrides,
  }
}

/** One page of a dish's reviews; the summary counts `all`, which defaults to the page. */
export function reviewPage(items: Review[], { all = items, totalPages = 1 } = {}): ReviewPage {
  const average = all.length ? all.reduce((sum, r) => sum + r.rating, 0) / all.length : null
  return {
    items,
    page: 1,
    page_size: 5,
    total: items.length,
    total_pages: totalPages,
    summary: {
      average: average === null ? null : average.toFixed(2),
      count: all.length,
      distribution: [5, 4, 3, 2, 1].map((stars) => ({
        stars,
        count: all.filter((r) => r.rating === stars).length,
      })),
    },
  }
}
