import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react'
import { ToastContext } from './toastContext'
import styles from './ToastProvider.module.css'

const VISIBLE_MS = 2600

export function ToastProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState('')
  const timer = useRef<number | undefined>(undefined)

  const show = useCallback((next: string) => {
    window.clearTimeout(timer.current)
    setMessage(next)
    timer.current = window.setTimeout(() => setMessage(''), VISIBLE_MS)
  }, [])

  useEffect(() => () => window.clearTimeout(timer.current), [])

  return (
    <ToastContext value={show}>
      {children}
      {/* Always mounted so screen readers announce each new message. */}
      <div role="status" aria-live="polite" className={styles.region}>
        {message && <div className={styles.toast}>{message}</div>}
      </div>
    </ToastContext>
  )
}
