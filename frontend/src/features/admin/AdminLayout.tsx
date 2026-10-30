import { NavLink, Outlet } from 'react-router'
import { EmptyView } from '@/components/ui/StatusView'
import { RequireAuth } from '@/features/auth/RequireAuth'
import { useI18n } from '@/i18n/context'
import styles from './AdminLayout.module.css'

const SECTIONS = [
  { to: '/admin', key: 'dashboard', end: true },
  { to: '/admin/orders', key: 'orders', end: false },
  { to: '/admin/reservations', key: 'reservations', end: false },
  { to: '/admin/products', key: 'products', end: false },
  { to: '/admin/users', key: 'users', end: false },
  { to: '/admin/promo-codes', key: 'promos', end: false },
  { to: '/admin/reports', key: 'reports', end: false },
  { to: '/admin/audit', key: 'audit', end: false },
] as const

/** Every admin page: signed-in admins only, with the section tabs above the page. */
export function AdminLayout() {
  const { t } = useI18n()
  return (
    <RequireAuth>
      {(user) =>
        user.role !== 'ADMIN' ? (
          <div className="page">
            <EmptyView title={t.admin.forbiddenTitle}>
              <p>{t.admin.forbiddenBody}</p>
            </EmptyView>
          </div>
        ) : (
          <div className="page">
            <p className="kicker">{t.admin.kicker}</p>
            <nav aria-label={t.admin.navLabel} className={styles.tabs}>
              {SECTIONS.map((section) => (
                <NavLink key={section.key} to={section.to} end={section.end} className={styles.tab}>
                  {t.admin.sections[section.key]}
                </NavLink>
              ))}
            </nav>
            <Outlet />
          </div>
        )
      }
    </RequireAuth>
  )
}
