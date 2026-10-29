import type { ReactNode } from 'react'
import styles from './Badge.module.css'

export type BadgeTone = 'amber' | 'blue' | 'green' | 'stone' | 'red'

export function Badge({
  tone,
  size = 'md',
  children,
}: {
  tone: BadgeTone
  size?: 'md' | 'lg'
  children: ReactNode
}) {
  return <span className={`${styles.badge} ${styles[tone]} ${styles[size]}`}>{children}</span>
}
