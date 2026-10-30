import type { ComponentProps } from 'react'
import { Link, type LinkProps } from 'react-router'
import { buttonClasses, type Size, type Variant } from './buttonClasses'

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
  return (
    <button type={type} className={buttonClasses(variant, size, block, className)} {...props} />
  )
}

export function ButtonLink({
  variant = 'primary',
  size = 'md',
  block = false,
  className,
  ...props
}: LinkProps & StyleProps) {
  return <Link className={buttonClasses(variant, size, block, className)} {...props} />
}
