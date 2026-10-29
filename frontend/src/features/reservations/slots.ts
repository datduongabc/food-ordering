import type { ReservationPolicy } from './schemas'

const SLOT_MINUTES = 30

function toMinutes(time: string): number {
  const [hours = 0, minutes = 0] = time.split(':').map(Number)
  return hours * 60 + minutes
}

function toTime(minutes: number): string {
  const pad = (value: number) => String(value).padStart(2, '0')
  return `${pad(Math.floor(minutes / 60))}:${pad(minutes % 60)}`
}

/** Calendar days from today to the last bookable day, as YYYY-MM-DD. */
export function bookableDates(policy: ReservationPolicy): string[] {
  const dates: string[] = []
  const day = new Date(`${policy.today}T00:00:00Z`)
  const last = new Date(`${policy.last_bookable_date}T00:00:00Z`)
  while (day <= last) {
    dates.push(day.toISOString().slice(0, 10))
    day.setUTCDate(day.getUTCDate() + 1)
  }
  return dates
}

/** Current HH:MM at the restaurant, whatever the visitor's own time zone. */
export function restaurantClock(policy: ReservationPolicy, now = new Date()): string {
  return new Intl.DateTimeFormat('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
    timeZone: policy.timezone,
  }).format(now)
}

/** Half-hour seatings on `date`, leaving out ones already past when `date` is today. */
export function timeSlots(policy: ReservationPolicy, date: string, clock: string): string[] {
  const first = toMinutes(policy.opening_time)
  const last = toMinutes(policy.last_seating_time)
  const after = date === policy.today ? toMinutes(clock) : -1
  const slots: string[] = []
  for (let minutes = first; minutes <= last; minutes += SLOT_MINUTES) {
    if (minutes > after) slots.push(toTime(minutes))
  }
  return slots
}
