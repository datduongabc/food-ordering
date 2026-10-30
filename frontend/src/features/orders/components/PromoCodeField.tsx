import { useState } from 'react'
import { TextField } from '@/components/form/TextField'
import { Button } from '@/components/ui/Button'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { formatVnd, interpolate } from '@/lib/format'
import { useCheckPromo } from '../api'
import type { PromoQuote } from '../schemas'
import styles from './PromoCodeField.module.css'

/**
 * Checks a code against the cart before the order is placed. It sits inside the checkout
 * form, so Enter applies the code instead of submitting the order.
 */
export function PromoCodeField({
  applied,
  onChange,
}: {
  applied: PromoQuote | undefined
  onChange: (quote: PromoQuote | undefined) => void
}) {
  const { t } = useI18n()
  const errorMessage = useErrorMessage()
  const check = useCheckPromo()
  const [code, setCode] = useState('')
  const [error, setError] = useState<string>()

  function apply() {
    const trimmed = code.trim()
    if (!trimmed) return
    setError(undefined)
    check.mutate(trimmed, {
      onSuccess: (quote) => {
        onChange(quote)
        setCode('')
      },
      onError: (failure) => setError(errorMessage(failure)),
    })
  }

  if (applied) {
    return (
      <div className={styles.applied} role="status">
        <span>
          {interpolate(t.checkout.promoApplied, {
            code: applied.code,
            amount: formatVnd(applied.discount),
          })}
        </span>
        <Button variant="outline" onClick={() => onChange(undefined)}>
          {t.checkout.promoRemove}
        </Button>
      </div>
    )
  }

  return (
    <div className={styles.row}>
      <TextField
        label={t.checkout.promoLabel}
        autoComplete="off"
        autoCapitalize="characters"
        spellCheck={false}
        maxLength={32}
        value={code}
        error={error}
        onChange={(event) => setCode(event.target.value)}
        onKeyDown={(event) => {
          if (event.key !== 'Enter') return
          event.preventDefault()
          apply()
        }}
      />
      <Button
        variant="outline"
        className={styles.apply}
        disabled={!code.trim() || check.isPending}
        onClick={apply}
      >
        {t.checkout.promoApply}
      </Button>
    </div>
  )
}
