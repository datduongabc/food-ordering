import styles from './Button.module.css'

export type Variant = 'primary' | 'dark' | 'outline' | 'danger' | 'momo' | 'green'
export type Size = 'md' | 'lg'

/** Button styling for elements that are not buttons, such as a download link. */
export function buttonClasses(variant: Variant, size: Size, block = false, extra?: string) {
  return [styles.button, styles[variant], styles[size], block && styles.block, extra]
    .filter(Boolean)
    .join(' ')
}
