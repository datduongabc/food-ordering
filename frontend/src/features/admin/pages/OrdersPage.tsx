import { useRef, useState, type Ref } from 'react'
import { useQuery } from '@tanstack/react-query'
import { TextAreaField } from '@/components/form/TextAreaField'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { EmptyView, ErrorView, Loading } from '@/components/ui/StatusView'
import { useToast } from '@/components/ui/toastContext'
import { Pagination } from '@/features/catalog/components/Pagination'
import detail from '@/features/orders/components/OrderDetail.module.css'
import list from '@/features/orders/components/OrdersPanel.module.css'
import { OrderTotals } from '@/features/orders/components/OrderTotals'
import { ORDER_STATUSES, type OrderStatus } from '@/features/orders/schemas'
import { ORDER_TONE, PAYMENT_TONE } from '@/features/orders/status'
import type { Dictionary } from '@/i18n/dictionary'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { useLocalize } from '@/i18n/useLocalize'
import { formatDateTime, formatVnd, interpolate } from '@/lib/format'
import { adminQueries, useChangeOrderStatus } from '../api'
import { FilterChips } from '../components/FilterChips'
import type { AdminOrder } from '../schemas'
import { oneOf, useUrlFilters } from '../useUrlFilters'
import shared from '../admin.module.css'

// Mirrors the API's ORDER_TRANSITIONS, so staff are only offered moves it will accept.
const NEXT: Record<OrderStatus, readonly ('CONFIRMED' | 'COMPLETED' | 'CANCELLED')[]> = {
  PENDING: ['CONFIRMED', 'CANCELLED'],
  CONFIRMED: ['COMPLETED', 'CANCELLED'],
  COMPLETED: [],
  CANCELLED: [],
}

