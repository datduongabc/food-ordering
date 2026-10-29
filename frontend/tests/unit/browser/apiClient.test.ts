import { http, HttpResponse } from 'msw/http'
import { describe, expect, it } from 'vitest'
import { z } from 'zod'
import { api, ApiError, ContractError } from '@/lib/api/client'
import { server } from '../../support/server'

const ok = z.object({ ok: z.boolean() })

describe('api client', () => {
  it('echoes the CSRF cookie in a header on unsafe requests', async () => {
    document.cookie = 'dateno_csrf=token-123; path=/'
    let header: string | null = null
    server.use(
      http.post('*/api/thing', ({ request }) => {
        header = request.headers.get('X-CSRF-Token')
        return HttpResponse.json({ ok: true })
      }),
    )

    await api.post('/thing', ok, {})

    expect(header).toBe('token-123')
  })

  it('fetches a CSRF cookie first when the visitor has none yet', async () => {
    const calls: string[] = []
    server.use(
      http.get('*/api/health', () => {
        calls.push('health')
        document.cookie = 'dateno_csrf=fresh; path=/'
        return HttpResponse.json({ status: 'ok' })
      }),
      http.post('*/api/thing', ({ request }) => {
        calls.push(`post:${request.headers.get('X-CSRF-Token')}`)
        return HttpResponse.json({ ok: true })
      }),
    )

    await api.post('/thing', ok, {})

    expect(calls).toEqual(['health', 'post:fresh'])
  })

  it('turns error bodies into ApiError with code and params', async () => {
    server.use(
      http.get('*/api/thing', () =>
        HttpResponse.json(
          { detail: 'Try again in 3 minute(s).', code: 'login_locked', params: { minutes: 3 } },
          { status: 429 },
        ),
      ),
    )

    const error = await api.get('/thing', ok).catch((caught: unknown) => caught)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 429, code: 'login_locked', params: { minutes: 3 } })
  })

  it('rejects responses that do not match the expected shape', async () => {
    server.use(http.get('*/api/thing', () => HttpResponse.json({ ok: 'yes' })))
    await expect(api.get('/thing', ok)).rejects.toBeInstanceOf(ContractError)
  })

  it('drops empty query params', async () => {
    let url = ''
    server.use(
      http.get('*/api/thing', ({ request }) => {
        url = request.url
        return HttpResponse.json({ ok: true })
      }),
    )
    await api.get('/thing', ok, { page: 2, category: undefined, q: '' })
    expect(new URL(url).search).toBe('?page=2')
  })
})
