import { Outlet, ScrollRestoration } from 'react-router'
import { useI18n } from '@/i18n/context'
import { Footer } from './Footer'
import { Header } from './Header'
import styles from './SiteLayout.module.css'

export function SiteLayout() {
  const { t } = useI18n()
  return (
    <div className={styles.shell}>
      <a href="#main" className={styles.skip}>
        {t.common.skipToContent}
      </a>
      <Header />
      <main id="main" className={styles.main}>
        <Outlet />
      </main>
      <Footer />
      <ScrollRestoration />
    </div>
  )
}
