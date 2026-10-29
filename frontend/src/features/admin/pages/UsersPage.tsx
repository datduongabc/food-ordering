import { useMemo, useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useQuery } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { FormError } from '@/components/form/FormError'
import { SelectField } from '@/components/form/SelectField'
import { TextField } from '@/components/form/TextField'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { EmptyView, ErrorView, Loading } from '@/components/ui/StatusView'
import { useToast } from '@/components/ui/toastContext'
import { useCurrentUser } from '@/features/auth/queries'
import { useServerErrors } from '@/features/auth/useFieldErrors'
import { authRules } from '@/features/auth/validation'
import { Pagination } from '@/features/catalog/components/Pagination'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { formatDate, interpolate } from '@/lib/format'
import { adminQueries, useSaveUser, useSetUserActive } from '../api'
import { ROLES, type AdminUser } from '../schemas'
import { useUrlFilters } from '../useUrlFilters'
import shared from '../admin.module.css'
import styles from './ProductsPage.module.css'

export function AdminUsersPage() {
  const { t } = useI18n()
  const labels = t.admin.users
  const { params, page, update } = useUrlFilters()
  const q = (params.get('q') ?? '').trim() || undefined
  const includeDeactivated = params.get('deactivated') === '1'
  const users = useQuery(adminQueries.users({ q, includeDeactivated, page }))
  const [editing, setEditing] = useState<AdminUser | 'new'>()

  let body
  if (users.error) {
    body = <ErrorView error={users.error} onRetry={() => users.refetch()} />
  } else if (!users.data) {
    body = <Loading />
  } else if (users.data.items.length === 0) {
    body = <EmptyView title={t.admin.noResults} />
  } else {
    body = (
      <>
        <div className={shared.tableWrap}>
          <table className={shared.table}>
            <thead>
              <tr>
                <th scope="col">{labels.name}</th>
                <th scope="col">{labels.contact}</th>
                <th scope="col">{labels.role}</th>
                <th scope="col">{labels.joined}</th>
                <th scope="col">{t.admin.actions}</th>
              </tr>
            </thead>
            <tbody>
              {users.data.items.map((user) => (
                <UserRow key={user.id} user={user} onEdit={() => setEditing(user)} />
              ))}
            </tbody>
          </table>
        </div>
        {users.data.total_pages > 1 && (
          <div className={shared.pager}>
            <Pagination
              page={page}
              totalPages={users.data.total_pages}
              onChange={(next) => update({ page: String(next) })}
            />
          </div>
        )}
      </>
    )
  }

  return (
    <>
      <div className={shared.head}>
        <h1 className={shared.title}>{labels.title}</h1>
        <Button onClick={() => setEditing('new')}>{labels.add}</Button>
      </div>
      {editing && (
        <UserForm
          key={editing === 'new' ? 'new' : editing.id}
          user={editing === 'new' ? undefined : editing}
          onDone={() => setEditing(undefined)}
        />
      )}
      <div className={shared.filters}>
        <TextField
          label={labels.search}
          type="search"
          defaultValue={params.get('q') ?? ''}
          onChange={(event) => update({ q: event.target.value })}
        />
        <label className={shared.check}>
          <input
            type="checkbox"
            checked={includeDeactivated}
            onChange={(event) => update({ deactivated: event.target.checked ? '1' : undefined })}
          />
          {labels.showDeactivated}
        </label>
        {users.data && (
          <span className={shared.count}>
            {interpolate(t.admin.total, { count: users.data.total })}
          </span>
        )}
      </div>
      {body}
    </>
  )
}

