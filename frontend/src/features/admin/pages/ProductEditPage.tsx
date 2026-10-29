import { useMemo, useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useQuery } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router'
import { z } from 'zod'
import { FormError } from '@/components/form/FormError'
import { SelectField } from '@/components/form/SelectField'
import { TextAreaField } from '@/components/form/TextAreaField'
import { TextField } from '@/components/form/TextField'
import { Button } from '@/components/ui/Button'
import { ErrorView, Loading } from '@/components/ui/StatusView'
import { useToast } from '@/components/ui/toastContext'
import { useServerErrors } from '@/features/auth/useFieldErrors'
import { catalogQueries } from '@/features/catalog/queries'
import type { Category, Location } from '@/features/catalog/schemas'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { useLocalize } from '@/i18n/useLocalize'
import { interpolate } from '@/lib/format'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { adminQueries, useSaveProduct, useUploadProductImage } from '../api'
import type { AdminProduct } from '../schemas'
import shared from '../admin.module.css'
import styles from './ProductsPage.module.css'

/** `/admin/products/new` adds a dish; `/admin/products/:id` edits one. */
export function ProductEditPage() {
  const { id } = useParams()
  const productId = id === undefined ? undefined : Number(id)
  const products = useQuery(adminQueries.products())
  const categories = useQuery(catalogQueries.categories())
  const locations = useQuery(catalogQueries.locations())

  if (productId !== undefined && !(Number.isInteger(productId) && productId > 0)) {
    return <NotFoundPage />
  }
  const error = products.error ?? categories.error ?? locations.error
  if (error) return <ErrorView error={error} />
  if (!products.data || !categories.data || !locations.data) return <Loading />

  const product = products.data.find((item) => item.id === productId)
  if (productId !== undefined && !product) return <NotFoundPage />
  return (
    <ProductForm
      key={product?.id ?? 'new'}
      product={product}
      categories={categories.data}
      locations={locations.data}
    />
  )
}

