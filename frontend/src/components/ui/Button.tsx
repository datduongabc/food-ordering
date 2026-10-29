import type { ComponentProps } from 'react'
import { Link, type LinkProps } from 'react-router'
import styles from './Button.module.css'

type Variant = 'primary' | 'dark' | 'outline' | 'danger' | 'momo' | 'green'
type Size = 'md' | 'lg'

function classes(variant: Variant, size: Size, block: boolean, extra?: string) {
  return [styles.button, styles[variant], styles[size], block && styles.block, extra]
    .filter(Boolean)
    .join(' ')
}

interface StyleProps {
  variant?: Variant
  size?: Size
  block?: boolean
}

export function Button({
  variant = 'primary',
  size = 'md',
  block = false,
  className,
  type = 'button',
  ...props
}: ComponentProps<'button'> & StyleProps) {
  return <button type={type} className={classes(variant, size, block, className)} {...props} />
}

export function ButtonLink({
  variant = 'primary',
  size = 'md',
  block = false,
  className,
  ...props
}: LinkProps & StyleProps) {
  return <Link className={classes(variant, size, block, className)} {...props} />
}
