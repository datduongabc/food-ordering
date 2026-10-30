import type { ComponentType } from 'react'
import type { RouteObject } from 'react-router'
import { SiteLayout } from '@/components/layout/SiteLayout'
import { HomePage } from '@/features/home/HomePage'
import { ErrorPage } from '@/pages/ErrorPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

function lazyPages(pages: Record<string, () => Promise<ComponentType>>): RouteObject[] {
  return Object.entries(pages).map(([path, load]) => ({
    path,
    lazy: async () => ({ Component: await load() }),
  }))
}

// The home page ships in the main bundle; other pages load on first visit.
export const routes: RouteObject[] = [
  {
    element: <SiteLayout />,
    errorElement: <ErrorPage />,
    children: [
      { index: true, element: <HomePage /> },
      {
        path: 'menu',
        lazy: async () => ({
          Component: (await import('@/features/catalog/pages/MenuPage')).MenuPage,
        }),
      },
      {
        path: 'menu/:slug',
        lazy: async () => ({
          Component: (await import('@/features/catalog/pages/DishPage')).DishPage,
        }),
      },
      ...lazyPages({
        login: () => import('@/features/auth/pages/LoginPage').then((m) => m.LoginPage),
        register: () => import('@/features/auth/pages/RegisterPage').then((m) => m.RegisterPage),
        'verify-email': () =>
          import('@/features/auth/pages/VerifyEmailPage').then((m) => m.VerifyEmailPage),
        'forgot-password': () =>
          import('@/features/auth/pages/ForgotPasswordPage').then((m) => m.ForgotPasswordPage),
        'reset-password': () =>
          import('@/features/auth/pages/ResetPasswordPage').then((m) => m.ResetPasswordPage),
        cart: () => import('@/features/cart/pages/CartPage').then((m) => m.CartPage),
        checkout: () => import('@/features/orders/pages/CheckoutPage').then((m) => m.CheckoutPage),
        'orders/:id/pay': () =>
          import('@/features/orders/pages/PaymentPage').then((m) => m.PaymentPage),
        'payment/momo/return': () =>
          import('@/features/orders/pages/MomoReturnPage').then((m) => m.MomoReturnPage),
        account: () => import('@/features/account/AccountPage').then((m) => m.AccountPage),
      }),
      {
        path: 'admin',
        lazy: async () => ({
          Component: (await import('@/features/admin/AdminLayout')).AdminLayout,
        }),
        children: [
          {
            index: true,
            lazy: async () => ({
              Component: (await import('@/features/admin/pages/DashboardPage')).DashboardPage,
            }),
          },
          ...lazyPages({
            orders: () =>
              import('@/features/admin/pages/OrdersPage').then((m) => m.AdminOrdersPage),
            reservations: () =>
              import('@/features/admin/pages/ReservationsPage').then(
                (m) => m.AdminReservationsPage,
              ),
            products: () =>
              import('@/features/admin/pages/ProductsPage').then((m) => m.AdminProductsPage),
            'products/new': () =>
              import('@/features/admin/pages/ProductEditPage').then((m) => m.ProductEditPage),
            'products/:id': () =>
              import('@/features/admin/pages/ProductEditPage').then((m) => m.ProductEditPage),
            users: () => import('@/features/admin/pages/UsersPage').then((m) => m.AdminUsersPage),
          }),
        ],
      },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]
