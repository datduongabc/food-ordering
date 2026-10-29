import { render } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { Providers } from '@/app/Providers'
import { createQueryClient } from '@/app/queryClient'
import { routes } from '@/app/routes'
import type { Lang } from '@/i18n/dictionary'

/** Renders the real route tree at `path`, exactly as the app would. */
export function renderApp(path: string, { lang = 'vi' as Lang } = {}) {
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  const queryClient = createQueryClient()
  queryClient.setDefaultOptions({
    queries: { ...queryClient.getDefaultOptions().queries, retry: false },
  })
  const view = render(
    <Providers queryClient={queryClient} lang={lang}>
      <RouterProvider router={router} />
    </Providers>,
  )
  return { ...view, router, queryClient }
}
