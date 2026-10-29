import { useId, type ComponentProps } from 'react'
import styles from './TextField.module.css'

interface Props extends ComponentProps<'input'> {
  label: string
  error?: string
  /** Rendered next to the label, e.g. a "Forgot password?" link. */
  labelAction?: React.ReactNode
  variant?: 'default' | 'code'
}

export function TextField({
  label,
  error,
  labelAction,
  variant = 'default',
  className,
  ...input
}: Props) {
  const id = useId()
  const errorId = `${id}-error`
  return (
    <div className={styles.field}>
      <div className={styles.labelRow}>
        <label htmlFor={id} className={styles.label}>
          {label}
        </label>
        {labelAction}
      </div>
      <input
        id={id}
        className={[styles.input, variant === 'code' && styles.code, className]
          .filter(Boolean)
          .join(' ')}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        {...input}
      />
      {error && (
        <p id={errorId} className={styles.error}>
          {error}
        </p>
      )}
    </div>
  )
}
