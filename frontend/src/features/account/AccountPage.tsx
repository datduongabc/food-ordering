import { Link, useSearchParams } from 'react-router'
import { RequireAuth } from '@/features/auth/RequireAuth'
import { useI18n } from '@/i18n/context'
import { interpolate } from '@/lib/format'
import { BookingsPanel } from '@/features/reservations/components/BookingsPanel'
import { OrdersPanel } from '@/features/orders/components/OrdersPanel'
import styles from './AccountPage.module.css'

export function AccountPage() {
  const { t } = useI18n()
  const [params] = useSearchParams()
  const tab = params.get('tab') === 'bookings' ? 'bookings' : 'orders'

  return (
    <RequireAuth>
      {(user) => (
        <div className="page">
          <p className="kicker">{interpolate(t.account.hello, { name: user.name })}</p>
          <h1 className={styles.title}>{t.account.title}</h1>
          <nav aria-label={t.account.tabsLabel} className={styles.tabs}>
            <Link
              to="/account"
              className={styles.tab}
              aria-current={tab === 'orders' ? 'page' : undefined}
            >
              {t.account.ordersTab}
            </Link>
            <Link
              to="/account?tab=bookings"
              className={styles.tab}
              aria-current={tab === 'bookings' ? 'page' : undefined}
            >
              {t.account.bookingsTab}
            </Link>
          </nav>
          {tab === 'orders' ? <OrdersPanel /> : <BookingsPanel />}
        </div>
      )}
    </RequireAuth>
  )
}
