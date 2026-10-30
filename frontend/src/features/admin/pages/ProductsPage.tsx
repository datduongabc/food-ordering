import { useQuery } from '@tanstack/react-query'
import { TextField } from '@/components/form/TextField'
import { Badge } from '@/components/ui/Badge'
import { Button, ButtonLink } from '@/components/ui/Button'
import { EmptyView, ErrorView, Loading } from '@/components/ui/StatusView'
import { useToast } from '@/components/ui/toastContext'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { useLocalize } from '@/i18n/useLocalize'
import { formatVnd, interpolate } from '@/lib/format'
import { adminQueries, useSetProductHidden } from '../api'
import type { AdminProduct } from '../schemas'
import { useUrlFilters } from '../useUrlFilters'
import shared from '../admin.module.css'
import styles from './ProductsPage.module.css'

/** Accent- and case-blind, so "pho" finds "Phở". */
function fold(text: string): string {
  return text
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .replace(/đ/gi, 'd')
    .toLowerCase()
}

export function AdminProductsPage() {
  const { t } = useI18n()
  const labels = t.admin.products
  const { params, update } = useUrlFilters()
  const query = params.get('q') ?? ''
  const showHidden = params.get('hidden') === '1'
  const products = useQuery(adminQueries.products())

  // The API returns every dish at once (a restaurant menu is small), so filtering is local.
  const needle = fold(query.trim())
  const visible = (products.data ?? []).filter(
    (product) =>
      (showHidden || product.deleted_at === null) &&
      (!needle || fold(`${product.name.vi} ${product.name.en}`).includes(needle)),
  )

  let body
  if (products.error) {
    body = <ErrorView error={products.error} onRetry={() => products.refetch()} />
  } else if (!products.data) {
    body = <Loading />
  } else if (visible.length === 0) {
    body = <EmptyView title={t.admin.noResults} />
  } else {
    body = (
      <div className={shared.tableWrap}>
        <table className={shared.table}>
          <thead>
            <tr>
              <th scope="col">{labels.dish}</th>
              <th scope="col">{labels.category}</th>
              <th scope="col" className={shared.num}>
                {labels.price}
              </th>
              <th scope="col">{labels.branches}</th>
              <th scope="col">{t.admin.actions}</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((product) => (
              <ProductRow key={product.id} product={product} />
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  return (
    <>
      <div className={shared.head}>
        <h1 className={shared.title}>{labels.title}</h1>
        <ButtonLink to="/admin/products/new">{labels.add}</ButtonLink>
      </div>
      <div className={shared.filters}>
        <TextField
          label={labels.search}
          type="search"
          value={query}
          onChange={(event) => update({ q: event.target.value })}
        />
        <label className={shared.check}>
          <input
            type="checkbox"
            checked={showHidden}
            onChange={(event) => update({ hidden: event.target.checked ? '1' : undefined })}
          />
          {labels.showHidden}
        </label>
        {products.data && (
          <span className={shared.count}>
            {interpolate(t.admin.total, { count: visible.length })}
          </span>
        )}
      </div>
      {body}
    </>
  )
}

function ProductRow({ product }: { product: AdminProduct }) {
  const { t } = useI18n()
  const labels = t.admin.products
  const localize = useLocalize()
  const toast = useToast()
  const errorMessage = useErrorMessage()
  const setHidden = useSetProductHidden()
  const hidden = product.deleted_at !== null
  const name = localize(product.name)

  return (
    <tr data-inactive={hidden}>
      <td data-label={labels.dish}>
        <div className={styles.dish}>
          <img src={product.thumbnail_url} alt="" className={styles.thumb} />
          <div className={shared.cellStack}>
            <strong>{name}</strong>
            <span className={shared.muted}>/{product.slug}</span>
            {hidden && <Badge tone="stone">{labels.hidden}</Badge>}
          </div>
        </div>
      </td>
      <td data-label={labels.category}>
        {product.category ? localize(product.category.name) : '—'}
      </td>
      <td data-label={labels.price} className={shared.num}>
        {formatVnd(product.price)}
      </td>
      <td data-label={labels.branches}>
        {product.locations.map((location) => localize(location.name)).join(', ')}
      </td>
      <td data-label={t.admin.actions}>
        <div className={shared.rowActions}>
          <ButtonLink
            to={`/admin/products/${product.id}`}
            variant="outline"
            className={shared.small}
            aria-label={`${t.admin.edit} ${name}`}
          >
            {t.admin.edit}
          </ButtonLink>
          <Button
            variant={hidden ? 'green' : 'danger'}
            className={shared.small}
            disabled={setHidden.isPending}
            aria-label={`${hidden ? labels.restore : labels.hide} ${name}`}
            onClick={() =>
              setHidden.mutate(
                { id: product.id, hidden: !hidden },
                {
                  onSuccess: () =>
                    toast(
                      interpolate(hidden ? labels.restoredToast : labels.hiddenToast, { name }),
                    ),
                  onError: (error) => toast(errorMessage(error)),
                },
              )
            }
          >
            {hidden ? labels.restore : labels.hide}
          </Button>
        </div>
      </td>
    </tr>
  )
}
