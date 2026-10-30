import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useLocation } from 'react-router'
import { ButtonLink } from '@/components/ui/Button'
import { Stars } from '@/components/ui/Stars'
import { ErrorView, Loading } from '@/components/ui/StatusView'
import { useCurrentUser } from '@/features/auth/queries'
import { Pagination } from '@/features/catalog/components/Pagination'
import { useI18n } from '@/i18n/context'
import { formatDate, interpolate } from '@/lib/format'
import { reviewQueries } from '../queries'
import { REVIEW_SORTS, type Review, type ReviewPage, type ReviewSort } from '../schemas'
import { ReviewForm } from './ReviewForm'
import styles from './ReviewSection.module.css'

export function ReviewSection({ slug }: { slug: string }) {
  const { t } = useI18n()
  const user = useCurrentUser()
  const location = useLocation()
  const [page, setPage] = useState(1)
  const [rating, setRating] = useState<number>()
  const [sort, setSort] = useState<ReviewSort>('newest')
  const reviews = useQuery(reviewQueries.forProduct(slug, { page, rating, sort }))

  function filter(stars: number | undefined) {
    setRating(stars)
    setPage(1)
  }

  let body
  if (reviews.isPending) {
    body = <Loading />
  } else if (reviews.isError) {
    body = <ErrorView error={reviews.error} onRetry={() => void reviews.refetch()} />
  } else if (reviews.data.summary.count === 0) {
    body = <p className={styles.empty}>{t.reviews.empty}</p>
  } else {
    const data = reviews.data
    body = (
      <>
        <Summary data={data} selected={rating} onSelect={filter} />
        <div className={styles.controls}>
          <div role="group" aria-label={t.reviews.filterLabel} className={styles.chips}>
            {[undefined, 5, 4, 3, 2, 1].map((stars) => (
              <button
                key={stars ?? 'all'}
                type="button"
                className={styles.chip}
                aria-pressed={rating === stars}
                onClick={() => filter(stars)}
              >
                {stars === undefined
                  ? t.reviews.allStars
                  : interpolate(t.reviews.starsShort, { stars })}
              </button>
            ))}
          </div>
          <label className={styles.sort}>
            {t.reviews.sortLabel}
            <select
              value={sort}
              onChange={(event) => {
                setSort(event.target.value as ReviewSort)
                setPage(1)
              }}
            >
              {REVIEW_SORTS.map((option) => (
                <option key={option} value={option}>
                  {t.reviews.sorts[option]}
                </option>
              ))}
            </select>
          </label>
        </div>
        {data.items.length === 0 ? (
          <p className={styles.empty}>{interpolate(t.reviews.noMatch, { stars: rating ?? '' })}</p>
        ) : (
          <ul className={styles.items}>
            {data.items.map((review) => (
              <ReviewItem key={review.id} review={review} />
            ))}
          </ul>
        )}
        {data.total_pages > 1 && (
          <Pagination page={page} totalPages={data.total_pages} onChange={setPage} />
        )}
      </>
    )
  }

  return (
    <section id="reviews" aria-labelledby="reviews-title" className={styles.section}>
      <div className={styles.list}>
        <span className="kicker">{t.reviews.kicker}</span>
        <h2 id="reviews-title" className={styles.title}>
          {t.reviews.title}
        </h2>
        {body}
      </div>

      <aside className={styles.aside}>
        {user ? (
          <ReviewAside slug={slug} />
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

/** The average, the count and a bar per star; a bar filters the list to that star. */
function Summary({
  data,
  selected,
  onSelect,
}: {
  data: ReviewPage
  selected?: number
  onSelect: (stars: number | undefined) => void
}) {
  const { t } = useI18n()
  const { average, count, distribution } = data.summary
  const most = Math.max(...distribution.map((bucket) => bucket.count), 1)
  return (
    <div className={styles.summary}>
      <div className={styles.average}>
        <span className={styles.averageNumber}>{average ? Number(average).toFixed(1) : '-'}</span>
        <Stars rating={average === null ? null : Number(average)} />
        <span className={styles.countLabel}>{interpolate(t.reviews.count, { count })}</span>
      </div>
      <ul aria-label={t.reviews.summaryLabel} className={styles.bars}>
        {distribution.map(({ stars, count: n }) => (
          <li key={stars}>
            <button
              type="button"
              className={styles.bar}
              aria-pressed={selected === stars}
              aria-label={interpolate(t.reviews.barLabel, { stars, count: n })}
              onClick={() => onSelect(selected === stars ? undefined : stars)}
            >
              <span aria-hidden="true" className={styles.barStars}>
                {interpolate(t.reviews.starsShort, { stars })}
              </span>
              <span aria-hidden="true" className={styles.track}>
                <span className={styles.fill} style={{ width: `${(n / most) * 100}%` }} />
              </span>
              <span aria-hidden="true" className={styles.barCount}>
                {n}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

function ReviewItem({ review }: { review: Review }) {
  const { t, lang } = useI18n()
  return (
    <li className={styles.review}>
      <div className={styles.meta}>
        <span className={styles.author}>
          <strong>{review.user_name}</strong>
          {review.verified_purchase && (
            <span className={styles.verified}>
              <span aria-hidden="true">✓</span> {t.reviews.verified}
            </span>
          )}
        </span>
        <time dateTime={review.created_at} className={styles.date}>
          {formatDate(review.created_at, lang)}
        </time>
      </div>
      <Stars rating={review.rating} />
      <p className={styles.comment}>{review.comment}</p>
      {review.photos.length > 0 && (
        <ul className={styles.photos}>
          {review.photos.map((photo) => (
            <li key={photo.id}>
              <a href={photo.url} target="_blank" rel="noreferrer">
                <img
                  src={photo.thumbnail_url}
                  alt={interpolate(t.reviews.photoAlt, { name: review.user_name })}
                  loading="lazy"
                  className={styles.photo}
                />
              </a>
            </li>
          ))}
        </ul>
      )}
      {review.reply && (
        <div className={styles.reply}>
          <span className={styles.replyLabel}>{t.reviews.reply}</span>
          <p className={styles.comment}>{review.reply}</p>
        </div>
      )}
    </li>
  )
}

/** The form for customers who received the dish; otherwise why it is closed. */
function ReviewAside({ slug }: { slug: string }) {
  const { t } = useI18n()
  const eligibility = useQuery(reviewQueries.eligibility(slug))
  // Once posted, eligibility turns to "already reviewed"; the form stays to say thank you.
  const [posted, setPosted] = useState(false)
  if (posted) return <ReviewForm slug={slug} onPosted={() => setPosted(true)} />
  if (eligibility.isPending) return <Loading />
  if (eligibility.isError) {
    return <ErrorView error={eligibility.error} onRetry={() => void eligibility.refetch()} />
  }
  if (eligibility.data.can_review) {
    return <ReviewForm slug={slug} onPosted={() => setPosted(true)} />
  }
  return (
    <div className={styles.signIn}>
      <h3 className={styles.asideTitle}>{t.reviews.write}</h3>
      <p>
        {eligibility.data.reason === 'already_reviewed'
          ? t.reviews.alreadyReviewed
          : t.reviews.notPurchased}
      </p>
    </div>
  )
}
