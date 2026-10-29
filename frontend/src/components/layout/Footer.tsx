import { useQuery } from '@tanstack/react-query'
import { catalogQueries } from '@/features/catalog/queries'
import { useI18n } from '@/i18n/context'
import styles from './Footer.module.css'

export function Footer() {
  const { t } = useI18n()
  const { data: locations } = useQuery(catalogQueries.locations())

  return (
    <footer id="branches" className={styles.footer}>
      <h2 className="visually-hidden">{t.nav.branches}</h2>
      <div className={styles.branches}>
        {locations?.map((location) => (
          <div key={location.id} className={styles.branch}>
            <span className={styles.name}>{location.name}</span>
            <p className={styles.address}>{location.address}</p>
            {/* Google Maps refuses to render inside a frame, so it always opens a new tab. */}
            <a
              href={location.map_url}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.directions}
            >
              {t.footer.directions} →
              <span className="visually-hidden">
                {' '}
                {location.name} {t.common.opensNewTab}
              </span>
            </a>
          </div>
        ))}
      </div>
      <p className={styles.copyright}>{t.footer.copyright}</p>
    </footer>
  )
}
