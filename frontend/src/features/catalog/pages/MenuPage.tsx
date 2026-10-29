import { useCallback, useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router'
import { EmptyView, ErrorView, Loading } from '@/components/ui/StatusView'
import { useI18n } from '@/i18n/context'
import { useLocalize } from '@/i18n/useLocalize'
import { interpolate } from '@/lib/format'
import { ProductCard } from '../components/ProductCard'
import { Pagination } from '../components/Pagination'
import { catalogQueries } from '../queries'
import { PRODUCT_SORTS, productSortSchema, type Product } from '../schemas'
import styles from './MenuPage.module.css'

const SEARCH_DELAY_MS = 300

function useMenuParams() {
  const [params, setParams] = useSearchParams()
  const page = Math.max(1, Number.parseInt(params.get('page') ?? '1', 10) || 1)
  const sort = productSortSchema.catch('default').parse(params.get('sort') ?? 'default')
  const category = params.get('category') ?? undefined
  const query = (params.get('q') ?? '').trim()

  // Every filter lives in the URL so a filtered menu can be shared, reloaded and navigated back to.
  const update = useCallback(
    (changes: Record<string, string | undefined>) =>
      setParams(
        (current) => {
          const next = new URLSearchParams(current)
          for (const [key, value] of Object.entries(changes)) {
            if (value === undefined || value === '') next.delete(key)
            else next.set(key, value)
          }
          if (!('page' in changes)) next.delete('page')
          return next
        },
        { replace: 'q' in changes },
      ),
    [setParams],
  )
  return { page, sort, category, query, update }
}

function DishGrid({ products }: { products: Product[] }) {
  return (
    <div className={styles.grid}>
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  )
}

export function MenuPage() {
  const { t } = useI18n()
  const localize = useLocalize()
  const { page, sort, category, query, update } = useMenuParams()
  const [searchText, setSearchText] = useState(query)

  useEffect(() => {
    const trimmed = searchText.trim()
    if (trimmed === query) return
    const timer = window.setTimeout(() => update({ q: trimmed }), SEARCH_DELAY_MS)
    return () => window.clearTimeout(timer)
  }, [searchText, query, update])

  const categories = useQuery(catalogQueries.categories())
  const searching = query.length > 0
  const list = useQuery({
    ...catalogQueries.products({ page, sort, category }),
    enabled: !searching,
  })
  const search = useQuery(catalogQueries.search(query))
  const active = searching ? search : list
  const products = searching ? search.data : list.data?.items

  return (
    <div className="page">
      <div className={styles.top}>
        <div className={styles.heading}>
          <span className={styles.kicker}>{t.menu.kicker}</span>
          <h1 className={styles.title}>{t.menu.title}</h1>
        </div>
        <label className={styles.search}>
          <svg
            aria-hidden="true"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="M20 20l-3.5-3.5" />
          </svg>
          <span className="visually-hidden">{t.menu.search}</span>
          <input
            type="search"
            value={searchText}
            onChange={(event) => setSearchText(event.target.value)}
            placeholder={t.menu.search}
            maxLength={100}
          />
        </label>
      </div>

      {searching ? (
        <p className={styles.resultsFor} aria-live="polite">
          {interpolate(t.menu.searchResults, { query })}
        </p>
      ) : (
        <div className={styles.toolbar}>
          <div role="group" aria-label={t.menu.category} className={styles.tabs}>
            <button
              type="button"
              aria-pressed={!category}
              className={styles.tab}
              onClick={() => update({ category: undefined })}
            >
              {t.menu.allCategories}
            </button>
            {categories.data?.map((item) => (
              <button
                key={item.id}
                type="button"
                aria-pressed={category === item.slug}
                className={styles.tab}
                onClick={() => update({ category: item.slug })}
              >
                {localize(item.name)}
              </button>
            ))}
          </div>
          <label className={styles.sort}>
            {t.menu.sort}
            <select value={sort} onChange={(event) => update({ sort: event.target.value })}>
              {PRODUCT_SORTS.map((value) => (
                <option key={value} value={value}>
                  {t.menu.sorts[value]}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}

      {active.isPending && !products ? (
        <Loading />
      ) : active.isError ? (
        <ErrorView error={active.error} onRetry={() => void active.refetch()} />
      ) : products && products.length > 0 ? (
        <div aria-busy={active.isFetching}>
          <DishGrid products={products} />
        </div>
      ) : (
        <EmptyView title={t.menu.emptyTitle}>
          <p>{searching ? interpolate(t.menu.emptySearch, { query }) : t.menu.emptyCategory}</p>
        </EmptyView>
      )}

      {!searching && list.data && list.data.total_pages > 1 && (
        <Pagination
          page={list.data.page}
          totalPages={list.data.total_pages}
          onChange={(next) => {
            update({ page: String(next) })
            window.scrollTo({ top: 0 })
          }}
        />
      )}
    </div>
  )
}
