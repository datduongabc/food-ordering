import { render } from '@testing-library/react'
import type { QueryClient } from '@tanstack/react-query'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { Providers } from '@/app/Providers'
import { createQueryClient } from '@/app/queryClient'
import { routes } from '@/app/routes'
import type { Lang } from '@/i18n/dictionary'

/** Clients of apps rendered in the current test, so teardown can wait for their requests. */
export const renderedClients = new Set<QueryClient>()

/** Renders the real route tree at `path`, exactly as the app would. */
export function renderApp(path: string, { lang = 'vi' as Lang } = {}) {
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  const queryClient = createQueryClient()
  queryClient.setDefaultOptions({
    queries: { ...queryClient.getDefaultOptions().queries, retry: false },
  })
  renderedClients.add(queryClient)
  const view = render(
    <Providers queryClient={queryClient} lang={lang}>
      <RouterProvider router={router} />
    </Providers>,
  )
  return { ...view, router, queryClient }
}
