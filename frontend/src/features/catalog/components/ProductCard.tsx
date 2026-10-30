import { Link } from 'react-router'
import { Button } from '@/components/ui/Button'
import { Stars } from '@/components/ui/Stars'
import { useAddToCart } from '@/features/cart/useAddToCart'
import { useI18n } from '@/i18n/context'
import { useLocalize } from '@/i18n/useLocalize'
import { formatVnd, interpolate } from '@/lib/format'
import type { Product } from '../schemas'
import styles from './ProductCard.module.css'

export function ProductCard({
  product,
  headingLevel = 2,
}: {
  product: Product
  headingLevel?: 2 | 3
}) {
  const { t } = useI18n()
  const localize = useLocalize()
  const name = localize(product.name)
  const addToCart = useAddToCart()
  const Heading = `h${headingLevel}` as const
  const href = `/menu/${product.slug}`

  return (
    <article className={styles.card}>
      <Link to={href} tabIndex={-1} aria-hidden="true">
        <img src={product.thumbnail_url} alt="" loading="lazy" className={styles.image} />
      </Link>
      <div className={styles.body}>
        {product.category && (
          <span className={styles.category}>{localize(product.category.name)}</span>
        )}
        <Heading className={styles.name}>
          <Link to={href}>{name}</Link>
        </Heading>
        <p className={styles.description}>{localize(product.description)}</p>
        <Stars rating={product.average_rating === null ? null : Number(product.average_rating)} />
        <div className={styles.footer}>
          <span className={styles.price}>{formatVnd(product.price)}</span>
          <Button
            variant="dark"
            aria-label={interpolate(t.common.addToCartLabel, { name })}
            onClick={() => void addToCart(product)}
          >
            {t.common.add}
          </Button>
        </div>
      </div>
    </article>
  )
}
