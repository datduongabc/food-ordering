import { useQuery } from '@tanstack/react-query'
import { TextField } from '@/components/form/TextField'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { EmptyView, ErrorView, Loading } from '@/components/ui/StatusView'
import { useToast } from '@/components/ui/toastContext'
import { Pagination } from '@/features/catalog/components/Pagination'
import { ORDER_TONE } from '@/features/orders/status'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { useLocalize } from '@/i18n/useLocalize'
import { formatClock, formatDayParts, interpolate } from '@/lib/format'
import { adminQueries, useChangeReservationStatus } from '../api'
import { FilterChips } from '../components/FilterChips'
import { RESERVATION_STATUSES, type AdminReservation, type ReservationStatus } from '../schemas'
import { oneOf, useUrlFilters } from '../useUrlFilters'
import shared from '../admin.module.css'

// Mirrors the API's RESERVATION_TRANSITIONS.
const NEXT: Record<ReservationStatus, readonly ('CONFIRMED' | 'COMPLETED' | 'CANCELLED')[]> = {
  PENDING: ['CONFIRMED', 'CANCELLED'],
  CONFIRMED: ['COMPLETED', 'CANCELLED'],
  COMPLETED: [],
  CANCELLED: [],
}

export function AdminReservationsPage() {
  const { t } = useI18n()
  const labels = t.admin.reservations
  const { params, page, update } = useUrlFilters()
  const status = oneOf(RESERVATION_STATUSES, params.get('status'))
  const date = /^\d{4}-\d{2}-\d{2}$/.test(params.get('date') ?? '')
    ? params.get('date')!
    : undefined
  const reservations = useQuery(adminQueries.reservations({ status, date, page }))

  let body
  if (reservations.error) {
    body = <ErrorView error={reservations.error} onRetry={() => reservations.refetch()} />
  } else if (!reservations.data) {
    body = <Loading />
  } else if (reservations.data.items.length === 0) {
    body = <EmptyView title={t.admin.noResults}>{labels.empty}</EmptyView>
  } else {
    body = (
      <>
        <div className={shared.tableWrap}>
          <table className={shared.table}>
            <thead>
              <tr>
                <th scope="col">#</th>
                <th scope="col">{labels.when}</th>
                <th scope="col">{labels.guest}</th>
                <th scope="col">{labels.branch}</th>
                <th scope="col">{t.admin.status}</th>
                <th scope="col">{t.admin.actions}</th>
              </tr>
            </thead>
            <tbody>
              {reservations.data.items.map((reservation) => (
                <ReservationRow key={reservation.id} reservation={reservation} />
              ))}
            </tbody>
          </table>
        </div>
        {reservations.data.total_pages > 1 && (
          <div className={shared.pager}>
            <Pagination
              page={page}
              totalPages={reservations.data.total_pages}
              onChange={(next) => update({ page: String(next) })}
            />
          </div>
        )}
      </>
    )
  }

  return (
    <>
      <div className={shared.head}>
        <h1 className={shared.title}>{labels.title}</h1>
        {reservations.data && (
          <span className={shared.count}>
            {interpolate(t.admin.total, { count: reservations.data.total })}
          </span>
        )}
      </div>
      <div className={shared.filters}>
        <FilterChips
          label={t.admin.status}
          options={[
            { value: undefined, label: t.admin.all },
            ...RESERVATION_STATUSES.map((value) => ({
              value,
              label: t.reservationStatus[value],
            })),
          ]}
          value={status}
          onChange={(value) => update({ status: value })}
        />
        <TextField
          label={labels.date}
          type="date"
          value={date ?? ''}
          onChange={(event) => update({ date: event.target.value })}
        />
        {date && (
          <Button variant="outline" onClick={() => update({ date: undefined })}>
            {labels.clearDate}
          </Button>
        )}
      </div>
      {body}
    </>
  )
}

function ReservationRow({ reservation }: { reservation: AdminReservation }) {
  const { t, lang } = useI18n()
  const labels = t.admin.reservations
  const localize = useLocalize()
  const toast = useToast()
  const errorMessage = useErrorMessage()
  const change = useChangeReservationStatus()

  return (
    <tr>
      <td data-label="#">{reservation.id}</td>
      <td data-label={labels.when}>
        <div className={shared.cellStack}>
          <strong>{formatClock(reservation.reservation_time)}</strong>
          <span className={shared.muted}>
            {formatDayParts(reservation.reservation_date, lang).full}
          </span>
        </div>
      </td>
      <td data-label={labels.guest}>
        <div className={shared.cellStack}>
          <strong>{reservation.customer_name}</strong>
          <span className={shared.muted}>
            {reservation.customer_phone} ·{' '}
            {interpolate(labels.guests, { count: reservation.guest_count })}
          </span>
          {reservation.special_requests && (
            <span>{interpolate(t.account.requests, { text: reservation.special_requests })}</span>
          )}
        </div>
      </td>
      <td data-label={labels.branch}>{localize(reservation.location.name)}</td>
      <td data-label={t.admin.status}>
        <Badge tone={ORDER_TONE[reservation.status]}>
          {t.reservationStatus[reservation.status]}
        </Badge>
      </td>
      <td data-label={t.admin.actions}>
        <div className={shared.rowActions}>
          {NEXT[reservation.status].map((status) => (
            <Button
              key={status}
              className={shared.small}
              variant={
                status === 'CANCELLED' ? 'danger' : status === 'COMPLETED' ? 'green' : 'primary'
              }
              disabled={change.isPending}
              onClick={() =>
                change.mutate(
                  { id: reservation.id, status },
                  {
                    onSuccess: () =>
                      toast(
                        interpolate(labels.changed, {
                          id: reservation.id,
                          status: t.reservationStatus[status],
                        }),
                      ),
                    onError: (error) => toast(errorMessage(error)),
                  },
                )
              }
            >
              {labels.to[status]}
            </Button>
          ))}
        </div>
      </td>
    </tr>
  )
}
