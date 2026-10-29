import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { apiError, mockApi, mockLayout, recordCalls } from '../support/api'
import { customer, district1, reservation } from '../support/fixtures'
import { renderApp } from '../support/render'

function mockHome() {
  mockApi('get', '/products/featured', null)
  mockApi('get', '/products', { items: [], page: 1, page_size: 5, total: 0, total_pages: 0 })
  mockApi('get', '/reviews/top', [])
}

/** Freezes the clock at a restaurant-local time on the policy's "today", 2026-10-29. */
function atRestaurantTime(hhmm: string) {
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date(`2026-10-29T${hhmm}:00+07:00`))
}

afterEach(() => {
  vi.useRealTimers()
})

async function bookingForm() {
  const section = await screen.findByRole('region', { name: 'Đặt bàn' })
  await within(section).findByLabelText('Giờ')
  return section
}

function options(select: HTMLElement) {
  return within(select)
    .getAllByRole('option')
    .map((option) => option.textContent)
}

describe('booking a table', () => {
  it('offers only later seatings today and every seating on later days', async () => {
    const user = userEvent.setup()
    atRestaurantTime('18:15')
    mockLayout()
    mockHome()
    renderApp('/')

    const form = await bookingForm()
    expect(within(form).getByRole('radio', { name: /29/ })).toBeChecked()
    const time = within(form).getByLabelText('Giờ')
    expect(options(time)).toEqual(['18:30', '19:00', '19:30', '20:00', '20:30', '21:00'])
    expect(time).toHaveValue('19:00')

    await user.click(within(form).getByRole('radio', { name: /30/ }))
    expect(options(time)[0]).toBe('10:00')
    expect(options(time).at(-1)).toBe('21:00')
  })

  it('skips today once the last seating has passed', async () => {
    atRestaurantTime('21:10')
    mockLayout()
    mockHome()
    renderApp('/')

    const form = await bookingForm()
    expect(within(form).getByRole('radio', { name: /29/ })).toBeDisabled()
    expect(within(form).getByRole('radio', { name: /30/ })).toBeChecked()
  })

  it('books for a signed-in customer with their details filled in', async () => {
    const user = userEvent.setup()
    atRestaurantTime('09:00')
    mockLayout({ signedIn: customer })
    mockHome()
    const calls = recordCalls([
      'post',
      '/reservations',
      reservation({ reservation_date: '2026-10-30', reservation_time: '12:30:00', guest_count: 4 }),
      201,
    ])
    renderApp('/')

    const form = await bookingForm()
    expect(within(form).getByLabelText('Họ và tên')).toHaveValue(customer.name)
    await user.click(within(form).getByRole('radio', { name: /30/ }))
    await user.selectOptions(within(form).getByLabelText('Giờ'), '12:30')
    await user.selectOptions(within(form).getByLabelText('Số khách'), '4')
    await user.type(within(form).getByLabelText('Yêu cầu thêm (không bắt buộc)'), 'Ghế trẻ em')
    await user.click(within(form).getByRole('button', { name: 'Xác nhận đặt bàn' }))

    expect(await within(form).findByText('Cảm ơn quý khách!')).toBeInTheDocument()
    expect(calls[0]?.body).toEqual({
      reservation_date: '2026-10-30',
      reservation_time: '12:30',
      guest_count: 4,
      location_id: district1.id,
      customer_name: customer.name,
      customer_phone: customer.phone,
      special_requests: 'Ghế trẻ em',
    })
    expect(within(form).getByText(/12:30 · 4 khách · DaTeNO - Quận 1/)).toBeInTheDocument()
    expect(within(form).getByRole('link', { name: 'Xem lịch đặt bàn' })).toHaveAttribute(
      'href',
      '/account?tab=bookings',
    )
  })

  it('asks guests for contact details and shows server rules under the field', async () => {
    const user = userEvent.setup()
    atRestaurantTime('09:00')
    mockLayout()
    mockHome()
    mockApi(
      'post',
      '/reservations',
      apiError('outside_opening_hours', { opening: '10:00', last_seating: '21:00' }),
      400,
    )
    renderApp('/')

    const form = await bookingForm()
    await user.click(within(form).getByRole('button', { name: 'Xác nhận đặt bàn' }))
    expect(within(form).getByLabelText('Họ và tên')).toHaveAccessibleDescription(
      'Vui lòng nhập thông tin này.',
    )

    await user.type(within(form).getByLabelText('Họ và tên'), 'Khách lẻ')
    await user.type(within(form).getByLabelText('Số điện thoại'), '0901 234 567')
    await user.click(within(form).getByRole('button', { name: 'Xác nhận đặt bàn' }))
    expect(await within(form).findByText('Nhà hàng nhận đặt bàn từ 10:00 đến 21:00.')).toBeVisible()
  })
})

describe('account bookings', () => {
  it('lists bookings and cancels a pending one', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: customer })
    mockApi('get', '/reservations/mine', [
      reservation({ id: 1, special_requests: 'Sinh nhật' }),
      reservation({
        id: 2,
        status: 'COMPLETED',
        can_cancel: false,
        reservation_date: '2026-10-12',
      }),
    ])
    mockApi(
      'post',
      '/reservations/1/cancel',
      reservation({ id: 1, status: 'CANCELLED', can_cancel: false, special_requests: 'Sinh nhật' }),
    )
    renderApp('/account?tab=bookings')

    expect(await screen.findByText('Yêu cầu: Sinh nhật')).toBeInTheDocument()
    expect(screen.getByText('Đã đến')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Đặt bàn', current: 'page' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Hủy đặt bàn' }))
    expect(await screen.findByText('Đã hủy lịch đặt bàn.')).toBeInTheDocument()
    expect(screen.getByText('Đã hủy')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Hủy đặt bàn' })).not.toBeInTheDocument()
  })
})
