import type { ComponentProps, ReactNode } from 'react'
import styles from './ChoiceCard.module.css'

interface Props extends Omit<ComponentProps<'input'>, 'type' | 'children'> {
  label: ReactNode
  hint?: ReactNode
  compact?: boolean
}

/** A radio button drawn as a selectable card; the native input keeps keyboard and AT support. */
export function ChoiceCard({ label, hint, compact = false, className, ...input }: Props) {
  return (
    <label
      className={[styles.card, compact && styles.compact, className].filter(Boolean).join(' ')}
    >
      <input type="radio" className={styles.input} {...input} />
      <span className={styles.title}>{label}</span>
      {hint && <span className={styles.hint}>{hint}</span>}
    </label>
  )
}
