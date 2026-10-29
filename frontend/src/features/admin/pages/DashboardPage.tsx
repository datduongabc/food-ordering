import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { Stars } from '@/components/ui/Stars'
import { ErrorView, Loading } from '@/components/ui/StatusView'
import { useI18n } from '@/i18n/context'
import { useLocalize } from '@/i18n/useLocalize'
import { formatDateTime, formatVnd, interpolate } from '@/lib/format'
import { adminQueries } from '../api'
import { FilterChips } from '../components/FilterChips'
import { RevenueChart } from '../components/RevenueChart'
import type { DishSales } from '../schemas'
import { oneOf, useUrlFilters } from '../useUrlFilters'
import shared from '../admin.module.css'
import styles from './DashboardPage.module.css'

const RANGES = ['7', '30', '90'] as const

export function DashboardPage() {
  const { t } = useI18n()
  const labels = t.admin.dashboard
  const { params, update } = useUrlFilters()
  const days = Number(oneOf(RANGES, params.get('days')) ?? '7')

  return (
    <>
      <div className={shared.head}>
        <h1 className={shared.title}>{labels.title}</h1>
      </div>
      <Summary />
      <div className={shared.filters}>
        <FilterChips
          label={labels.range}
          options={RANGES.map((range) => ({
            value: range,
            label: interpolate(labels.lastDays, { days: range }),
          }))}
          value={String(days) as (typeof RANGES)[number]}
          onChange={(value) => update({ days: value === '7' ? undefined : value })}
        />
      </div>
      <div className={styles.grid}>
        <Trend days={days} />
        <TopDishes days={days} />
        <Payments days={days} />
        <Ratings />
      </div>
    </>
  )
}

function Summary() {
  const { t } = useI18n()
  const labels = t.admin.dashboard
  const summary = useQuery(adminQueries.dashboard())
  if (summary.error) return <ErrorView error={summary.error} onRetry={() => summary.refetch()} />
  if (!summary.data) return <Loading />
  const data = summary.data

  const tiles = [
    {
      label: labels.revenue,
      value: formatVnd(data.completed_revenue),
      hint: interpolate(labels.revenueHint, { count: data.completed_orders }),
    },
    { label: labels.average, value: formatVnd(data.average_order_value) },
    {
      label: labels.pendingOrders,
      value: data.pending_orders,
      hint: interpolate(labels.ofOrders, { count: data.total_orders }),
      to: '/admin/orders?status=PENDING',
    },
    {
      label: labels.pendingBookings,
      value: data.pending_reservations,
      hint: interpolate(labels.ofBookings, { count: data.total_reservations }),
      to: '/admin/reservations?status=PENDING',
    },
    { label: labels.activeDishes, value: data.active_products, to: '/admin/products' },
    { label: labels.customers, value: data.customers, to: '/admin/users' },
  ]

  return (
    <dl className={styles.tiles}>
      {tiles.map((tile) => (
        <div key={tile.label} className={styles.tile}>
          <dt className={styles.tileLabel}>
            {tile.to ? <Link to={tile.to}>{tile.label}</Link> : tile.label}
          </dt>
          <dd className={styles.tileValue}>{tile.value}</dd>
          {tile.hint && <dd className={shared.muted}>{tile.hint}</dd>}
        </div>
      ))}
    </dl>
  )
}

function Trend({ days }: { days: number }) {
  const { t } = useI18n()
  const labels = t.admin.dashboard
  const trend = useQuery(adminQueries.revenue(days))
  return (
    <section className={`${shared.card} ${styles.wide}`} aria-labelledby="trend-title">
      <div>
        <h2 id="trend-title" className={shared.cardTitle}>
          {labels.trendTitle}
        </h2>
        {trend.data && (
          <p className={shared.muted}>
            {interpolate(labels.trendSummary, {
              revenue: formatVnd(trend.data.total_revenue),
              orders: trend.data.total_orders,
            })}
          </p>
        )}
      </div>
      {trend.error ? (
        <ErrorView error={trend.error} onRetry={() => trend.refetch()} />
      ) : trend.data ? (
        <RevenueChart trend={trend.data} />
      ) : (
        <Loading />
      )}
    </section>
  )
}

function DishList({
  title,
  dishes,
  show,
}: {
  title: string
  dishes: DishSales[]
  show: 'quantity' | 'revenue'
}) {
  const { t } = useI18n()
  const localize = useLocalize()
  return (
    <div className={styles.dishList}>
      <h3 className={styles.listTitle}>{title}</h3>
      <ol className={styles.ranked}>
        {dishes.map((dish) => (
          <li key={dish.product_id} className={styles.rankedItem}>
            <Link to={`/menu/${dish.slug}`} className={styles.dishName}>
              {localize(dish.name)}
            </Link>
            <span className={shared.num}>
              {show === 'quantity'
                ? interpolate(t.admin.dashboard.portions, { count: dish.quantity })
                : formatVnd(dish.revenue)}
            </span>
          </li>
        ))}
      </ol>
    </div>
  )
}

