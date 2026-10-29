import { Link } from 'react-router'
import { Button } from '@/components/ui/Button'
import { Stars } from '@/components/ui/Stars'
import { useAddToCart } from '@/features/cart/useAddToCart'
import { useI18n } from '@/i18n/context'
import { formatPrice, interpolate } from '@/lib/format'
import type { Product } from '../schemas'
import { useCategoryLabel } from '../useCategoryLabel'
import styles from './ProductCard.module.css'

export function ProductCard({
  product,
  headingLevel = 2,
}: {
  product: Product
  headingLevel?: 2 | 3
}) {
  const { t } = useI18n()
  const categoryLabel = useCategoryLabel()
  const addToCart = useAddToCart()
  const Heading = `h${headingLevel}` as const
  const href = `/menu/${product.slug}`

  return (
    <article className={styles.card}>
      <Link to={href} tabIndex={-1} aria-hidden="true">
        <img src={product.image_url} alt="" loading="lazy" className={styles.image} />
      </Link>
      <div className={styles.body}>
        {product.category && (
          <span className={styles.category}>{categoryLabel(product.category)}</span>
        )}
        <Heading className={styles.name}>
          <Link to={href}>{product.name}</Link>
        </Heading>
        <p className={styles.description}>{product.description}</p>
        <Stars rating={product.average_rating === null ? null : Number(product.average_rating)} />
        <div className={styles.footer}>
          <span className={styles.price}>{formatPrice(product.price)}</span>
          <Button
            variant="dark"
            aria-label={interpolate(t.common.addToCartLabel, { name: product.name })}
            onClick={() => void addToCart(product)}
          >
            {t.common.add}
          </Button>
        </div>
      </div>
    </article>
  )
}
