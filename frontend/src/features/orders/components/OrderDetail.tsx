import { useState, type Ref } from 'react'
import { Badge } from '@/components/ui/Badge'
import { Button, ButtonLink } from '@/components/ui/Button'
import { useToast } from '@/components/ui/toastContext'
import type { Dictionary } from '@/i18n/dictionary'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { useLocalize } from '@/i18n/useLocalize'
import { formatDateTime, formatVnd, interpolate } from '@/lib/format'
import { useCancelOrder } from '../api'
import type { Order, OrderEvent } from '../schemas'
import { ORDER_TONE, PAYMENT_TONE } from '../status'
import styles from './OrderDetail.module.css'

/** The customer-facing wording of one status change; staff names stay internal. */
function eventLabel(event: OrderEvent, t: Dictionary): string {
  const labels = t.account.events
  switch (event.to_status) {
    case 'PENDING':
      return labels.placed
    case 'CONFIRMED':
      return event.actor === 'system' ? labels.paidConfirmed : labels.confirmed
    case 'COMPLETED':
      return labels.completed
    case 'CANCELLED':
      return event.actor === 'customer' ? labels.cancelledByYou : labels.cancelledByStaff
  }
}

export function OrderDetail({ order, ref }: { order: Order; ref?: Ref<HTMLElement> }) {
  const { t, lang } = useI18n()
  const localize = useLocalize()
  const toast = useToast()
  const errorMessage = useErrorMessage()
  const cancel = useCancelOrder()
  const [confirming, setConfirming] = useState(false)
  const titleId = `order-${order.id}-title`

  return (
    <section ref={ref} aria-labelledby={titleId} className={styles.detail}>
      <div className={styles.head}>
        <div className={styles.headText}>
          <h2 id={titleId} className={styles.title}>
            {interpolate(t.account.orderTitle, { id: order.id })}
          </h2>
          <span className={styles.muted}>{formatDateTime(order.created_at, lang)}</span>
        </div>
        <Badge tone={ORDER_TONE[order.status]} size="lg">
          {t.orderStatus[order.status]}
        </Badge>
      </div>

      <div className={styles.boxes}>
        <div className={styles.box}>
          <span className={styles.boxLabel}>{t.account.deliverTo}</span>
          <strong>
            {order.delivery_name} · {order.delivery_phone}
          </strong>
          <span className={styles.boxText}>{order.delivery_address}</span>
          {order.delivery_note && (
            <span className={styles.boxText}>
              {interpolate(t.account.note, { note: order.delivery_note })}
            </span>
          )}
        </div>
        <div className={styles.box}>
          <span className={styles.boxLabel}>{t.account.payment}</span>
          <strong>{t.paymentMethod[order.payment_method]}</strong>
          <Badge tone={PAYMENT_TONE[order.payment_status]}>
            {t.paymentStatus[order.payment_status]}
          </Badge>
        </div>
        <div className={styles.box}>
          <span className={styles.boxLabel}>{t.account.branch}</span>
          <strong>{order.location ? localize(order.location.name) : t.account.noBranch}</strong>
        </div>
      </div>

      <ul className={styles.items}>
        {order.items.map((item) => (
          <li key={item.product_id} className={styles.item}>
            <img src={item.image_url} alt="" className={styles.thumb} />
            <span className={styles.itemName}>
              {localize(item.product_name)} <span className={styles.muted}>× {item.quantity}</span>
            </span>
            <strong>{formatVnd(item.subtotal)}</strong>
          </li>
        ))}
      </ul>
      <div className={styles.total}>
        <strong>{t.account.total}</strong>
        <strong className={styles.totalValue}>{formatVnd(order.total_price)}</strong>
      </div>

      <div className={styles.timeline}>
        <h3 className={styles.timelineTitle}>{t.account.timeline}</h3>
        <ol className={styles.events}>
          {order.events.map((event) => (
            <li key={`${event.to_status}-${event.created_at}`} className={styles.event}>
              <span aria-hidden="true" className={styles.rail}>
                <span className={styles.dot} data-status={event.to_status} />
                <span className={styles.line} />
              </span>
              <span className={styles.eventText}>
                <strong>{eventLabel(event, t)}</strong>
                <span className={styles.eventWhen}>{formatDateTime(event.created_at, lang)}</span>
                {event.note && (
                  <span className={styles.eventNote}>
                    {interpolate(t.account.staffNote, { note: event.note })}
                  </span>
                )}
              </span>
            </li>
          ))}
        </ol>
      </div>

      {confirming ? (
        <div role="alertdialog" aria-labelledby={`${titleId}-cancel`} className={styles.confirm}>
          <strong id={`${titleId}-cancel`} className={styles.confirmText}>
            {interpolate(
              order.payment_status === 'PAID'
                ? t.account.cancelPaidQuestion
                : t.account.cancelQuestion,
              { id: order.id },
            )}
          </strong>
          <div className={styles.actions}>
            <Button
              disabled={cancel.isPending}
              onClick={() =>
                cancel.mutate(order.id, {
                  onSuccess: () => {
                    setConfirming(false)
                    toast(interpolate(t.account.cancelled, { id: order.id }))
                  },
                  onError: (error) => toast(errorMessage(error)),
                })
              }
            >
              {t.account.yesCancel}
            </Button>
            <Button variant="outline" onClick={() => setConfirming(false)}>
              {t.account.keep}
            </Button>
          </div>
        </div>
      ) : (
        (order.can_pay || order.can_cancel) && (
          <div className={styles.actions}>
            {order.can_pay && (
              <ButtonLink to={`/orders/${order.id}/pay`} variant="momo">
                {/* A cash order can still be paid online; starting the payment switches it. */}
                {order.payment_method === 'COD' ? t.account.switchToMomo : t.account.payNow}
              </ButtonLink>
            )}
            {order.can_cancel && (
              <Button variant="danger" onClick={() => setConfirming(true)}>
                {t.account.cancelOrder}
              </Button>
            )}
          </div>
        )
      )}
      {order.status === 'CONFIRMED' && <p className={styles.muted}>{t.account.lockedNote}</p>}
    </section>
  )
}