function UserRow({ user, onEdit }: { user: AdminUser; onEdit: () => void }) {
  const { t, lang } = useI18n()
  const labels = t.admin.users
  const me = useCurrentUser()
  const toast = useToast()
  const errorMessage = useErrorMessage()
  const setActive = useSetUserActive()
  const [confirming, setConfirming] = useState(false)
  const deactivated = user.deleted_at !== null
  const isMe = me?.id === user.id

  function toggle(active: boolean) {
    setActive.mutate(
      { id: user.id, active },
      {
        onSuccess: () => {
          setConfirming(false)
          toast(interpolate(active ? labels.restored : labels.deactivated, { name: user.name }))
        },
        onError: (error) => toast(errorMessage(error)),
      },
    )
  }

  return (
    <tr data-inactive={deactivated}>
      <td data-label={labels.name}>
        <div className={shared.cellStack}>
          <strong>
            {user.name} {isMe && <span className={shared.muted}>{labels.you}</span>}
          </strong>
          {deactivated && <Badge tone="stone">{labels.deactivatedBadge}</Badge>}
        </div>
      </td>
      <td data-label={labels.contact}>
        <div className={shared.cellStack}>
          <span>{user.email}</span>
          <span className={shared.muted}>{user.phone}</span>
          <Badge tone={user.is_email_verified ? 'green' : 'amber'}>
            {user.is_email_verified ? labels.verified : labels.unverified}
          </Badge>
        </div>
      </td>
      <td data-label={labels.role}>
        <Badge tone={user.role === 'ADMIN' ? 'blue' : 'stone'}>{labels.roles[user.role]}</Badge>
      </td>
      <td data-label={labels.joined}>{formatDate(user.created_at, lang)}</td>
      <td data-label={t.admin.actions}>
        {confirming ? (
          <div
            role="alertdialog"
            aria-labelledby={`user-${user.id}-confirm`}
            className={shared.cellStack}
          >
            <strong id={`user-${user.id}-confirm`}>
              {interpolate(labels.deactivateQuestion, { name: user.name })}
            </strong>
            <div className={shared.rowActions}>
              <Button
                variant="danger"
                className={shared.small}
                disabled={setActive.isPending}
                onClick={() => toggle(false)}
              >
                {labels.deactivate}
              </Button>
              <Button
                variant="outline"
                className={shared.small}
                onClick={() => setConfirming(false)}
              >
                {t.admin.cancel}
              </Button>
            </div>
          </div>
        ) : (
          <div className={shared.rowActions}>
            <Button
              variant="outline"
              className={shared.small}
              aria-label={`${t.admin.edit} ${user.name}`}
              onClick={onEdit}
            >
              {t.admin.edit}
            </Button>
            {deactivated ? (
              <Button
                variant="green"
                className={shared.small}
                disabled={setActive.isPending}
                aria-label={`${labels.restore} ${user.name}`}
                onClick={() => toggle(true)}
              >
                {labels.restore}
              </Button>
            ) : (
              !isMe && (
                <Button
                  variant="danger"
                  className={shared.small}
                  aria-label={`${labels.deactivate} ${user.name}`}
                  onClick={() => setConfirming(true)}
                >
                  {labels.deactivate}
                </Button>
              )
            )}
          </div>
        )}
      </td>
    </tr>
  )
}

function UserForm({ user, onDone }: { user: AdminUser | undefined; onDone: () => void }) {
  const { t } = useI18n()
  const labels = t.admin.users
  const toast = useToast()
  const save = useSaveUser()
  const [formError, setFormError] = useState<string>()

  const schema = useMemo(() => {
    const rules = authRules(t)
    return z.object({
      name: rules.name,
      email: rules.email,
      phone: rules.phone,
      role: z.enum(ROLES),
      email_verified: z.boolean(),
      // Required for a new account; blank on an existing one keeps the current password.
      password: user ? z.union([z.literal(''), rules.newPassword]) : rules.newPassword,
    })
  }, [t, user])

  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      name: user?.name ?? '',
      email: user?.email ?? '',
      phone: user?.phone ?? '',
      role: user?.role ?? 'CUSTOMER',
      email_verified: user?.is_email_verified ?? false,
      password: '',
    },
  })
  const serverError = useServerErrors(form, {
    email_or_phone_taken: 'email',
    cannot_demote_self: 'role',
  })
  const errors = form.formState.errors

  return (
    <form
      className={`${shared.card} ${styles.fields} ${shared.formCard}`}
      aria-labelledby="user-form-title"
      noValidate
      onSubmit={form.handleSubmit(async ({ password, ...values }) => {
        setFormError(undefined)
        try {
          const saved = await save.mutateAsync({
            id: user?.id,
            values: { ...values, password: password || undefined },
          })
          toast(user ? t.admin.saved : interpolate(labels.created, { name: saved.name }))
          onDone()
        } catch (error) {
          setFormError(serverError(error))
        }
      })}
    >
      <h2 id="user-form-title" className={shared.cardTitle}>
        {user ? interpolate(labels.editTitle, { name: user.name }) : labels.newTitle}
      </h2>
      <div className={styles.pair}>
        <TextField
          label={t.auth.fullName}
          autoComplete="off"
          error={errors.name?.message}
          {...form.register('name')}
        />
        <TextField
          label={t.auth.email}
          type="email"
          autoComplete="off"
          error={errors.email?.message}
          {...form.register('email')}
        />
      </div>
      <div className={styles.pair}>
        <TextField
          label={t.auth.phone}
          type="tel"
          autoComplete="off"
          error={errors.phone?.message}
          {...form.register('phone')}
        />
        <SelectField label={labels.role} error={errors.role?.message} {...form.register('role')}>
          {ROLES.map((role) => (
            <option key={role} value={role}>
              {labels.roles[role]}
            </option>
          ))}
        </SelectField>
      </div>
      <TextField
        label={user ? labels.newPassword : labels.password}
        type="password"
        autoComplete="new-password"
        error={errors.password?.message}
        {...form.register('password')}
      />
      <label className={shared.check}>
        <input type="checkbox" {...form.register('email_verified')} />
        {labels.emailVerified}
      </label>
      <FormError message={formError} />
      <div className={shared.rowActions}>
        <Button type="submit" disabled={form.formState.isSubmitting}>
          {t.admin.save}
        </Button>
        <Button variant="outline" onClick={onDone}>
          {t.admin.cancel}
        </Button>
      </div>
    </form>
  )
}
