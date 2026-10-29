import { useI18n } from '@/i18n/context'
import { interpolate } from '@/lib/format'
import styles from './Pagination.module.css'

interface Props {
  page: number
  totalPages: number
  onChange: (page: number) => void
}

export function Pagination({ page, totalPages, onChange }: Props) {
  const { t } = useI18n()
  const pages = Array.from({ length: totalPages }, (_, index) => index + 1)

  return (
    <nav aria-label={t.menu.pages} className={styles.pagination}>
      <button
        type="button"
        className={styles.button}
        aria-label={t.menu.prev}
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
      >
        ‹
      </button>
      {pages.map((number) => (
        <button
          key={number}
          type="button"
          className={styles.button}
          aria-label={interpolate(t.menu.page, { page: number })}
          aria-current={number === page ? 'page' : undefined}
          onClick={() => onChange(number)}
        >
          {number}
        </button>
      ))}
      <button
        type="button"
        className={styles.button}
        aria-label={t.menu.next}
        disabled={page >= totalPages}
        onClick={() => onChange(page + 1)}
      >
        ›
      </button>
    </nav>
  )
}
