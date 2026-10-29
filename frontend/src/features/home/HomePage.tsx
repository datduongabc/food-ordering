import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { ButtonLink } from '@/components/ui/Button'
import { Stars } from '@/components/ui/Stars'
import { ProductCard } from '@/features/catalog/components/ProductCard'
import { catalogQueries } from '@/features/catalog/queries'
import { reviewQueries } from '@/features/reviews/queries'
import { useI18n } from '@/i18n/context'
import { formatPrice } from '@/lib/format'
import styles from './HomePage.module.css'

const PICKS = 4

export function HomePage() {
  const { t } = useI18n()
  const featured = useQuery(catalogQueries.featured())
  // One extra so the featured dish can be left out without leaving a gap.
  const picks = useQuery(catalogQueries.products({ page: 1, sort: 'default', pageSize: PICKS + 1 }))
  const reviews = useQuery(reviewQueries.top(3))
  const dish = featured.data
  const pickItems = picks.data?.items.filter((item) => item.id !== dish?.id).slice(0, PICKS)

  return (
    <>
      <section className={styles.hero}>
        <div className={styles.heroText}>
          <p className={styles.heroKicker}>{t.home.heroKicker}</p>
          <h1 className={styles.heroTitle}>{t.home.heroTitle}</h1>
          <p className={styles.heroBody}>{t.home.heroBody}</p>
          <div className={styles.actions}>
            <ButtonLink to="/menu" size="lg">
              {t.home.ctaMenu}
            </ButtonLink>
          </div>
        </div>
        {dish && (
          <figure className={styles.featured}>
            {/* The caption carries the link text; the image link is a duplicate mouse target. */}
            <Link to={`/menu/${dish.slug}`} tabIndex={-1} aria-hidden="true">
              <img src={dish.image_url} alt="" className={styles.featuredImage} />
            </Link>
            <div className={styles.tag}>
              <span className={styles.tagLabel}>{t.home.featuredTag}</span>
              <span className={styles.tagPrice}>{formatPrice(dish.price)}</span>
            </div>
            <figcaption className={styles.caption}>
              <Link to={`/menu/${dish.slug}`}>{dish.name}</Link>
            </figcaption>
          </figure>
        )}
      </section>

      <section aria-labelledby="picks-title" className={styles.section}>
        <div className={styles.sectionHead}>
          <div className={styles.sectionTitles}>
            <span className="kicker">{t.home.picksKicker}</span>
            <h2 id="picks-title" className={styles.sectionTitle}>
              {t.home.picksTitle}
            </h2>
          </div>
          <Link to="/menu" className={styles.more}>
            {t.home.fullMenu}
          </Link>
        </div>
        <div className={styles.grid}>
          {pickItems?.map((product) => (
            <ProductCard key={product.id} product={product} headingLevel={3} />
          ))}
        </div>
      </section>

      {/* Hidden until guests have written reviews, rather than showing placeholder quotes. */}
      {reviews.data && reviews.data.length > 0 && (
        <section aria-labelledby="reviews-title" className={styles.section}>
          <div className={styles.sectionTitles}>
            <span className="kicker">{t.home.reviewsKicker}</span>
            <h2 id="reviews-title" className={styles.sectionTitle}>
              {t.home.reviewsTitle}
            </h2>
          </div>
          <div className={styles.quotes}>
            {reviews.data.map((review) => (
              <blockquote key={review.id} className={styles.quote}>
                <Stars rating={review.rating} />
                <p className={styles.quoteText}>{review.comment}</p>
                <footer className={styles.quoteFooter}>
                  <strong>{review.user_name}</strong> ·{' '}
                  <Link to={`/menu/${review.product_slug}`}>{review.product_name}</Link>
                </footer>
              </blockquote>
            ))}
          </div>
        </section>
      )}
    </>
  )
}
