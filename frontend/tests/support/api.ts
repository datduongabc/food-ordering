import type { JsonBodyType } from 'msw'
import { http, HttpResponse } from 'msw/http'
import { cartOf, district1, mains, starters } from './fixtures'
import { server } from './server'

type Method = 'get' | 'post' | 'put' | 'delete'

/** Answers one endpoint with fixed JSON (and status) for the rest of the test. */
export function mockApi(method: Method, path: string, body: JsonBodyType, status = 200) {
  server.use(http[method](`*/api${path}`, () => HttpResponse.json(body, { status })))
}

export function apiError(code: string, params: Record<string, unknown> = {}) {
  return { detail: `English detail for ${code}`, code, params }
}

/** The calls every page makes through the layout: session check, cart, branches. */
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
}
