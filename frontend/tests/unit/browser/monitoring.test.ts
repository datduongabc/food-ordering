import { beforeEach, describe, expect, it, vi } from 'vitest'

const sentry = vi.hoisted(() => ({ init: vi.fn(), captureException: vi.fn() }))
vi.mock('@sentry/react', () => sentry)

describe('monitoring', () => {
  beforeEach(() => {
    vi.resetModules()
    sentry.init.mockClear()
    sentry.captureException.mockClear()
  })

  it('stays off without a DSN, and reporting is then a no-op', async () => {
    const { startMonitoring, reportError } = await import('@/lib/monitoring')
    await startMonitoring('')
    reportError(new Error('ignored'))

    expect(sentry.init).not.toHaveBeenCalled()
    expect(sentry.captureException).not.toHaveBeenCalled()
  })

  it('sends errors to Sentry without personal data once started', async () => {
    const { startMonitoring, reportError } = await import('@/lib/monitoring')
    await startMonitoring('https://key@o1.ingest.sentry.io/1')
    const error = new Error('boom')
    reportError(error)

    expect(sentry.init).toHaveBeenCalledWith(
      expect.objectContaining({ dsn: 'https://key@o1.ingest.sentry.io/1', sendDefaultPii: false }),
    )
    expect(sentry.captureException).toHaveBeenCalledWith(error)
  })
})
