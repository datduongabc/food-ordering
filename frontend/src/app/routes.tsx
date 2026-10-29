import type { ComponentType } from 'react'
import type { RouteObject } from 'react-router'
import { SiteLayout } from '@/components/layout/SiteLayout'
import { HomePage } from '@/features/home/HomePage'
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
      }),
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]
