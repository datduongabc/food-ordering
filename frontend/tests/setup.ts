import '@testing-library/jest-dom/vitest'
import { act, cleanup, waitFor } from '@testing-library/react'
import { afterAll, afterEach, beforeAll } from 'vitest'
import { renderedClients } from './support/render'
import { server } from './support/server'

// jsdom has no layout, so it does not implement scrolling; the app scrolls on navigation.
window.scrollTo = () => {}
// Nor media queries; tests run as the wide desktop layout.
window.matchMedia = (query: string) =>
  ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => false,
  }) satisfies MediaQueryList

// MSW only logs requests nobody mocked; collecting them lets afterEach fail the test, so a page
// can never silently depend on an endpoint the test did not set up.
const unhandled: string[] = []

beforeAll(() =>
  server.listen({
    onUnhandledFrame: ({ frame, defaults }) => {
      const { data } = frame
      const request =
        data instanceof Object && 'request' in data && data.request instanceof Request
          ? data.request
          : undefined
      unhandled.push(
        request ? `${request.method} ${new URL(request.url).pathname}` : String(frame.protocol),
      )
      defaults.error()
    },
  }),
)
afterEach(async () => {
  // A request still in flight would otherwise land in the next test, after its handlers reset.
  // Flushing effects first starts any query the last render scheduled.
  await act(() => Promise.resolve())
  await waitFor(() => {
    for (const client of renderedClients) {
      if (client.isFetching() + client.isMutating() > 0) throw new Error('Requests still running')
    }
  })
  renderedClients.clear()
  cleanup()
  const missing = unhandled.splice(0)
  if (missing.length > 0) throw new Error(`Unmocked API calls: ${missing.join(', ')}`)
  server.resetHandlers()
  window.localStorage.clear()
  document.cookie.split('; ').forEach((cookie) => {
    const name = cookie.split('=')[0]
    if (name) document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`
  })
})
afterAll(() => server.close())
