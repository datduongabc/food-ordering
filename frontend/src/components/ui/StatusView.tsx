import type { ReactNode } from 'react'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { Button } from './Button'
import styles from './StatusView.module.css'

export function Loading({ label }: { label?: string }) {
  const { t } = useI18n()
  return (
    <div className={styles.loading} role="status">
      <span className={styles.spinner} aria-hidden="true" />
      {label ?? t.common.loading}
    </div>
  )
}

export function ErrorView({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const { t } = useI18n()
  const message = useErrorMessage()
  return (
    <div className={styles.box} role="alert">
      <p className={styles.title}>{t.errors.loadFailed}</p>
      <p className={styles.body}>{message(error)}</p>
      {onRetry && (
        <Button variant="outline" onClick={onRetry}>
          {t.common.retry}
        </Button>
      )}
    </div>
  )
}

export function EmptyView({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className={styles.box}>
      <p className={styles.title}>{title}</p>
      {children}
    </div>
  )
}
