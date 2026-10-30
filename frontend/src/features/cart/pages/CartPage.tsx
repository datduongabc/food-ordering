import { Link } from 'react-router'
import { ButtonLink } from '@/components/ui/Button'
import { QuantityStepper } from '@/components/ui/QuantityStepper'
import { ErrorView, Loading } from '@/components/ui/StatusView'
import { useToast } from '@/components/ui/toastContext'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { useLocalize } from '@/i18n/useLocalize'
import { formatVnd, interpolate } from '@/lib/format'
import { MAX_QUANTITY } from '../schemas'
import { useCart, useCartActions } from '../useCart'
import { OrderSummary } from '../components/OrderSummary'
import styles from './CartPage.module.css'

export function CartPage() {
  const { t } = useI18n()
  const localize = useLocalize()
  const toast = useToast()
  const errorMessage = useErrorMessage()
  const { cart, error, signedIn } = useCart()
  const actions = useCartActions()

  async function run(action: () => Promise<unknown>) {
    try {
      await action()
    } catch (failure) {
      toast(errorMessage(failure))
    }
  }

  if (error && !cart) return <ErrorView error={error} />
  if (!cart) return <Loading />

  if (cart.items.length === 0) {
    return (
      <div className="page">
        <h1 className={styles.title}>{t.cart.title}</h1>
        <div className={styles.empty}>
          <p className="kicker">{t.cart.emptyTitle}</p>
          <p className={styles.muted}>{t.cart.emptyBody}</p>
          <ButtonLink to="/menu" size="lg">
            {t.cart.browse}
          </ButtonLink>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <h1 className={styles.title}>{t.cart.title}</h1>
      <p className={styles.subtitle}>{interpolate(t.cart.count, { count: cart.total_count })}</p>

      <div className={styles.layout}>
        <section aria-label={t.cart.itemsLabel} className={styles.items}>
          {cart.items.map(({ product, quantity, subtotal }) => {
            const name = localize(product.name)
            return (
              <article key={product.id} className={styles.line}>
                <Link to={`/menu/${product.slug}`} tabIndex={-1} aria-hidden="true">
                  <img src={product.thumbnail_url} alt="" className={styles.image} />
                </Link>
                <div className={styles.info}>
                  <h2 className={styles.name}>
                    <Link to={`/menu/${product.slug}`}>{name}</Link>
                  </h2>
                  <span className={styles.muted}>
                    {interpolate(t.cart.unitPrice, { price: formatVnd(product.price) })}
                  </span>
                  <button
                    type="button"
                    className={styles.remove}
                    aria-label={interpolate(t.cart.removeLabel, { name })}
                    disabled={actions.isPending}
                    onClick={() => run(() => actions.remove(product.id))}
                  >
                    {t.cart.remove}
                  </button>
                </div>
                <QuantityStepper
                  label={interpolate(t.cart.quantityOf, { name })}
                  value={quantity}
                  max={MAX_QUANTITY}
                  disabled={actions.isPending}
                  onChange={(next) => run(() => actions.setQuantity(product.id, next))}
                />
                <strong className={styles.subtotal}>{formatVnd(subtotal)}</strong>
              </article>
            )
          })}
          <div className={styles.footer}>
            <Link to="/menu" className={styles.continue}>
              {t.cart.continue}
            </Link>
            <button
              type="button"
              className={styles.clear}
              disabled={actions.isPending}
              onClick={() => run(actions.clear)}
            >
              {t.cart.clear}
            </button>
          </div>
        </section>

        <OrderSummary title={t.cart.summary} subtotal={cart.total_price}>
          <ButtonLink to="/checkout" size="lg" block>
            {t.cart.checkout}
          </ButtonLink>
          {!signedIn && <p className={styles.note}>{t.cart.guestNote}</p>}
        </OrderSummary>
      </div>
    </div>
  )
}
