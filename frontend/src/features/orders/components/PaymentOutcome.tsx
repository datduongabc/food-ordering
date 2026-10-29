import type { ReactNode } from 'react'
import { ButtonLink } from '@/components/ui/Button'
import { useI18n } from '@/i18n/context'
import { formatVnd, interpolate } from '@/lib/format'
import styles from '../pages/PaymentPage.module.css'

function orderLink(orderId: number) {
  return `/account?order=${orderId}`
}

export function PaidOutcome({ orderId, amount }: { orderId: number; amount: number }) {
  const { t } = useI18n()
  return (
    <section className={`${styles.outcome} ${styles.paid}`}>
      <span aria-hidden="true" className={`${styles.icon} ${styles.iconPaid}`}>
        ✓
      </span>
      <p className={styles.paidKicker}>{t.payment.paidKicker}</p>
      <h1 className={styles.outcomeTitle}>{interpolate(t.payment.paidTitle, { id: orderId })}</h1>
      <p className={styles.outcomeBody}>
        {interpolate(t.payment.paidBody, { amount: formatVnd(amount) })}
      </p>
      <ButtonLink to={orderLink(orderId)} size="lg">
        {t.payment.viewOrder}
      </ButtonLink>
    </section>
  )
}

/** A payment that did not go through; `retry` starts another attempt. */
export function FailedOutcome({ orderId, retry }: { orderId: number; retry: ReactNode }) {
  const { t } = useI18n()
  return (
    <section className={`${styles.outcome} ${styles.failed}`}>
      <span aria-hidden="true" className={`${styles.icon} ${styles.iconFailed}`}>
        !
      </span>
      <h1 className={styles.outcomeTitle}>{t.payment.failedTitle}</h1>
      <p className={styles.outcomeBody}>{t.payment.failedBody}</p>
      <div className={styles.actions}>
        {retry}
        <ButtonLink to={orderLink(orderId)} variant="outline" size="lg">
          {t.payment.later}
        </ButtonLink>
      </div>
    </section>
  )
}

/** Something to tell the customer, with the way back to their orders. */
export function NoticeOutcome({
  title,
  body,
  orderId,
}: {
  title: string
  body: string
  orderId?: number
}) {
  const { t } = useI18n()
  return (
    <section className={`${styles.outcome} ${styles.failed}`}>
      <span aria-hidden="true" className={`${styles.icon} ${styles.iconFailed}`}>
        !
      </span>
      <h1 className={styles.outcomeTitle}>{title}</h1>
      <p className={styles.outcomeBody}>{body}</p>
      <ButtonLink to={orderId ? orderLink(orderId) : '/account'} size="lg">
        {t.payment.viewOrder}
      </ButtonLink>
    </section>
  )
}
