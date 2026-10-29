import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router'
import { Button, ButtonLink } from '@/components/ui/Button'
import { QuantityStepper } from '@/components/ui/QuantityStepper'
import { Stars } from '@/components/ui/Stars'
import { EmptyView, ErrorView, Loading } from '@/components/ui/StatusView'
import { useAddToCart } from '@/features/cart/useAddToCart'
import { ReviewSection } from '@/features/reviews/components/ReviewSection'
import { useI18n } from '@/i18n/context'
import { useLocalize } from '@/i18n/useLocalize'
import { isApiError } from '@/lib/api/client'
import { formatPrice, interpolate } from '@/lib/format'
import { catalogQueries } from '../queries'
import styles from './DishPage.module.css'

export function DishPage() {
  const { slug = '' } = useParams()
  const { t } = useI18n()
  const localize = useLocalize()
  const addToCart = useAddToCart()
  const [quantity, setQuantity] = useState(1)
  const [adding, setAdding] = useState(false)
  const product = useQuery(catalogQueries.product(slug))

  if (product.isPending) return <Loading />
  if (product.isError) {
    return (
      <div className="page">
        {isApiError(product.error, 404) ? (
          <EmptyView title={t.dish.notFoundTitle}>
            <p>{t.dish.notFoundBody}</p>
            <ButtonLink to="/menu" variant="outline">
              {t.nav.menu}
            </ButtonLink>
          </EmptyView>
        ) : (
          <ErrorView error={product.error} onRetry={() => void product.refetch()} />
        )}
      </div>
    )
  }

  const dish = product.data
  const name = localize(dish.name)
  const rating = dish.average_rating === null ? null : Number(dish.average_rating)

  return (
    <div className="page">
      <nav aria-label={t.dish.breadcrumb} className={styles.breadcrumb}>
        <Link to="/menu">{t.nav.menu}</Link>
        {dish.category && (
          <>
            <span aria-hidden="true">/</span>
            <Link to={`/menu?category=${dish.category.slug}`}>{localize(dish.category.name)}</Link>
          </>
        )}
        <span aria-hidden="true">/</span>
        <span aria-current="page">{name}</span>
      </nav>

      <section className={styles.hero}>
        <img src={dish.image_url} alt={name} className={styles.image} />
        <div className={styles.info}>
          {dish.category && <span className={styles.category}>{localize(dish.category.name)}</span>}
          <h1 className={styles.name}>{name}</h1>
          <div className={styles.rating}>
            <Stars rating={rating} />
            <a href="#reviews">{rating === null ? t.common.noReviews : t.reviews.title}</a>
          </div>
          <span className={styles.price}>{formatPrice(dish.price)}</span>
          <p className={styles.description}>{localize(dish.description)}</p>

          <div className={styles.branches}>
            <span className={styles.label}>{t.dish.availableAt}</span>
            {dish.locations.length > 0 ? (
              <ul className={styles.chips}>
                {dish.locations.map((location) => (
                  <li key={location.id} className={styles.chip}>
                    <span aria-hidden="true">✓</span> {localize(location.name)}
                  </li>
                ))}
              </ul>
            ) : (
              <p className={styles.muted}>{t.dish.notServed}</p>
            )}
          </div>

          <div className={styles.buy}>
            <QuantityStepper value={quantity} onChange={setQuantity} label={t.dish.quantity} />
            <Button
              size="lg"
              className={styles.addButton}
              disabled={adding}
              onClick={async () => {
                setAdding(true)
                await addToCart(dish, quantity)
                setAdding(false)
              }}
            >
              {interpolate(t.dish.addFor, {
                price: formatPrice(Number(dish.price) * quantity),
              })}
            </Button>
          </div>
        </div>
      </section>

      <ReviewSection slug={dish.slug} />
    </div>
  )
}
