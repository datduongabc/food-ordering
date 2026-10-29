import { useId, type ComponentProps } from 'react'
import styles from './TextField.module.css'

interface Props extends ComponentProps<'select'> {
  label: string
  error?: string
}

export function SelectField({ label, error, className, children, ...select }: Props) {
  const id = useId()
  const errorId = `${id}-error`
  return (
    <div className={styles.field}>
      <label htmlFor={id} className={styles.label}>
        {label}
      </label>
      <select
        id={id}
        className={[styles.input, styles.select, className].filter(Boolean).join(' ')}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        {...select}
      >
        {children}
      </select>
      {error && (
        <p id={errorId} className={styles.error}>
          {error}
        </p>
      )}
    </div>
  )
}
