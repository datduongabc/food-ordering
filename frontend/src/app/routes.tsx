import type { RouteObject } from 'react-router'
import { SiteLayout } from '@/components/layout/SiteLayout'
import { HomePage } from '@/features/home/HomePage'
import { NotFoundPage } from '@/pages/NotFoundPage'

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
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]
