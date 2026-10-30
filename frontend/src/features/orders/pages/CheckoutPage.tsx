import { useMemo, useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useQuery } from '@tanstack/react-query'
import { useForm, useWatch } from 'react-hook-form'
import { Link, useNavigate } from 'react-router'
import { z } from 'zod'
import { ChoiceCard } from '@/components/form/ChoiceCard'
import { FormError } from '@/components/form/FormError'
import { TextAreaField } from '@/components/form/TextAreaField'
import { TextField } from '@/components/form/TextField'
import { Button, ButtonLink } from '@/components/ui/Button'
import { EmptyView, ErrorView, Loading } from '@/components/ui/StatusView'
import { useToast } from '@/components/ui/toastContext'
import { RequireAuth } from '@/features/auth/RequireAuth'
import type { User } from '@/features/auth/schemas'
import { useServerErrors } from '@/features/auth/useFieldErrors'
import { authRules } from '@/features/auth/validation'
import { OrderSummary } from '@/features/cart/components/OrderSummary'
import type { Cart } from '@/features/cart/schemas'
import { useCart } from '@/features/cart/useCart'
import { catalogQueries } from '@/features/catalog/queries'
import type { Location } from '@/features/catalog/schemas'
import { useI18n } from '@/i18n/context'
import { useLocalize } from '@/i18n/useLocalize'
import { formatVnd, interpolate } from '@/lib/format'
import { usePlaceOrder } from '../api'
import { PromoCodeField } from '../components/PromoCodeField'
import { PAYMENT_METHODS, type PromoQuote } from '../schemas'
import styles from './CheckoutPage.module.css'

export function CheckoutPage() {
  const { t } = useI18n()
  const { cart, error } = useCart()
  const locations = useQuery(catalogQueries.locations())

  return (
    <RequireAuth>
      {(user) => {
        if (error && !cart) return <ErrorView error={error} />
        if (locations.error) return <ErrorView error={locations.error} />
        if (!cart || !locations.data) return <Loading />
        if (cart.items.length === 0) {
          return (
            <div className="page">
              <EmptyView title={t.cart.emptyTitle}>
                <ButtonLink to="/menu">{t.cart.browse}</ButtonLink>
              </EmptyView>
            </div>
          )
        }
        return <CheckoutForm user={user} cart={cart} locations={locations.data} />
      }}
    </RequireAuth>
  )
}

/** Dishes in the cart that `location` does not serve. */
function missingAt(cart: Cart, locationId: number) {
  return cart.items
    .map((line) => line.product)
    .filter((product) => !product.locations.some((location) => location.id === locationId))
}

