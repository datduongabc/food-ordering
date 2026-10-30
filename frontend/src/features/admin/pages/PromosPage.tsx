import { useMemo, useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useQuery } from '@tanstack/react-query'
import { useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'
import { FormError } from '@/components/form/FormError'
import { SelectField } from '@/components/form/SelectField'
import { TextField } from '@/components/form/TextField'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { EmptyView, ErrorView, Loading } from '@/components/ui/StatusView'
import { useToast } from '@/components/ui/toastContext'
import { useServerErrors } from '@/features/auth/useFieldErrors'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { formatDate, formatVnd, interpolate } from '@/lib/format'
import { adminQueries, useSavePromo, useSetPromoActive } from '../api'
import { DISCOUNT_KINDS, type AdminPromo, type PromoInput } from '../schemas'
import shared from '../admin.module.css'
import styles from './ProductsPage.module.css'

/** Today at the restaurant as YYYY-MM-DD, whatever the browser's own time zone. */
function restaurantToday(): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Ho_Chi_Minh' }).format(new Date())
}

export function AdminPromosPage() {
  const { t } = useI18n()
  const labels = t.admin.promos
  const promos = useQuery(adminQueries.promos())
  const [editing, setEditing] = useState<AdminPromo | 'new'>()

  let body
  if (promos.error) {
    body = <ErrorView error={promos.error} onRetry={() => promos.refetch()} />
  } else if (!promos.data) {
    body = <Loading />
  } else if (promos.data.length === 0) {
    body = <EmptyView title={labels.empty} />
  } else {
    body = (
      <div className={shared.tableWrap}>
        <table className={shared.table}>
          <thead>
            <tr>
              <th scope="col">{labels.code}</th>
              <th scope="col">{labels.discount}</th>
              <th scope="col">{labels.conditions}</th>
              <th scope="col">{labels.period}</th>
              <th scope="col">{labels.uses}</th>
              <th scope="col">{t.admin.actions}</th>
            </tr>
          </thead>
          <tbody>
            {promos.data.map((promo) => (
              <PromoRow key={promo.id} promo={promo} onEdit={() => setEditing(promo)} />
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  return (
    <>
      <div className={shared.head}>
        <h1 className={shared.title}>{labels.title}</h1>
        <Button onClick={() => setEditing('new')}>{labels.add}</Button>
      </div>
      <p className={shared.muted}>{labels.intro}</p>
      {editing && (
        <PromoForm
          key={editing === 'new' ? 'new' : editing.id}
          promo={editing === 'new' ? undefined : editing}
          onDone={() => setEditing(undefined)}
        />
      )}
      {body}
    </>
  )
}

function PromoRow({ promo, onEdit }: { promo: AdminPromo; onEdit: () => void }) {
  const { t, lang } = useI18n()
  const labels = t.admin.promos
  const toast = useToast()
  const errorMessage = useErrorMessage()
  const setActive = useSetPromoActive()
  const disabled = promo.disabled_at !== null
  const expired = promo.ends_on !== null && promo.ends_on < restaurantToday()

  const discount =
    promo.kind === 'PERCENT'
      ? [
          interpolate(labels.percentOff, { value: promo.value }),
          promo.max_discount !== null &&
            interpolate(labels.upTo, { amount: formatVnd(promo.max_discount) }),
        ]
          .filter(Boolean)
          .join(', ')
      : interpolate(labels.amountOff, { amount: formatVnd(promo.value) })

  function toggle(active: boolean) {
    setActive.mutate(
      { id: promo.id, active },
      {
        onSuccess: () =>
          toast(interpolate(active ? labels.enabled : labels.disabled, { code: promo.code })),
        onError: (error) => toast(errorMessage(error)),
      },
    )
  }

  return (
    <tr data-inactive={disabled || expired}>
      <td data-label={labels.code}>
        <div className={shared.cellStack}>
          <strong>{promo.code}</strong>
          {disabled ? (
            <Badge tone="stone">{labels.disabledBadge}</Badge>
          ) : expired ? (
            <Badge tone="amber">{labels.expiredBadge}</Badge>
          ) : (
            <Badge tone="green">{labels.active}</Badge>
          )}
        </div>
      </td>
      <td data-label={labels.discount}>{discount}</td>
      <td data-label={labels.conditions}>
        <div className={shared.cellStack}>
          <span>
            {promo.min_subtotal > 0
              ? interpolate(labels.minOrder, { amount: formatVnd(promo.min_subtotal) })
              : labels.noMin}
          </span>
          {promo.per_customer_limit !== null && (
            <span className={shared.muted}>
              {interpolate(labels.perCustomerTimes, { count: promo.per_customer_limit })}
            </span>
          )}
        </div>
      </td>
      <td data-label={labels.period}>
        <div className={shared.cellStack}>
          {promo.starts_on && (
            <span>{interpolate(labels.fromDate, { date: formatDate(promo.starts_on, lang) })}</span>
          )}
          <span>
            {promo.ends_on
              ? interpolate(labels.untilDate, { date: formatDate(promo.ends_on, lang) })
              : labels.always}
          </span>
        </div>
      </td>
      <td data-label={labels.uses} className={shared.num}>
        {promo.usage_limit === null
          ? promo.uses
          : interpolate(labels.usesOf, { uses: promo.uses, limit: promo.usage_limit })}
      </td>
      <td data-label={t.admin.actions}>
        <div className={shared.rowActions}>
          <Button
            variant="outline"
            className={shared.small}
            aria-label={`${t.admin.edit} ${promo.code}`}
            onClick={onEdit}
          >
            {t.admin.edit}
          </Button>
          <Button
            variant={disabled ? 'green' : 'danger'}
            className={shared.small}
            disabled={setActive.isPending}
            aria-label={`${disabled ? labels.enable : labels.disable} ${promo.code}`}
            onClick={() => toggle(disabled)}
          >
            {disabled ? labels.enable : labels.disable}
          </Button>
        </div>
      </td>
    </tr>
  )
}

const asNumber = (value: string) => (value.trim() === '' ? null : Number(value))

function PromoForm({ promo, onDone }: { promo: AdminPromo | undefined; onDone: () => void }) {
  const { t } = useI18n()
  const labels = t.admin.promos
  const toast = useToast()
  const save = useSavePromo()
  const [formError, setFormError] = useState<string>()

  const schema = useMemo(() => {
    const whole = z.string().trim().regex(/^\d*$/, labels.wholeNumber)
    return z
      .object({
        code: z
          .string()
          .trim()
          .regex(/^[A-Za-z0-9_-]{3,32}$/, labels.codeInvalid),
        kind: z.enum(DISCOUNT_KINDS),
        value: whole.min(1, labels.wholeNumber),
        max_discount: whole,
        min_subtotal: whole,
        starts_on: z.string(),
        ends_on: z.string(),
        usage_limit: whole,
        per_customer_limit: whole,
      })
      .superRefine((values, ctx) => {
        const value = Number(values.value)
        if (values.kind === 'PERCENT' && (value < 1 || value > 100)) {
          ctx.addIssue({ code: 'custom', path: ['value'], message: labels.percentRange })
        }
        if (values.kind === 'AMOUNT' && value < 1000) {
          ctx.addIssue({ code: 'custom', path: ['value'], message: labels.amountMin })
        }
        if (
          values.kind === 'PERCENT' &&
          values.max_discount &&
          Number(values.max_discount) < 1000
        ) {
          ctx.addIssue({ code: 'custom', path: ['max_discount'], message: labels.amountMin })
        }
        for (const field of ['usage_limit', 'per_customer_limit'] as const) {
          if (values[field] && Number(values[field]) < 1) {
            ctx.addIssue({ code: 'custom', path: [field], message: labels.wholeNumber })
          }
        }
        if (values.starts_on && values.ends_on && values.ends_on < values.starts_on) {
          ctx.addIssue({ code: 'custom', path: ['ends_on'], message: labels.endBeforeStart })
        }
      })
  }, [labels])

  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      code: promo?.code ?? '',
      kind: promo?.kind ?? 'PERCENT',
      value: promo ? String(promo.value) : '',
      max_discount: promo?.max_discount?.toString() ?? '',
      min_subtotal: promo && promo.min_subtotal > 0 ? String(promo.min_subtotal) : '',
      starts_on: promo?.starts_on ?? '',
      ends_on: promo?.ends_on ?? '',
      usage_limit: promo?.usage_limit?.toString() ?? '',
      per_customer_limit: promo ? (promo.per_customer_limit?.toString() ?? '') : '1',
    },
  })
  const serverError = useServerErrors(form, { promo_code_taken: 'code' })
  const errors = form.formState.errors
  const kind = useWatch({ control: form.control, name: 'kind' })

  return (
    <form
      className={`${shared.card} ${styles.fields} ${shared.formCard}`}
      aria-labelledby="promo-form-title"
      noValidate
      onSubmit={form.handleSubmit(async (values) => {
        setFormError(undefined)
        const input: PromoInput = {
          code: values.code.toUpperCase(),
          kind: values.kind,
          value: Number(values.value),
          max_discount: values.kind === 'PERCENT' ? asNumber(values.max_discount) : null,
          min_subtotal: asNumber(values.min_subtotal) ?? 0,
          starts_on: values.starts_on || null,
          ends_on: values.ends_on || null,
          usage_limit: asNumber(values.usage_limit),
          per_customer_limit: asNumber(values.per_customer_limit),
        }
        try {
          const saved = await save.mutateAsync({ id: promo?.id, values: input })
          toast(promo ? t.admin.saved : interpolate(labels.created, { code: saved.code }))
          onDone()
        } catch (error) {
          setFormError(serverError(error))
        }
      })}
    >
      <h2 id="promo-form-title" className={shared.cardTitle}>
        {promo ? interpolate(labels.editTitle, { code: promo.code }) : labels.newTitle}
      </h2>
      <div className={styles.pair}>
        <TextField
          label={labels.code}
          autoComplete="off"
          autoCapitalize="characters"
          spellCheck={false}
          maxLength={32}
          placeholder="GIAM20"
          error={errors.code?.message}
          {...form.register('code')}
        />
        <SelectField label={labels.kind} error={errors.kind?.message} {...form.register('kind')}>
          {DISCOUNT_KINDS.map((option) => (
            <option key={option} value={option}>
              {labels.kinds[option]}
            </option>
          ))}
        </SelectField>
      </div>
      <div className={styles.pair}>
        <TextField
          label={kind === 'PERCENT' ? labels.percent : labels.amount}
          inputMode="numeric"
          error={errors.value?.message}
          {...form.register('value')}
        />
        {kind === 'PERCENT' ? (
          <TextField
            label={labels.maxDiscount}
            inputMode="numeric"
            placeholder={labels.optional}
            error={errors.max_discount?.message}
            {...form.register('max_discount')}
          />
        ) : (
          <span />
        )}
      </div>
      <div className={styles.pair}>
        <TextField
          label={labels.minSubtotal}
          inputMode="numeric"
          placeholder="0"
          error={errors.min_subtotal?.message}
          {...form.register('min_subtotal')}
        />
        <TextField
          label={labels.perCustomer}
          inputMode="numeric"
          placeholder={labels.optional}
          error={errors.per_customer_limit?.message}
          {...form.register('per_customer_limit')}
        />
      </div>
      <div className={styles.pair}>
        <TextField
          label={labels.startsOn}
          type="date"
          error={errors.starts_on?.message}
          {...form.register('starts_on')}
        />
        <TextField
          label={labels.endsOn}
          type="date"
          error={errors.ends_on?.message}
          {...form.register('ends_on')}
        />
      </div>
      <TextField
        label={labels.usageLimit}
        inputMode="numeric"
        placeholder={labels.optional}
        error={errors.usage_limit?.message}
        {...form.register('usage_limit')}
      />
      <FormError message={formError} />
      <div className={shared.rowActions}>
        <Button type="submit" disabled={form.formState.isSubmitting}>
          {t.admin.save}
        </Button>
        <Button variant="outline" onClick={onDone}>
          {t.admin.cancel}
        </Button>
      </div>
    </form>
  )
}
