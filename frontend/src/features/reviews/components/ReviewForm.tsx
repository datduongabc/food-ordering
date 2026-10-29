import { useMemo } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { Controller, useForm } from 'react-hook-form'
import { z } from 'zod'
import { Button } from '@/components/ui/Button'
import { FormError } from '@/components/form/FormError'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { interpolate } from '@/lib/format'
import { useCreateReview } from '../queries'
import { COMMENT_MAX } from '../schemas'
import styles from './ReviewForm.module.css'

export function ReviewForm({ slug }: { slug: string }) {
  const { t } = useI18n()
  const errorMessage = useErrorMessage()
  const createReview = useCreateReview(slug)

  const schema = useMemo(
    () =>
      z.object({
        rating: z.number().int().min(1).max(5),
        comment: z
          .string()
          .trim()
          .min(1, t.validation.commentRequired)
          .max(COMMENT_MAX, interpolate(t.validation.tooLong, { max: COMMENT_MAX })),
      }),
    [t],
  )
  const form = useForm({ resolver: zodResolver(schema), defaultValues: { rating: 5, comment: '' } })
  const commentError = form.formState.errors.comment?.message

  if (createReview.isSuccess) {
    return (
      <div className={styles.thanks} role="status">
        <span className={styles.thanksKicker}>{t.reviews.thanksKicker}</span>
        <p>{t.reviews.thanks}</p>
      </div>
    )
  }

  return (
    <form
      className={styles.form}
      noValidate
      onSubmit={form.handleSubmit((values) => createReview.mutate(values))}
    >
      <h3 className={styles.title}>{t.reviews.write}</h3>
      <Controller
        control={form.control}
        name="rating"
        render={({ field }) => (
          <fieldset className={styles.fieldset}>
            <legend className={styles.label}>{t.reviews.yourRating}</legend>
            <div className={styles.stars}>
              {[1, 2, 3, 4, 5].map((value) => (
                <button
                  key={value}
                  type="button"
                  className={styles.star}
                  data-filled={value <= field.value}
                  aria-label={interpolate(t.reviews.star, { count: value })}
                  aria-pressed={value === field.value}
                  onClick={() => field.onChange(value)}
                >
                  ★
                </button>
              ))}
            </div>
          </fieldset>
        )}
      />
      <label className={styles.label}>
        {t.reviews.comment}
        <textarea
          rows={4}
          placeholder={t.reviews.commentPlaceholder}
          aria-invalid={commentError ? true : undefined}
          aria-describedby={commentError ? 'review-comment-error' : undefined}
          className={styles.textarea}
          {...form.register('comment')}
        />
      </label>
      {commentError && (
        <p id="review-comment-error" className={styles.fieldError}>
          {commentError}
        </p>
      )}
      <Button type="submit" variant="dark" disabled={createReview.isPending}>
        {t.reviews.submit}
      </Button>
      <FormError message={createReview.isError ? errorMessage(createReview.error) : undefined} />
      <p className={styles.note}>{t.reviews.onePerDish}</p>
    </form>
  )
}
