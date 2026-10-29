import { useI18n } from '@/i18n/context'
import { interpolate } from '@/lib/format'
import styles from './Stars.module.css'

/** Read-only star rating; `rating` may be fractional (an average) or null (no reviews). */
export function Stars({ rating }: { rating: number | null }) {
  const { t } = useI18n()
  const filled = rating === null ? 0 : Math.round(rating)
  const label =
    rating === null
      ? t.common.noReviews
      : interpolate(t.common.ratingOutOf, { rating: rating.toFixed(1).replace(/\.0$/, '') })
  return (
    <span role="img" aria-label={label} className={styles.stars}>
      {'★'.repeat(filled)}
      <span className={styles.empty}>{'★'.repeat(5 - filled)}</span>
    </span>
  )
}