export function AdminOrdersPage() {
  const { t, lang } = useI18n()
  const { params, page, update } = useUrlFilters()
  const status = oneOf(ORDER_STATUSES, params.get('status'))
  const orders = useQuery(adminQueries.orders({ status, page }))
  const detailRef = useRef<HTMLElement>(null)

  let body
  if (orders.error) {
    body = <ErrorView error={orders.error} onRetry={() => orders.refetch()} />
  } else if (!orders.data) {
    body = <Loading />
  } else if (orders.data.items.length === 0) {
    body = <EmptyView title={t.admin.noResults}>{t.admin.orders.empty}</EmptyView>
  } else {
    const items = orders.data.items
    const requested = Number(params.get('order'))
    const selected = items.find((order) => order.id === requested) ?? items[0]!
    body = (
      <>
        <div className={list.layout}>
          <ul className={list.list} aria-label={t.admin.orders.title}>
            {items.map((order) => (
              <li key={order.id}>
                <button
                  type="button"
                  className={list.item}
                  aria-pressed={order.id === selected.id}
                  onClick={() => {
                    update({ order: String(order.id), page: String(page) })
                    if (window.matchMedia('(max-width: 900px)').matches) {
                      detailRef.current?.scrollIntoView({ block: 'start' })
                    }
                  }}
                >
                  <span className={list.itemHead}>
                    <strong className={list.itemId}>#{order.id}</strong>
                    <Badge tone={ORDER_TONE[order.status]}>{t.orderStatus[order.status]}</Badge>
                  </span>
                  <span>{order.customer.name}</span>
                  <span className={list.itemMeta}>
                    {formatDateTime(order.created_at, lang)} ·{' '}
                    {t.paymentMethod[order.payment_method]}
                  </span>
                  <strong>{formatVnd(order.total_price)}</strong>
                </button>
              </li>
            ))}
          </ul>
          <AdminOrderDetail key={selected.id} ref={detailRef} order={selected} />
        </div>
        {orders.data.total_pages > 1 && (
          <div className={shared.pager}>
            <Pagination
              page={page}
              totalPages={orders.data.total_pages}
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
        <h1 className={shared.title}>{t.admin.orders.title}</h1>
        {orders.data && (
          <span className={shared.count}>
            {interpolate(t.admin.total, { count: orders.data.total })}
          </span>
        )}
      </div>
      <div className={shared.filters}>
        <FilterChips
          label={t.admin.status}
          options={[
            { value: undefined, label: t.admin.all },
            ...ORDER_STATUSES.map((value) => ({ value, label: t.orderStatus[value] ?? value })),
          ]}
          value={status}
          onChange={(value) => update({ status: value, order: undefined })}
        />
      </div>
      {body}
    </>
  )
}

function actorLabel(event: AdminOrder['events'][number], t: Dictionary): string {
  if (event.actor === 'staff') return event.actor_name ?? t.admin.kicker
  return event.actor === 'customer' ? t.admin.orders.byCustomer : t.admin.orders.bySystem
}

function AdminOrderDetail({ order, ref }: { order: AdminOrder; ref?: Ref<HTMLElement> }) {
  const { t, lang } = useI18n()
  const labels = t.admin.orders
  const localize = useLocalize()
  const toast = useToast()
  const errorMessage = useErrorMessage()
  const change = useChangeOrderStatus()
  const [note, setNote] = useState('')
  const [confirmingCancel, setConfirmingCancel] = useState(false)
  const titleId = `admin-order-${order.id}-title`
  const next = NEXT[order.status]

  function move(status: (typeof next)[number]) {
    change.mutate(
      { id: order.id, status, note: note.trim() },
      {
        onSuccess: () => {
          setNote('')
          setConfirmingCancel(false)
          toast(interpolate(labels.changed, { id: order.id, status: t.orderStatus[status] ?? '' }))
        },
        onError: (error) => toast(errorMessage(error)),
      },
    )
  }

  return (
    <section ref={ref} aria-labelledby={titleId} className={detail.detail}>
      <div className={detail.head}>
        <div className={detail.headText}>
          <h2 id={titleId} className={detail.title}>
            {interpolate(t.account.orderTitle, { id: order.id })}
          </h2>
          <span className={detail.muted}>{formatDateTime(order.created_at, lang)}</span>
        </div>
        <Badge tone={ORDER_TONE[order.status]} size="lg">
          {t.orderStatus[order.status]}
        </Badge>
      </div>

      <div className={detail.boxes}>
        <div className={detail.box}>
          <span className={detail.boxLabel}>{labels.customer}</span>
          <strong>{order.customer.name}</strong>
          <span className={detail.boxText}>
            {order.customer.email} · {order.customer.phone}
          </span>
        </div>
        <div className={detail.box}>
          <span className={detail.boxLabel}>{t.account.deliverTo}</span>
          <strong>
            {order.delivery_name} · {order.delivery_phone}
          </strong>
          <span className={detail.boxText}>{order.delivery_address}</span>
          {order.delivery_note && (
            <span className={detail.boxText}>
              {interpolate(t.account.note, { note: order.delivery_note })}
            </span>
          )}
        </div>
        <div className={detail.box}>
          <span className={detail.boxLabel}>{t.account.payment}</span>
          <strong>{t.paymentMethod[order.payment_method]}</strong>
          <Badge tone={PAYMENT_TONE[order.payment_status]}>
            {t.paymentStatus[order.payment_status]}
          </Badge>
          {order.momo_order_id && (
            <span className={detail.boxText}>
              {interpolate(labels.momoIds, {
                order: order.momo_order_id,
                trans: order.momo_trans_id ?? labels.noTransaction,
              })}
            </span>
          )}
        </div>
        <div className={detail.box}>
          <span className={detail.boxLabel}>{t.account.branch}</span>
          <strong>{order.location ? localize(order.location.name) : t.account.noBranch}</strong>
        </div>
      </div>

      <ul className={detail.items}>
        {order.items.map((item) => (
          <li key={item.product_id} className={detail.item}>
            <img src={item.thumbnail_url} alt="" className={detail.thumb} />
            <span className={detail.itemName}>
              {localize(item.product_name)} <span className={detail.muted}>× {item.quantity}</span>
            </span>
            <strong>{formatVnd(item.subtotal)}</strong>
          </li>
        ))}
      </ul>
      <OrderTotals order={order} />

      <div className={detail.timeline}>
        <h3 className={detail.timelineTitle}>{t.account.timeline}</h3>
        <ol className={detail.events}>
          {order.events.map((event) => (
            <li key={`${event.to_status}-${event.created_at}`} className={detail.event}>
              <span aria-hidden="true" className={detail.rail}>
                <span className={detail.dot} data-status={event.to_status} />
                <span className={detail.line} />
              </span>
              <span className={detail.eventText}>
                <strong>
                  {t.orderStatus[event.to_status]} · {actorLabel(event, t)}
                </strong>
                <span className={detail.eventWhen}>{formatDateTime(event.created_at, lang)}</span>
                {event.note && <span className={detail.eventNote}>{event.note}</span>}
              </span>
            </li>
          ))}
        </ol>
      </div>

      {next.length === 0 ? (
        <p className={detail.muted}>{labels.closed}</p>
      ) : (
        <div className={shared.cellStack}>
          <h3 className={detail.timelineTitle}>{labels.changeTitle}</h3>
          <TextAreaField
            label={labels.note}
            placeholder={labels.notePlaceholder}
            maxLength={500}
            value={note}
            onChange={(event) => setNote(event.target.value)}
          />
          {confirmingCancel ? (
            <div
              role="alertdialog"
              aria-labelledby={`${titleId}-cancel`}
              className={detail.confirm}
            >
              <strong id={`${titleId}-cancel`} className={detail.confirmText}>
                {interpolate(
                  order.payment_status === 'PAID'
                    ? t.account.cancelPaidQuestion
                    : t.account.cancelQuestion,
                  { id: order.id },
                )}
              </strong>
              {order.payment_status === 'PAID' && order.payment_method === 'MOMO' && (
                <span>{labels.refundNote}</span>
              )}
              <div className={detail.actions}>
                <Button disabled={change.isPending} onClick={() => move('CANCELLED')}>
                  {t.account.yesCancel}
                </Button>
                <Button variant="outline" onClick={() => setConfirmingCancel(false)}>
                  {t.account.keep}
                </Button>
              </div>
            </div>
          ) : (
            <div className={detail.actions}>
              {next.map((status) =>
                status === 'CANCELLED' ? (
                  <Button key={status} variant="danger" onClick={() => setConfirmingCancel(true)}>
                    {labels.to.CANCELLED}
                  </Button>
                ) : (
                  <Button
                    key={status}
                    variant={status === 'COMPLETED' ? 'green' : 'primary'}
                    disabled={change.isPending}
                    onClick={() => move(status)}
                  >
                    {labels.to[status]}
                  </Button>
                ),
              )}
            </div>
          )}
        </div>
      )}
    </section>
  )
}
