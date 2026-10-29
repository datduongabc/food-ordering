import { useMemo, useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router'
import { z } from 'zod'
import { FormError } from '@/components/form/FormError'
import { TextField } from '@/components/form/TextField'
import { Button } from '@/components/ui/Button'
import { useI18n } from '@/i18n/context'
import { useLogin } from '../api'
import { AuthLayout } from '../components/AuthLayout'
import { AuthTabs } from '../components/AuthTabs'
import styles from '../components/AuthForm.module.css'
import { useCurrentUser } from '../queries'
import { useServerErrors } from '../useFieldErrors'
import { authRules, safeNext } from '../validation'

export function LoginPage() {
  const { t } = useI18n()
  const user = useCurrentUser()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const next = safeNext(params.get('next'))
  const login = useLogin()
  const [formError, setFormError] = useState<string>()

  const schema = useMemo(() => {
    const rules = authRules(t)
    return z.object({
      email: rules.email,
      password: rules.currentPassword,
      remember: z.boolean(),
    })
  }, [t])
  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: { email: '', password: '', remember: false },
  })
  const serverError = useServerErrors(form, {})
  const errors = form.formState.errors

  // Someone already signed in has nothing to do here.
  if (user && login.isIdle) return <Navigate to={next} replace />

  return (
    <AuthLayout>
      <AuthTabs />
      <form
        className={styles.form}
        noValidate
        onSubmit={form.handleSubmit(async (values) => {
          setFormError(undefined)
          try {
            await login.mutateAsync(values)
            navigate(next, { replace: true })
          } catch (error) {
            setFormError(serverError(error))
          }
        })}
      >
        <h1 className={styles.title}>{t.auth.loginTitle}</h1>
        <TextField
          label={t.auth.email}
          type="email"
          autoComplete="email"
          placeholder="ban@vidu.vn"
          error={errors.email?.message}
          {...form.register('email')}
        />
        <TextField
          label={t.auth.password}
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          labelAction={
            <Link to="/forgot-password" className={styles.link}>
              {t.auth.forgot}
            </Link>
          }
          {...form.register('password')}
        />
        <label className={styles.checkbox}>
          <input type="checkbox" {...form.register('remember')} />
          {t.auth.remember}
        </label>
        <FormError message={formError} />
        <Button type="submit" size="lg" block disabled={form.formState.isSubmitting}>
          {t.auth.loginCta}
        </Button>
      </form>
    </AuthLayout>
  )
}
