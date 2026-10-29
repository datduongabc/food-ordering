import { useQuery } from '@tanstack/react-query'
import { useLocation } from 'react-router'
import { ButtonLink } from '@/components/ui/Button'
import { Stars } from '@/components/ui/Stars'
import { ErrorView, Loading } from '@/components/ui/StatusView'
import { useCurrentUser } from '@/features/auth/queries'
import { useI18n } from '@/i18n/context'
import { formatDate } from '@/lib/format'
import { reviewQueries } from '../queries'
import { ReviewForm } from './ReviewForm'
import styles from './ReviewSection.module.css'

export function ReviewSection({ slug }: { slug: string }) {
  const { t, lang } = useI18n()
  const user = useCurrentUser()
  const location = useLocation()
  const reviews = useQuery(reviewQueries.forProduct(slug))

  return (
    <section id="reviews" aria-labelledby="reviews-title" className={styles.section}>
      <div className={styles.list}>
        <span className="kicker">{t.reviews.kicker}</span>
        <h2 id="reviews-title" className={styles.title}>
          {t.reviews.title}
        </h2>
        {reviews.isPending ? (
          <Loading />
        ) : reviews.isError ? (
          <ErrorView error={reviews.error} onRetry={() => void reviews.refetch()} />
        ) : reviews.data.length === 0 ? (
          <p className={styles.empty}>{t.reviews.empty}</p>
        ) : (
          <ul className={styles.items}>
            {reviews.data.map((review) => (
              <li key={review.id} className={styles.review}>
                <div className={styles.meta}>
                  <strong>{review.user_name}</strong>
                  <time dateTime={review.created_at} className={styles.date}>
                    {formatDate(review.created_at, lang)}
                  </time>
                </div>
                <Stars rating={review.rating} />
                <p className={styles.comment}>{review.comment}</p>
              </li>
            ))}
          </ul>
        )}
      </div>

      <aside className={styles.aside}>
        {user ? (
          <ReviewForm slug={slug} />
        ) : (
          <div className={styles.signIn}>
            <h3 className={styles.asideTitle}>{t.reviews.write}</h3>
            <p>{t.reviews.signInToReview}</p>
            <ButtonLink
              to={`/login?next=${encodeURIComponent(location.pathname + '#reviews')}`}
              variant="dark"
            >
              {t.nav.signIn}
            </ButtonLink>
          </div>
        )}
      </aside>
    </section>
  )
}
