import { useI18n } from '@/i18n/context'
import { formatVnd, interpolate } from '@/lib/format'
import type { Order } from '../schemas'
import styles from './OrderDetail.module.css'

/** What the dishes came to, any promo discount, and what is owed: for customers and staff. */
export function OrderTotals({ order }: { order: Order }) {
  const { t } = useI18n()
  return (
    <dl className={styles.totals}>
      {order.discount_amount > 0 && (
        <>
          <div className={styles.subRow}>
            <dt>{t.account.subtotal}</dt>
            <dd>{formatVnd(order.subtotal_price)}</dd>
          </div>
          <div className={`${styles.subRow} ${styles.discount}`}>
            <dt>{interpolate(t.account.discount, { code: order.promo_code ?? '' })}</dt>
            <dd>−{formatVnd(order.discount_amount)}</dd>
          </div>
        </>
      )}
      <div className={styles.total}>
        <dt>
          <strong>{t.account.total}</strong>
        </dt>
        <dd>
          <strong className={styles.totalValue}>{formatVnd(order.total_price)}</strong>
        </dd>
      </div>
    </dl>
  )
}
