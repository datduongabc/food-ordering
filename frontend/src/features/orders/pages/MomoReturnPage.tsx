import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router'
import { ButtonLink } from '@/components/ui/Button'
import { Loading } from '@/components/ui/StatusView'
import { RequireAuth } from '@/features/auth/RequireAuth'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { orderQueries } from '../api'
import { FailedOutcome, NoticeOutcome, PaidOutcome } from '../components/PaymentOutcome'
import styles from './PaymentPage.module.css'

/** Where MoMo sends the customer back, with the signed payment result in the query string. */
export function MomoReturnPage() {
  return <RequireAuth>{() => <MomoReturn />}</RequireAuth>
}

function MomoReturn() {
  const { t } = useI18n()
  const errorMessage = useErrorMessage()
  const [searchParams] = useSearchParams()
  const result = useQuery(orderQueries.momoReturn(Object.fromEntries(searchParams)))

  let body
  if (result.isPending) {
    body = <Loading label={t.payment.checking} />
  } else if (result.error) {
    body = <NoticeOutcome title={t.payment.returnErrorTitle} body={errorMessage(result.error)} />
  } else {
    const order = result.data
    if (order.payment_status === 'PAID') {
      body = <PaidOutcome orderId={order.id} amount={order.total_price} />
    } else if (order.payment_status === 'FAILED') {
      body = (
        <FailedOutcome
          orderId={order.id}
          retry={
            order.can_pay && (
              <ButtonLink to={`/orders/${order.id}/pay`} variant="momo" size="lg">
                {t.payment.retry}
              </ButtonLink>
            )
          }
        />
      )
    } else {
      body = (
        <NoticeOutcome
          title={t.payment.pendingTitle}
          body={t.payment.pendingBody}
          orderId={order.id}
        />
      )
    }
  }

  return <div className={styles.page}>{body}</div>
}
