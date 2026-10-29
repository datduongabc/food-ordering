import { useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router'
import { Badge } from '@/components/ui/Badge'
import { ButtonLink } from '@/components/ui/Button'
import { EmptyView, ErrorView, Loading } from '@/components/ui/StatusView'
import { useI18n } from '@/i18n/context'
import { formatDateTime, formatVnd, interpolate } from '@/lib/format'
import { orderQueries } from '../api'
import { ORDER_TONE } from '../status'
import { OrderDetail } from './OrderDetail'
import styles from './OrdersPanel.module.css'

export function OrdersPanel() {
  const { t, lang } = useI18n()
  const [params, setParams] = useSearchParams()
  const orders = useQuery(orderQueries.list())
  const detailRef = useRef<HTMLElement>(null)

  if (orders.error) return <ErrorView error={orders.error} onRetry={() => orders.refetch()} />
  if (!orders.data) return <Loading />
  if (orders.data.length === 0) {
    return (
      <EmptyView title={t.account.noOrdersTitle}>
        <p>{t.account.noOrdersBody}</p>
        <ButtonLink to="/menu">{t.cart.browse}</ButtonLink>
      </EmptyView>
    )
  }

  const requested = Number(params.get('order'))
  const selected = orders.data.find((order) => order.id === requested) ?? orders.data[0]!

  return (
    <div className={styles.layout}>
      <ul className={styles.list} aria-label={t.account.ordersTab}>
        {orders.data.map((order) => {
          const count = order.items.reduce((sum, item) => sum + item.quantity, 0)
          return (
            <li key={order.id}>
              <button
                type="button"
                className={styles.item}
                aria-pressed={order.id === selected.id}
                onClick={() => {
                  setParams({ order: String(order.id) }, { replace: true })
                  // On narrow screens the detail sits below the list, out of sight.
                  if (window.matchMedia('(max-width: 900px)').matches) {
                    detailRef.current?.scrollIntoView({ block: 'start' })
                  }
                }}
              >
                <span className={styles.itemHead}>
                  <strong className={styles.itemId}>#{order.id}</strong>
                  <Badge tone={ORDER_TONE[order.status]}>{t.orderStatus[order.status]}</Badge>
                </span>
                <span className={styles.itemMeta}>
                  {formatDateTime(order.created_at, lang)} ·{' '}
                  {interpolate(t.account.orderCount, { count })}
                </span>
                <strong>{formatVnd(order.total_price)}</strong>
              </button>
            </li>
          )
        })}
      </ul>
      <OrderDetail key={selected.id} ref={detailRef} order={selected} />
    </div>
  )
}