function TopDishes({ days }: { days: number }) {
  const { t } = useI18n()
  const labels = t.admin.dashboard
  const dishes = useQuery(adminQueries.topDishes(days))
  return (
    <section className={`${shared.card} ${styles.wide}`} aria-labelledby="dishes-title">
      <h2 id="dishes-title" className={shared.cardTitle}>
        {labels.dishesTitle}
      </h2>
      {dishes.error ? (
        <ErrorView error={dishes.error} onRetry={() => dishes.refetch()} />
      ) : dishes.data ? (
        <div className={styles.dishLists}>
          <DishList title={labels.byQuantity} dishes={dishes.data.by_quantity} show="quantity" />
          <DishList title={labels.byRevenue} dishes={dishes.data.by_revenue} show="revenue" />
          <DishList title={labels.leastSold} dishes={dishes.data.least_sold} show="quantity" />
        </div>
      ) : (
        <Loading />
      )}
    </section>
  )
}

function Payments({ days }: { days: number }) {
  const { t } = useI18n()
  const labels = t.admin.dashboard
  const payments = useQuery(adminQueries.payments(days))
  const data = payments.data
  return (
    <section className={shared.card} aria-labelledby="payments-title">
      <h2 id="payments-title" className={shared.cardTitle}>
        {labels.paymentsTitle}
      </h2>
      {payments.error ? (
        <ErrorView error={payments.error} onRetry={() => payments.refetch()} />
      ) : data ? (
        <dl className={styles.facts}>
          <div className={styles.fact}>
            <dt>{labels.cod}</dt>
            <dd className={styles.factValue}>{data.cod_orders}</dd>
          </div>
          <div className={styles.fact}>
            <dt>{labels.momo}</dt>
            <dd className={styles.factValue}>{data.momo_orders}</dd>
          </div>
          <div className={`${styles.fact} ${styles.factWide}`}>
            <dt>{labels.momoRate}</dt>
            <dd className={styles.factValue}>
              {data.momo.success_rate === null
                ? labels.noAttempts
                : `${Math.round(data.momo.success_rate * 100)}%`}
            </dd>
            <dd className={shared.muted}>
              {interpolate(labels.momoRateBody, {
                paid: data.momo.paid,
                failed: data.momo.failed,
              })}
            </dd>
          </div>
        </dl>
      ) : (
        <Loading />
      )}
    </section>
  )
}

function Ratings() {
  const { t, lang } = useI18n()
  const localize = useLocalize()
  const labels = t.admin.dashboard
  const ratings = useQuery(adminQueries.ratings())
  const data = ratings.data
  return (
    <section className={shared.card} aria-labelledby="ratings-title">
      <h2 id="ratings-title" className={shared.cardTitle}>
        {labels.ratingsTitle}
      </h2>
      {ratings.error ? (
        <ErrorView error={ratings.error} onRetry={() => ratings.refetch()} />
      ) : !data ? (
        <Loading />
      ) : data.latest_reviews.length === 0 ? (
        <p className={shared.muted}>{labels.noReviews}</p>
      ) : (
        <>
          <div className={styles.dishList}>
            <h3 className={styles.listTitle}>{labels.lowestRated}</h3>
            <ol className={styles.ranked}>
              {data.lowest_rated.map((dish) => (
                <li key={dish.product_id} className={styles.rankedItem}>
                  <Link to={`/menu/${dish.slug}`} className={styles.dishName}>
                    {localize(dish.name)}
                  </Link>
                  <span className={styles.rating}>
                    <Stars rating={Number(dish.average_rating)} />
                    <span className={shared.muted}>
                      {interpolate(t.common.reviewCount, { count: dish.review_count })}
                    </span>
                  </span>
                </li>
              ))}
            </ol>
          </div>
          <div className={styles.dishList}>
            <h3 className={styles.listTitle}>{labels.latestReviews}</h3>
            <ul className={styles.reviews}>
              {data.latest_reviews.map((review) => (
                <li key={review.id} className={styles.review}>
                  <span className={styles.reviewHead}>
                    <Stars rating={review.rating} />
                    <span className={shared.muted}>{formatDateTime(review.created_at, lang)}</span>
                  </span>
                  <span className={styles.reviewBy}>
                    {interpolate(labels.reviewBy, {
                      name: review.user_name,
                      dish: localize(review.product_name),
                    })}
                  </span>
                  <span>{review.comment}</span>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </section>
  )
}