function CheckoutForm({
  user,
  cart,
  locations,
}: {
  user: User
  cart: Cart
  locations: Location[]
}) {
  const { t } = useI18n()
  const localize = useLocalize()
  const navigate = useNavigate()
  const toast = useToast()
  const placeOrder = usePlaceOrder()
  const [formError, setFormError] = useState<string>()
  const [promo, setPromo] = useState<PromoQuote>()

  const schema = useMemo(() => {
    const rules = authRules(t)
    return z.object({
      delivery_name: rules.name,
      delivery_phone: rules.phone,
      delivery_address: z.string().trim().min(5, t.checkout.addressShort).max(500),
      delivery_note: z
        .string()
        .trim()
        .max(500, interpolate(t.validation.tooLong, { max: 500 })),
      location_id: z.coerce.number<string>().int(),
      payment_method: z.enum(PAYMENT_METHODS),
    })
  }, [t])

  // Start on the first branch that can cook everything, so most customers need not choose.
  const firstServing = locations.find((location) => missingAt(cart, location.id).length === 0)
  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      delivery_name: user.name,
      delivery_phone: user.phone,
      delivery_address: '',
      delivery_note: '',
      location_id: String((firstServing ?? locations[0])?.id ?? ''),
      payment_method: 'COD' as const,
    },
  })
  const serverError = useServerErrors(form, {})
  const errors = form.formState.errors
  const [locationId, method] = useWatch({
    control: form.control,
    name: ['location_id', 'payment_method'],
  })
  const branch = locations.find((location) => String(location.id) === locationId)
  const missing = branch ? missingAt(cart, branch.id) : []

  return (
    <div className="page">
      <Link to="/cart" className={styles.back}>
        {t.checkout.back}
      </Link>
      <h1 className={styles.title}>{t.checkout.title}</h1>

      <form
        className={styles.layout}
        noValidate
        onSubmit={form.handleSubmit(async (values) => {
          setFormError(undefined)
          try {
            const order = await placeOrder.mutateAsync({ ...values, promo_code: promo?.code })
            if (order.payment_method === 'MOMO') {
              navigate(`/orders/${order.id}/pay`, { replace: true })
            } else {
              toast(interpolate(t.checkout.placed, { id: order.id }))
              navigate(`/account?order=${order.id}`, { replace: true })
            }
          } catch (error) {
            setFormError(serverError(error))
          }
        })}
      >
        <div className={styles.steps}>
          <fieldset className={styles.step}>
            <legend className={styles.legend}>
              <span className={styles.number}>1</span>
              {t.checkout.deliveryTitle}
            </legend>
            <div className={styles.pair}>
              <TextField
                label={t.checkout.name}
                autoComplete="name"
                error={errors.delivery_name?.message}
                {...form.register('delivery_name')}
              />
              <TextField
                label={t.checkout.phone}
                type="tel"
                inputMode="numeric"
                autoComplete="tel"
                error={errors.delivery_phone?.message}
                {...form.register('delivery_phone')}
              />
            </div>
            <TextField
              label={t.checkout.address}
              autoComplete="street-address"
              placeholder={t.checkout.addressPlaceholder}
              error={errors.delivery_address?.message}
              {...form.register('delivery_address')}
            />
            <TextAreaField
              label={t.checkout.note}
              placeholder={t.checkout.notePlaceholder}
              error={errors.delivery_note?.message}
              {...form.register('delivery_note')}
            />
          </fieldset>

          <fieldset className={styles.step}>
            <legend className={styles.legend}>
              <span className={styles.number}>2</span>
              {t.checkout.branchTitle}
            </legend>
            <p className={styles.hint}>{t.checkout.branchHint}</p>
            <div className={styles.choices}>
              {locations.map((location) => (
                <ChoiceCard
                  key={location.id}
                  value={String(location.id)}
                  label={localize(location.name)}
                  hint={localize(location.address)}
                  {...form.register('location_id')}
                />
              ))}
            </div>
            {branch && missing.length > 0 && (
              <p role="alert" className={styles.alert}>
                {interpolate(t.checkout.unavailable, {
                  dishes: missing.map((product) => localize(product.name)).join(', '),
                  branch: localize(branch.name),
                })}
              </p>
            )}
          </fieldset>

          <fieldset className={styles.step}>
            <legend className={styles.legend}>
              <span className={styles.number}>3</span>
              {t.checkout.payTitle}
            </legend>
            <div className={styles.choices}>
              <ChoiceCard
                value="COD"
                label={t.paymentMethod.COD}
                hint={t.checkout.codHint}
                {...form.register('payment_method')}
              />
              <ChoiceCard
                value="MOMO"
                label={
                  <>
                    <span aria-hidden="true" className={styles.momoMark}>
                      mo
                    </span>
                    {t.paymentMethod.MOMO}
                  </>
                }
                hint={t.checkout.momoHint}
                {...form.register('payment_method')}
              />
            </div>
          </fieldset>
        </div>

        <OrderSummary
          title={t.checkout.summary}
          subtotal={cart.total_price}
          discount={promo && { code: promo.code, amount: promo.discount }}
          lines={
            <ul className={styles.lines}>
              {cart.items.map(({ product, quantity, subtotal }) => (
                <li key={product.id} className={styles.lineItem}>
                  <img src={product.image_url} alt="" className={styles.thumb} />
                  <span className={styles.lineName}>
                    {localize(product.name)} <span className={styles.qty}>× {quantity}</span>
                  </span>
                  <strong>{formatVnd(subtotal)}</strong>
                </li>
              ))}
            </ul>
          }
        >
          <PromoCodeField applied={promo} onChange={setPromo} />
          <FormError message={formError} />
          <Button
            type="submit"
            size="lg"
            block
            variant={method === 'MOMO' ? 'momo' : 'primary'}
            disabled={missing.length > 0 || form.formState.isSubmitting}
          >
            {method === 'MOMO' ? t.checkout.placeMomo : t.checkout.placeCod}
          </Button>
          <p className={styles.terms}>{t.checkout.terms}</p>
        </OrderSummary>
      </form>
    </div>
  )
}
