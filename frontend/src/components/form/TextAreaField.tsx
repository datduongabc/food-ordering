import { useId, type ComponentProps } from 'react'
import styles from './TextField.module.css'

interface Props extends ComponentProps<'textarea'> {
  label: string
  error?: string
}

export function TextAreaField({ label, error, className, rows = 2, ...textarea }: Props) {
  const id = useId()
  const errorId = `${id}-error`
  return (
    <div className={styles.field}>
      <label htmlFor={id} className={styles.label}>
        {label}
      </label>
      <textarea
        id={id}
        rows={rows}
        className={[styles.input, styles.textarea, className].filter(Boolean).join(' ')}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        {...textarea}
      />
      {error && (
        <p id={errorId} className={styles.error}>
          {error}
        </p>
      )}
    </div>
  )
}
