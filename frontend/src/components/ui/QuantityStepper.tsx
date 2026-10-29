import { useI18n } from '@/i18n/context'
import styles from './QuantityStepper.module.css'

interface Props {
  value: number
  onChange: (value: number) => void
  min?: number
  max?: number
  label: string
  disabled?: boolean
}

export function QuantityStepper({ value, onChange, min = 1, max = 99, label, disabled }: Props) {
  const { t } = useI18n()
  return (
    <div role="group" aria-label={label} className={styles.stepper}>
      <button
        type="button"
        className={styles.step}
        aria-label={t.dish.decrease}
        disabled={disabled || value <= min}
        onClick={() => onChange(value - 1)}
      >
        −
      </button>
      <output aria-live="polite" className={styles.value}>
        {value}
      </output>
      <button
        type="button"
        className={styles.step}
        aria-label={t.dish.increase}
        disabled={disabled || value >= max}
        onClick={() => onChange(value + 1)}
      >
        +
      </button>
    </div>
  )
}
