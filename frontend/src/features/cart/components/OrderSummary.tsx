import type { ReactNode } from 'react'
import { useI18n } from '@/i18n/context'
import { formatVnd, interpolate } from '@/lib/format'
import styles from './OrderSummary.module.css'

/** The yellow-shadowed total card shared by the cart and checkout. */
export function OrderSummary({
  title,
  subtotal,
  discount,
  lines,
  children,
}: {
  title: string
  subtotal: number
  discount?: { code: string; amount: number }
  lines?: ReactNode
  children?: ReactNode
}) {
  const { t } = useI18n()
  return (
    <aside className={styles.summary} aria-labelledby="order-summary-title">
      <h2 id="order-summary-title" className={styles.title}>
        {title}
      </h2>
      {lines}
      <dl className={styles.rows}>
        <div className={styles.row}>
          <dt>{t.cart.subtotal}</dt>
          <dd>
            <strong>{formatVnd(subtotal)}</strong>
          </dd>
        </div>
        {discount && (
          <div className={`${styles.row} ${styles.discount}`}>
            <dt>{interpolate(t.cart.discount, { code: discount.code })}</dt>
            <dd>−{formatVnd(discount.amount)}</dd>
          </div>
        )}
        <div className={`${styles.row} ${styles.muted}`}>
          <dt>{t.cart.delivery}</dt>
          <dd>{t.cart.free}</dd>
        </div>
        <div className={`${styles.row} ${styles.total}`}>
          <dt>{t.cart.total}</dt>
          <dd>{formatVnd(subtotal - (discount?.amount ?? 0))}</dd>
        </div>
      </dl>
      {children}
    </aside>
  )
}