function ProductForm({
  product,
  categories,
  locations,
}: {
  product: AdminProduct | undefined
  categories: Category[]
  locations: Location[]
}) {
  const { t } = useI18n()
  const labels = t.admin.products
  const localize = useLocalize()
  const navigate = useNavigate()
  const toast = useToast()
  const save = useSaveProduct()
  const [formError, setFormError] = useState<string>()

  const schema = useMemo(() => {
    const v = t.validation
    const text = (max: number) =>
      z.string().trim().min(1, v.required).max(max, interpolate(v.tooLong, { max }))
    return z.object({
      name_vi: text(255),
      name_en: text(255),
      description_vi: text(500),
      description_en: text(500),
      slug: z
        .string()
        .trim()
        .regex(/^([a-z0-9]+(-[a-z0-9]+)*)?$/, labels.slugInvalid)
        .max(255),
      // Staff type "250.000" the way prices are printed; only the digits count.
      price: z
        .string()
        .transform((value) => Number(value.replace(/[\s.,]/g, '')))
        .pipe(
          z
            .number()
            .int(labels.priceInvalid)
            .gt(0, labels.priceInvalid)
            .max(100_000_000, labels.priceInvalid),
        ),
      category_id: z.string().min(1, labels.categoryRequired),
      location_ids: z.array(z.string()).min(1, labels.branchesRequired),
    })
  }, [t, labels])

  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      name_vi: product?.name.vi ?? '',
      name_en: product?.name.en ?? '',
      description_vi: product?.description.vi ?? '',
      description_en: product?.description.en ?? '',
      slug: product?.slug ?? '',
      price: product ? String(product.price) : '',
      category_id: String(product?.category?.id ?? ''),
      location_ids: product
        ? product.locations.map((location) => String(location.id))
        : locations.map((location) => String(location.id)),
    },
  })
  const serverError = useServerErrors(form, { slug_taken: 'slug', slug_required: 'slug' })
  const errors = form.formState.errors

  return (
    <>
      <Link to="/admin/products" className={styles.back}>
        {labels.back}
      </Link>
      <div className={shared.head}>
        <h1 className={shared.title}>
          {product
            ? interpolate(labels.editTitle, { name: localize(product.name) })
            : labels.newTitle}
        </h1>
      </div>
      <div className={styles.form}>
        <form
          className={`${shared.card} ${styles.fields}`}
          noValidate
          onSubmit={form.handleSubmit(async (values) => {
            setFormError(undefined)
            const input = {
              name: { vi: values.name_vi, en: values.name_en },
              description: { vi: values.description_vi, en: values.description_en },
              // Blank means "make one from the English name" for a new dish, "keep" for an old one.
              slug: values.slug || undefined,
              price: values.price,
              category_id: Number(values.category_id),
              location_ids: values.location_ids.map(Number),
            }
            try {
              const saved = await save.mutateAsync({ id: product?.id, values: input })
              if (product) {
                toast(t.admin.saved)
              } else {
                toast(interpolate(labels.created, { name: localize(saved.name) }))
                navigate(`/admin/products/${saved.id}`, { replace: true })
              }
            } catch (error) {
              setFormError(serverError(error))
            }
          })}
        >
          <div className={styles.pair}>
            <TextField
              label={labels.nameVi}
              error={errors.name_vi?.message}
              {...form.register('name_vi')}
            />
            <TextField
              label={labels.nameEn}
              error={errors.name_en?.message}
              {...form.register('name_en')}
            />
          </div>
          <div className={styles.pair}>
            <TextAreaField
              label={labels.descriptionVi}
              rows={4}
              error={errors.description_vi?.message}
              {...form.register('description_vi')}
            />
            <TextAreaField
              label={labels.descriptionEn}
              rows={4}
              error={errors.description_en?.message}
              {...form.register('description_en')}
            />
          </div>
          <div className={styles.pair}>
            <TextField
              label={labels.priceLabel}
              inputMode="numeric"
              error={errors.price?.message}
              {...form.register('price')}
            />
            <SelectField
              label={labels.category}
              error={errors.category_id?.message}
              {...form.register('category_id')}
            >
              <option value="">—</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {localize(category.name)}
                </option>
              ))}
            </SelectField>
          </div>
          <TextField
            label={labels.slug}
            placeholder={labels.slugPlaceholder}
            error={errors.slug?.message}
            {...form.register('slug')}
          />
          <fieldset
            className={styles.fieldset}
            aria-invalid={errors.location_ids ? true : undefined}
            aria-describedby={errors.location_ids ? 'branches-error' : undefined}
          >
            <legend className={styles.legend}>{labels.branches}</legend>
            {locations.map((location) => (
              <label key={location.id} className={shared.check}>
                <input type="checkbox" value={location.id} {...form.register('location_ids')} />
                {localize(location.name)}
              </label>
            ))}
            {errors.location_ids && (
              <p id="branches-error" className={styles.error}>
                {errors.location_ids.message}
              </p>
            )}
          </fieldset>
          <FormError message={formError} />
          <div className={shared.rowActions}>
            <Button type="submit" disabled={form.formState.isSubmitting}>
              {t.admin.save}
            </Button>
            <Button variant="outline" onClick={() => navigate('/admin/products')}>
              {t.admin.cancel}
            </Button>
          </div>
        </form>
        <PhotoCard product={product} />
      </div>
    </>
  )
}

function PhotoCard({ product }: { product: AdminProduct | undefined }) {
  const { t } = useI18n()
  const labels = t.admin.products
  const toast = useToast()
  const errorMessage = useErrorMessage()
  const upload = useUploadProductImage()
  const [file, setFile] = useState<File>()
  const [inputKey, setInputKey] = useState(0)

  return (
    <section className={shared.card} aria-labelledby="photo-title">
      <h2 id="photo-title" className={shared.cardTitle}>
        {labels.image}
      </h2>
      {product ? (
        <>
          <img src={product.image_url} alt="" className={styles.photo} />
          <TextField
            key={inputKey}
            label={labels.chooseImage}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(event) => setFile(event.target.files?.[0])}
          />
          <p className={shared.muted}>{labels.imageHint}</p>
          <FormError message={upload.error ? errorMessage(upload.error) : undefined} />
          <Button
            variant="dark"
            disabled={!file || upload.isPending}
            onClick={() =>
              file &&
              upload.mutate(
                { id: product.id, file },
                {
                  onSuccess: () => {
                    setFile(undefined)
                    setInputKey((key) => key + 1)
                    toast(labels.uploaded)
                  },
                },
              )
            }
          >
            {labels.upload}
          </Button>
        </>
      ) : (
        <p className={shared.muted}>{labels.imageNew}</p>
      )}
    </section>
  )
}
