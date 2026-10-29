import styles from '../admin.module.css'

interface Props<T extends string> {
  label: string
  options: readonly { value: T | undefined; label: string }[]
  value: T | undefined
  onChange: (value: T | undefined) => void
}

/** One-choice filter drawn as a row of toggle buttons. */
export function FilterChips<T extends string>({ label, options, value, onChange }: Props<T>) {
  return (
    <div role="group" aria-label={label} className={styles.chips}>
      {options.map((option) => (
        <button
          key={option.value ?? 'all'}
          type="button"
          className={styles.chip}
          aria-pressed={option.value === value}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}
