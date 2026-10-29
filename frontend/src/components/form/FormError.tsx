import styles from './FormError.module.css'

/** A form-level error (e.g. from the server); renders nothing when there is none. */
export function FormError({ message }: { message: string | undefined }) {
  if (!message) return null
  return (
    <p role="alert" className={styles.error}>
      {message}
    </p>
  )
}
