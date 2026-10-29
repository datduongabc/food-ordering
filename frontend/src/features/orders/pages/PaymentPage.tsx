import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router'
import { Button, ButtonLink } from '@/components/ui/Button'
import { Loading } from '@/components/ui/StatusView'
import { RequireAuth } from '@/features/auth/RequireAuth'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { formatVnd, interpolate } from '@/lib/format'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { orderQueries, useCompleteSandboxPayment } from '../api'
import { SandboxQr } from '../components/SandboxQr'
import styles from './PaymentPage.module.css'

export function PaymentPage() {
  const { id } = useParams()
  const orderId = Number(id)
  if (!Number.isInteger(orderId) || orderId <= 0) return <NotFoundPage />
  return <RequireAuth>{() => <MomoSandbox orderId={orderId} />}</RequireAuth>
}

function MomoSandbox({ orderId }: { orderId: number }) {
  const { t } = useI18n()
  const errorMessage = useErrorMessage()
  const attempt = useQuery(orderQueries.momo(orderId))
  const complete = useCompleteSandboxPayment()
  const [result, setResult] = useState<'paid' | 'failed'>()
  const orderLink = `/account?order=${orderId}`

  function finish(outcome: 'approved' | 'declined', momoOrderId: string) {
    complete.mutate(
      { momo_order_id: momoOrderId, result: outcome },
      { onSuccess: () => setResult(outcome === 'approved' ? 'paid' : 'failed') },
    )
  }

  let body
  if (attempt.isPending) {
    body = <Loading />
  } else if (attempt.error) {
    body = (
      <section className={`${styles.outcome} ${styles.failed}`}>
        <span aria-hidden="true" className={`${styles.icon} ${styles.iconFailed}`}>
          !
        </span>
        <h1 className={styles.outcomeTitle}>{t.payment.unavailableTitle}</h1>
        <p className={styles.outcomeBody}>{errorMessage(attempt.error)}</p>
        <ButtonLink to={orderLink} size="lg">
          {t.payment.viewOrder}
        </ButtonLink>
      </section>
    )
  } else if (result === 'paid') {
    body = (
      <section className={`${styles.outcome} ${styles.paid}`}>
        <span aria-hidden="true" className={`${styles.icon} ${styles.iconPaid}`}>
          ✓
        </span>
        <p className={styles.paidKicker}>{t.payment.paidKicker}</p>
        <h1 className={styles.outcomeTitle}>{interpolate(t.payment.paidTitle, { id: orderId })}</h1>
        <p className={styles.outcomeBody}>
          {interpolate(t.payment.paidBody, { amount: formatVnd(attempt.data.amount) })}
        </p>
        <ButtonLink to={orderLink} size="lg">
          {t.payment.viewOrder}
        </ButtonLink>
      </section>
    )
  } else if (result === 'failed') {
    body = (
      <section className={`${styles.outcome} ${styles.failed}`}>
        <span aria-hidden="true" className={`${styles.icon} ${styles.iconFailed}`}>
          !
        </span>
        <h1 className={styles.outcomeTitle}>{t.payment.failedTitle}</h1>
        <p className={styles.outcomeBody}>{t.payment.failedBody}</p>
        <div className={styles.actions}>
          <Button
            variant="momo"
            size="lg"
            onClick={async () => {
              // MoMo rejects a reused order id, so a retry starts a fresh attempt.
              await attempt.refetch()
              setResult(undefined)
            }}
            disabled={attempt.isFetching}
          >
            {t.payment.retry}
          </Button>
          <ButtonLink to={orderLink} variant="outline" size="lg">
            {t.payment.later}
          </ButtonLink>
        </div>
      </section>
    )
  } else {
    const { momo_order_id: momoOrderId, amount } = attempt.data
    body = (
      <div className={styles.pending}>
        <section className={styles.details}>
          <div className={styles.heading}>
            <span aria-hidden="true" className={styles.momoMark}>
              mo
            </span>
            <h1 className={styles.title}>{t.payment.title}</h1>
          </div>
          <dl className={styles.facts}>
            <dt>{t.payment.merchant}</dt>
            <dd>DaTeNO</dd>
            <dt>{t.payment.orderNo}</dt>
            <dd>#{orderId}</dd>
            <dt>{t.payment.content}</dt>
            <dd>{interpolate(t.payment.contentValue, { id: orderId })}</dd>
          </dl>
          <div className={styles.amount}>
            <span>{t.payment.amount}</span>
            <strong>{formatVnd(amount)}</strong>
          </div>
        </section>
        <section className={styles.approve}>
          <p className={styles.scan}>{t.payment.scan}</p>
          <SandboxQr label={t.payment.qrLabel} className={styles.qr} />
          {complete.error && (
            <p role="alert" className={styles.error}>
              {errorMessage(complete.error)}
            </p>
          )}
          <Button
            variant="momo"
            size="lg"
            block
            disabled={complete.isPending}
            onClick={() => finish('approved', momoOrderId)}
          >
            {t.payment.approve}
          </Button>
          <Button
            variant="outline"
            size="lg"
            block
            disabled={complete.isPending}
            onClick={() => finish('declined', momoOrderId)}
          >
            {t.payment.decline}
          </Button>
        </section>
      </div>
    )
  }

  return (
    <>
      <p role="note" className={styles.sandbox}>
        {t.payment.sandbox}
      </p>
      <div className={styles.page}>{body}</div>
    </>
  )
}
