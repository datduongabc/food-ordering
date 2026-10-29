import { useMemo, useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Navigate, useNavigate, useSearchParams } from 'react-router'
import { z } from 'zod'
import { FormError } from '@/components/form/FormError'
import { TextField } from '@/components/form/TextField'
import { Button } from '@/components/ui/Button'
import { useI18n } from '@/i18n/context'
import { useRegister } from '../api'
import { AuthLayout } from '../components/AuthLayout'
import { AuthTabs } from '../components/AuthTabs'
import styles from '../components/AuthForm.module.css'
import { useCurrentUser } from '../queries'
import { useServerErrors } from '../useFieldErrors'
import { authRules, safeNext } from '../validation'

export function RegisterPage() {
  const { t } = useI18n()
  const user = useCurrentUser()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const next = safeNext(params.get('next'))
  const register = useRegister()
  const [formError, setFormError] = useState<string>()

  const schema = useMemo(() => {
    const rules = authRules(t)
    return z.object({
      name: rules.name,
      email: rules.email,
      phone: rules.phone,
      password: rules.newPassword,
    })
  }, [t])
  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: { name: '', email: '', phone: '', password: '' },
  })
  const serverError = useServerErrors(form, { email_taken: 'email', phone_taken: 'phone' })
  const errors = form.formState.errors

  if (user && register.isIdle) return <Navigate to={next} replace />

  return (
    <AuthLayout>
      <AuthTabs />
      <form
        className={styles.form}
        noValidate
        onSubmit={form.handleSubmit(async (values) => {
          setFormError(undefined)
          try {
            await register.mutateAsync(values)
            navigate(`/verify-email?next=${encodeURIComponent(next)}`, { replace: true })
          } catch (error) {
            setFormError(serverError(error))
          }
        })}
      >
        <h1 className={styles.title}>{t.auth.registerTitle}</h1>
        <TextField
          label={t.auth.fullName}
          autoComplete="name"
          placeholder="Nguyễn Văn A"
          error={errors.name?.message}
          {...form.register('name')}
        />
        <TextField
          label={t.auth.email}
          type="email"
          autoComplete="email"
          placeholder="ban@vidu.vn"
          error={errors.email?.message}
          {...form.register('email')}
        />
        <TextField
          label={t.auth.phone}
          type="tel"
          autoComplete="tel"
          inputMode="numeric"
          placeholder="0901 234 567"
          error={errors.phone?.message}
          {...form.register('phone')}
        />
        <TextField
          label={t.auth.password}
          type="password"
          autoComplete="new-password"
          placeholder={t.auth.passwordPlaceholder}
          error={errors.password?.message}
          {...form.register('password')}
        />
        <FormError message={formError} />
        <Button type="submit" size="lg" block disabled={form.formState.isSubmitting}>
          {t.auth.registerCta}
        </Button>
      </form>
    </AuthLayout>
  )
}
