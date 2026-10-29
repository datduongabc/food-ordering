import { useQuery } from '@tanstack/react-query'
import { Badge, type BadgeTone } from '@/components/ui/Badge'
import { Button, ButtonLink } from '@/components/ui/Button'
import { EmptyView, ErrorView, Loading } from '@/components/ui/StatusView'
import { useToast } from '@/components/ui/toastContext'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { useLocalize } from '@/i18n/useLocalize'
import { formatClock, formatDayParts, interpolate } from '@/lib/format'
import { reservationQueries, useCancelReservation } from '../api'
import type { Reservation } from '../schemas'
import styles from './BookingsPanel.module.css'

const TONE: Record<Reservation['status'], BadgeTone> = {
  PENDING: 'amber',
  CONFIRMED: 'blue',
  COMPLETED: 'green',
  CANCELLED: 'stone',
}

export function BookingsPanel() {
  const { t, lang } = useI18n()
  const localize = useLocalize()
  const toast = useToast()
  const errorMessage = useErrorMessage()
  const bookings = useQuery(reservationQueries.mine())
  const cancel = useCancelReservation()

  return (
    <div className={styles.panel}>
      <div className={styles.intro}>
        <p className={styles.muted}>{t.account.bookingHint}</p>
        <ButtonLink to="/#book" variant="green">
          {t.account.newBooking}
        </ButtonLink>
      </div>

      {bookings.error ? (
        <ErrorView error={bookings.error} onRetry={() => bookings.refetch()} />
      ) : !bookings.data ? (
        <Loading />
      ) : bookings.data.length === 0 ? (
        <EmptyView title={t.account.noBookingsTitle} />
      ) : (
        <ul className={styles.list}>
          {bookings.data.map((booking) => {
            const day = formatDayParts(booking.reservation_date, lang)
            return (
              <li key={booking.id} className={styles.booking}>
                <span className={styles.tile} aria-hidden="true">
                  <span className={styles.tileSmall}>{day.weekday}</span>
                  <span className={styles.tileDay}>{day.day}</span>
                  <span className={styles.tileSmall}>{day.month}</span>
                </span>
                <div className={styles.info}>
                  <strong className={styles.when}>
                    <span className="visually-hidden">{day.full}, </span>
                    {formatClock(booking.reservation_time)} ·{' '}
                    {interpolate(t.account.guests, { count: booking.guest_count })}
                  </strong>
                  <span className={styles.muted}>{localize(booking.location.name)}</span>
                  {booking.special_requests && (
                    <span className={styles.requests}>
                      {interpolate(t.account.requests, { text: booking.special_requests })}
                    </span>
                  )}
                </div>
                <div className={styles.side}>
                  <Badge tone={TONE[booking.status]}>{t.reservationStatus[booking.status]}</Badge>
                  {booking.can_cancel && (
                    <Button
                      variant="danger"
                      disabled={cancel.isPending}
                      onClick={() =>
                        cancel.mutate(booking.id, {
                          onSuccess: () => toast(t.account.bookingCancelled),
                          onError: (error) => toast(errorMessage(error)),
                        })
                      }
                    >
                      {t.account.cancelBooking}
                    </Button>
                  )}
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
