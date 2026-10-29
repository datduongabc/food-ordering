import { useMemo, useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useQuery } from '@tanstack/react-query'
import { useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'
import { ChoiceCard } from '@/components/form/ChoiceCard'
import { FormError } from '@/components/form/FormError'
import { SelectField } from '@/components/form/SelectField'
import { TextAreaField } from '@/components/form/TextAreaField'
import { TextField } from '@/components/form/TextField'
import { Button, ButtonLink } from '@/components/ui/Button'
import { ErrorView, Loading } from '@/components/ui/StatusView'
import { useCurrentUser } from '@/features/auth/queries'
import type { User } from '@/features/auth/schemas'
import { useServerErrors } from '@/features/auth/useFieldErrors'
import { authRules } from '@/features/auth/validation'
import { catalogQueries } from '@/features/catalog/queries'
import type { Location } from '@/features/catalog/schemas'
import { useI18n } from '@/i18n/context'
import { useLocalize } from '@/i18n/useLocalize'
import { formatClock, formatDayParts, interpolate } from '@/lib/format'
import { reservationQueries, useBookTable } from '../api'
import type { Reservation, ReservationPolicy } from '../schemas'
import { bookableDates, restaurantClock, timeSlots } from '../slots'
import styles from './BookingSection.module.css'

const PREFERRED_TIME = '19:00'

export function BookingSection() {
  const { t } = useI18n()
  const user = useCurrentUser()
  const policy = useQuery(reservationQueries.policy())
  const locations = useQuery(catalogQueries.locations())
  const error = policy.error ?? locations.error

  return (
    <section id="book" aria-labelledby="book-title" className={styles.section}>
      <div className={styles.inner}>
        <div className={styles.intro}>
          <p className={styles.kicker}>{t.booking.kicker}</p>
          <h2 id="book-title" className={styles.title}>
            {t.booking.title}
          </h2>
          {policy.data && (
            <p className={styles.body}>
              {interpolate(t.booking.body, {
                days: bookableDates(policy.data).length - 1,
                max: policy.data.max_guests,
              })}
            </p>
          )}
        </div>
        <div className={styles.card}>
          {error ? (
            <ErrorView error={error} />
          ) : !policy.data || !locations.data || user === undefined ? (
            <Loading />
          ) : (
            <BookingForm policy={policy.data} locations={locations.data} user={user} />
          )}
        </div>
      </div>
    </section>
  )
}

function BookingForm({
  policy,
  locations,
  user,
}: {
  policy: ReservationPolicy
  locations: Location[]
  user: User | null
}) {
  const { t, lang } = useI18n()
  const localize = useLocalize()
  const book = useBookTable()
  const [booked, setBooked] = useState<Reservation>()
  const [formError, setFormError] = useState<string>()

  const clock = restaurantClock(policy)
  const dates = bookableDates(policy).map((date) => ({
    date,
    slots: timeSlots(policy, date, clock),
  }))
  const firstOpen = dates.find((day) => day.slots.length > 0)
  const pickTime = (slots: string[]) =>
    slots.includes(PREFERRED_TIME) ? PREFERRED_TIME : (slots[0] ?? '')

  const schema = useMemo(() => {
    const rules = authRules(t)
    return z.object({
      reservation_date: z.string().min(1, t.validation.required),
      reservation_time: z.string().min(1, t.validation.required),
      guest_count: z.coerce.number<string>().int().min(1),
      location_id: z.coerce.number<string>().int(),
      customer_name: rules.name,
      customer_phone: rules.phone,
      special_requests: z
        .string()
        .trim()
        .max(1000, interpolate(t.validation.tooLong, { max: 1000 })),
    })
  }, [t])

  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      reservation_date: firstOpen?.date ?? '',
      reservation_time: pickTime(firstOpen?.slots ?? []),
      guest_count: '2',
      location_id: String(locations[0]?.id ?? ''),
      customer_name: user?.name ?? '',
      customer_phone: user?.phone ?? '',
      special_requests: '',
    },
  })
  const serverError = useServerErrors(form, {
    too_many_guests: 'guest_count',
    time_passed: 'reservation_time',
    outside_opening_hours: 'reservation_time',
  })
  const errors = form.formState.errors
  const selectedDate = useWatch({ control: form.control, name: 'reservation_date' })
  const slots = dates.find((day) => day.date === selectedDate)?.slots ?? []

  if (booked) {
    const summary = interpolate(t.booking.summary, {
      date: formatDayParts(booked.reservation_date, lang).full,
      time: formatClock(booked.reservation_time),
      guests: booked.guest_count,
      branch: localize(booked.location.name),
    })
    return (
      <div className={styles.done} role="status">
        <p className={styles.doneKicker}>{t.booking.doneKicker}</p>
        <h3 className={styles.doneTitle}>{t.booking.doneTitle}</h3>
        <p className={styles.doneBody}>
          {interpolate(t.booking.doneBody, { summary, phone: booked.customer_phone })}
        </p>
        <div className={styles.doneActions}>
          {user && (
            <ButtonLink to="/account?tab=bookings" variant="green">
              {t.booking.viewBookings}
            </ButtonLink>
          )}
          <Button
            variant="outline"
            onClick={() => {
              book.reset()
              setBooked(undefined)
            }}
          >
            {t.booking.another}
          </Button>
        </div>
      </div>
    )
  }

  return (
    <form
      className={styles.form}
      noValidate
      onSubmit={form.handleSubmit(async (values) => {
        setFormError(undefined)
        try {
          setBooked(await book.mutateAsync(values))
        } catch (error) {
          setFormError(serverError(error))
        }
      })}
    >
      <fieldset className={styles.dates}>
        <legend className={styles.legend}>{t.booking.date}</legend>
        <div className={styles.dateGrid}>
          {dates.map(({ date, slots: daySlots }) => {
            const parts = formatDayParts(date, lang)
            return (
              <ChoiceCard
                key={date}
                compact
                value={date}
                disabled={daySlots.length === 0}
                aria-label={parts.full}
                hint={date === policy.today ? t.booking.today : parts.weekday}
                label={parts.day}
                {...form.register('reservation_date', {
                  onChange: () => form.setValue('reservation_time', pickTime(daySlots)),
                })}
              />
            )
          })}
        </div>
        {!firstOpen && <p className={styles.hint}>{t.booking.noSlots}</p>}
      </fieldset>

      <div className={styles.row}>
        <SelectField
          label={t.booking.time}
          error={errors.reservation_time?.message}
          {...form.register('reservation_time')}
        >
          {slots.map((slot) => (
            <option key={slot} value={slot}>
              {slot}
            </option>
          ))}
        </SelectField>
        <SelectField
          label={t.booking.guests}
          error={errors.guest_count?.message}
          {...form.register('guest_count')}
        >
          {Array.from({ length: policy.max_guests }, (_, index) => index + 1).map((count) => (
            <option key={count} value={count}>
              {count}
            </option>
          ))}
        </SelectField>
        <SelectField
          label={t.booking.branch}
          error={errors.location_id?.message}
          {...form.register('location_id')}
        >
          {locations.map((location) => (
            <option key={location.id} value={location.id}>
              {localize(location.name)}
            </option>
          ))}
        </SelectField>
      </div>

      <div className={styles.pair}>
        <TextField
          label={t.booking.name}
          autoComplete="name"
          placeholder="Nguyễn Văn A"
          error={errors.customer_name?.message}
          {...form.register('customer_name')}
        />
        <TextField
          label={t.booking.phone}
          type="tel"
          inputMode="numeric"
          autoComplete="tel"
          placeholder="0901 234 567"
          error={errors.customer_phone?.message}
          {...form.register('customer_phone')}
        />
      </div>
      <TextAreaField
        label={t.booking.requests}
        placeholder={t.booking.requestsPlaceholder}
        error={errors.special_requests?.message}
        {...form.register('special_requests')}
      />

      <FormError message={formError} />
      <Button
        type="submit"
        size="lg"
        className={styles.submit}
        disabled={!firstOpen || form.formState.isSubmitting}
      >
        {t.booking.submit}
      </Button>
    </form>
  )
}
