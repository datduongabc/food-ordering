import { NavLink, useSearchParams } from 'react-router'
import { useI18n } from '@/i18n/context'
import styles from './AuthForm.module.css'

/** Sign in / sign up switch; keeps ?next so either way returns the customer where they were. */
export function AuthTabs() {
  const { t } = useI18n()
  const [params] = useSearchParams()
  const search = params.get('next') ? `?next=${encodeURIComponent(params.get('next') ?? '')}` : ''
  const className = ({ isActive }: { isActive: boolean }) =>
    isActive ? `${styles.tab} ${styles.tabActive}` : styles.tab
  return (
    <nav aria-label={t.auth.tabsLabel} className={styles.tabs}>
      <NavLink to={`/login${search}`} className={className} replace>
        {t.auth.login}
      </NavLink>
      <NavLink to={`/register${search}`} className={className} replace>
        {t.auth.register}
      </NavLink>
    </nav>
  )
}
