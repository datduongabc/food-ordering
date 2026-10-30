import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { describe, expect, it, vi } from 'vitest'
import { Providers } from '@/app/Providers'
import { createQueryClient } from '@/app/queryClient'
import { startMonitoring } from '@/lib/monitoring'
import { ErrorPage } from '@/pages/ErrorPage'

const sentry = vi.hoisted(() => ({ init: vi.fn(), captureException: vi.fn() }))
vi.mock('@sentry/react', () => sentry)

function Broken(): never {
  throw new Error('render failed')
}

describe('error page', () => {
  it('replaces a crashed page with a way out and reports the error', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    await startMonitoring('https://key@o1.ingest.sentry.io/1')
    const reload = vi.fn()
    vi.spyOn(window, 'location', 'get').mockReturnValue({ ...window.location, reload })
    const router = createMemoryRouter([
      { path: '/', element: <Broken />, errorElement: <ErrorPage /> },
    ])
    render(
      <Providers queryClient={createQueryClient()}>
        <RouterProvider router={router} />
      </Providers>,
    )

    expect(await screen.findByText('Đã có lỗi xảy ra')).toBeInTheDocument()
    await waitFor(() =>
      expect(sentry.captureException).toHaveBeenCalledWith(
        expect.objectContaining({ message: 'render failed' }),
      ),
    )
    await userEvent.click(screen.getByRole('button', { name: 'Tải lại trang' }))
    expect(reload).toHaveBeenCalled()
    vi.restoreAllMocks()
  })
})
