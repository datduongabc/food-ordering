import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Stars } from '@/components/ui/Stars'
import { EmptyView, ErrorView, Loading } from '@/components/ui/StatusView'
import { useToast } from '@/components/ui/toastContext'
import { Pagination } from '@/features/catalog/components/Pagination'
import { COMMENT_MAX } from '@/features/reviews/schemas'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { useLocalize } from '@/i18n/useLocalize'
import { formatDateTime, interpolate } from '@/lib/format'
import { adminQueries, useReplyToReview, useSetReviewHidden } from '../api'
import { FilterChips } from '../components/FilterChips'
import { REVIEW_VISIBILITIES, type AdminReview } from '../schemas'
import { oneOf, useUrlFilters } from '../useUrlFilters'
import shared from '../admin.module.css'
import styles from './ReviewsPage.module.css'

const STARS = ['5', '4', '3', '2', '1'] as const

export function AdminReviewsPage() {
  const { t } = useI18n()
  const labels = t.admin.reviews
  const { params, page, update } = useUrlFilters()
  const visibility = oneOf(REVIEW_VISIBILITIES, params.get('visibility'))
  const stars = oneOf(STARS, params.get('rating'))
  const reviews = useQuery(
    adminQueries.reviews({ visibility, rating: stars ? Number(stars) : undefined, page }),
  )

  let body
  if (reviews.error) {
    body = <ErrorView error={reviews.error} onRetry={() => reviews.refetch()} />
  } else if (!reviews.data) {
    body = <Loading />
  } else if (reviews.data.items.length === 0) {
    body = <EmptyView title={t.admin.noResults} />
  } else {
    body = (
      <>
        <ul className={styles.list}>
          {reviews.data.items.map((review) => (
            <ReviewCard key={review.id} review={review} />
          ))}
        </ul>
        {reviews.data.total_pages > 1 && (
          <div className={shared.pager}>
            <Pagination
              page={page}
              totalPages={reviews.data.total_pages}
              onChange={(next) => update({ page: String(next) })}
            />
          </div>
        )}
      </>
    )
  }

  return (
    <>
      <div className={shared.head}>
        <h1 className={shared.title}>{labels.title}</h1>
        {reviews.data && (
          <span className={shared.count}>
            {interpolate(t.admin.total, { count: reviews.data.total })}
          </span>
        )}
      </div>
      <p className={shared.muted}>{labels.intro}</p>
      <div className={shared.filters}>
        <FilterChips
          label={labels.visibility}
          options={[
            { value: undefined, label: t.admin.all },
            ...REVIEW_VISIBILITIES.map((value) => ({ value, label: labels.visibilities[value] })),
          ]}
          value={visibility}
          onChange={(value) => update({ visibility: value })}
        />
        <FilterChips
          label={labels.stars}
          options={[
            { value: undefined, label: t.admin.all },
            ...STARS.map((value) => ({ value, label: `${value}★` })),
          ]}
          value={stars}
          onChange={(value) => update({ rating: value })}
        />
      </div>
      {body}
    </>
  )
}

function ReviewCard({ review }: { review: AdminReview }) {
  const { t, lang } = useI18n()
  const labels = t.admin.reviews
  const localize = useLocalize()
  const toast = useToast()
  const errorMessage = useErrorMessage()
  const setHidden = useSetReviewHidden()
  const [replying, setReplying] = useState(false)
  const hidden = review.hidden_at !== null

  function toggle(hide: boolean) {
    setHidden.mutate(
      { id: review.id, hidden: hide },
      {
        onSuccess: () =>
          toast(interpolate(hide ? labels.hidden : labels.restored, { name: review.user_name })),
        onError: (error) => toast(errorMessage(error)),
      },
    )
  }

  return (
    <li className={styles.card} data-hidden={hidden}>
      <div className={styles.head}>
        <div className={shared.cellStack}>
          <Link to={`/menu/${review.product_slug}#reviews`} className={styles.dish}>
            {localize(review.product_name)}
          </Link>
          <span className={shared.muted}>
            {review.user_name} · {formatDateTime(review.created_at, lang)}
          </span>
        </div>
        <div className={styles.badges}>
          <Stars rating={review.rating} />
          {review.verified_purchase && <Badge tone="green">{t.reviews.verified}</Badge>}
          {hidden && <Badge tone="stone">{labels.hiddenBadge}</Badge>}
        </div>
      </div>
      <p className={styles.comment}>{review.comment}</p>
      {review.photos.length > 0 && (
        <ul
          className={styles.photos}
          aria-label={interpolate(labels.photoCount, { count: review.photos.length })}
        >
          {review.photos.map((photo) => (
            <li key={photo.id}>
              <a href={photo.url} target="_blank" rel="noreferrer">
                <img
                  src={photo.thumbnail_url}
                  alt={interpolate(t.reviews.photoAlt, { name: review.user_name })}
                  className={styles.photo}
                />
              </a>
            </li>
          ))}
        </ul>
      )}
      {replying ? (
        <ReplyForm review={review} onDone={() => setReplying(false)} />
      ) : (
        review.reply && (
          <div className={styles.reply}>
            <span className={styles.replyLabel}>{t.reviews.reply}</span>
            <p className={styles.comment}>{review.reply}</p>
          </div>
        )
      )}
      {!replying && (
        <div className={shared.rowActions}>
          <Button variant="outline" className={shared.small} onClick={() => setReplying(true)}>
            {review.reply ? labels.editReply : labels.reply}
          </Button>
          <Button
            variant={hidden ? 'green' : 'danger'}
            className={shared.small}
            disabled={setHidden.isPending}
            onClick={() => toggle(!hidden)}
          >
            {hidden ? labels.restore : labels.hide}
          </Button>
        </div>
      )}
    </li>
  )
}

function ReplyForm({ review, onDone }: { review: AdminReview; onDone: () => void }) {
  const { t } = useI18n()
  const labels = t.admin.reviews
  const toast = useToast()
  const errorMessage = useErrorMessage()
  const reply = useReplyToReview()
  const [text, setText] = useState(review.reply ?? '')

  return (
    <form
      className={styles.replyForm}
      onSubmit={(event) => {
        event.preventDefault()
        reply.mutate(
          { id: review.id, reply: text },
          {
            onSuccess: () => {
              toast(labels.replySaved)
              onDone()
            },
            onError: (error) => toast(errorMessage(error)),
          },
        )
      }}
    >
      <label className={styles.replyField}>
        {labels.replyLabel}
        <textarea
          rows={3}
          maxLength={COMMENT_MAX}
          value={text}
          onChange={(event) => setText(event.target.value)}
          className={styles.textarea}
        />
      </label>
      <p className={shared.muted}>{labels.replyHint}</p>
      <div className={shared.rowActions}>
        <Button type="submit" className={shared.small} disabled={reply.isPending}>
          {t.admin.save}
        </Button>
        <Button type="button" variant="outline" className={shared.small} onClick={onDone}>
          {t.admin.cancel}
        </Button>
      </div>
    </form>
  )
}
