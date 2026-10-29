import type { JsonBodyType } from 'msw'
import { http, HttpResponse } from 'msw/http'
import { cartOf, district1, mains, policy, starters } from './fixtures'
import { server } from './server'

type Method = 'get' | 'post' | 'put' | 'delete'

/** Answers one endpoint with fixed JSON (and status) for the rest of the test. */
export function mockApi(method: Method, path: string, body: JsonBodyType, status = 200) {
  server.use(http[method](`*/api${path}`, () => HttpResponse.json(body, { status })))
}

export function apiError(code: string, params: Record<string, unknown> = {}) {
  return { detail: `English detail for ${code}`, code, params }
}

/** The calls the layout (and the home page's booking form) make: session, cart, branches. */
export function mockLayout({ signedIn = null as JsonBodyType } = {}) {
  // The client calls /health to obtain a CSRF cookie before its first unsafe request.
  server.use(
    http.get('*/api/health', () => {
      document.cookie = 'dateno_csrf=test-token; path=/'
      return HttpResponse.json({ status: 'ok' })
    }),
  )
  if (signedIn) mockApi('get', '/auth/me', signedIn)
  else mockApi('get', '/auth/me', apiError('auth_required'), 401)
  mockApi('get', '/locations', [district1])
  mockApi('get', '/categories', [starters, mains])
  mockApi('get', '/cart', cartOf())
  mockApi('get', '/reservations/policy', policy)
}

/** Records the JSON body of each call to these endpoints, in order. */
export function recordCalls(...handlers: [string, string, unknown, number?][]) {
  const calls: { path: string; body: unknown }[] = []
  for (const [method, path, response, status = 200] of handlers) {
    server.use(
      http[method as 'post'](`*/api${path}`, async ({ request }) => {
        const text = await request.text()
        calls.push({ path, body: text ? JSON.parse(text) : null })
        return HttpResponse.json(response as never, { status })
      }),
    )
  }
  return calls
}
