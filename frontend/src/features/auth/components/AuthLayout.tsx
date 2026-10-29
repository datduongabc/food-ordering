import type { ReactNode } from 'react'
import { useI18n } from '@/i18n/context'
import styles from './AuthLayout.module.css'

/** The welcome column plus a card, shared by every account screen. */
export function AuthLayout({ children }: { children: ReactNode }) {
  const { t } = useI18n()
  const perks = [t.auth.perks.orders, t.auth.perks.bookings, t.auth.perks.cart]
  return (
    <div className={`page ${styles.layout}`}>
      <section className={styles.side}>
        <span className={styles.kicker}>{t.auth.sideKicker}</span>
        <p className={styles.title}>{t.auth.sideTitle}</p>
        <ul className={styles.perks}>
          {perks.map((perk) => (
            <li key={perk}>
              <span aria-hidden="true" className={styles.check}>
                ✓
              </span>
              <span>{perk}</span>
            </li>
          ))}
        </ul>
      </section>
      <section className={styles.card}>{children}</section>
    </div>
  )
}
