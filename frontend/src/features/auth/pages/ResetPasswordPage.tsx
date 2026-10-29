import { useMemo, useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm, useWatch } from 'react-hook-form'
import { Link, useSearchParams } from 'react-router'
import { z } from 'zod'
import { FormError } from '@/components/form/FormError'
import { TextField } from '@/components/form/TextField'
import { Button, ButtonLink } from '@/components/ui/Button'
import { useToast } from '@/components/ui/toastContext'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { interpolate } from '@/lib/format'
import { useForgotPassword, useResetPassword } from '../api'
import { AuthLayout } from '../components/AuthLayout'
import styles from '../components/AuthForm.module.css'
import { useServerErrors } from '../useFieldErrors'
import { authRules } from '../validation'

export function ResetPasswordPage() {
  const { t } = useI18n()
  const toast = useToast()
  const errorMessage = useErrorMessage()
  const [params] = useSearchParams()
  const reset = useResetPassword()
  const resend = useForgotPassword()
  const [formError, setFormError] = useState<string>()

  const schema = useMemo(() => {
    const rules = authRules(t)
    return z.object({ email: rules.email, code: rules.code, password: rules.newPassword })
  }, [t])
  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: { email: params.get('email') ?? '', code: '', password: '' },
  })
  const serverError = useServerErrors(form, {
    invalid_code: 'code',
    too_many_code_attempts: 'code',
  })
  const errors = form.formState.errors
  const email = useWatch({ control: form.control, name: 'email' })

  if (reset.isSuccess) {
    return (
      <AuthLayout>
        <div className={styles.done} role="status">
          <span aria-hidden="true" className={styles.doneIcon}>
            ✓
          </span>
          <h1 className={styles.title}>{t.auth.doneTitle}</h1>
          <p className={styles.body}>{t.auth.doneBody}</p>
          <ButtonLink to="/login" size="lg">
            {t.auth.loginNow}
          </ButtonLink>
        </div>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout>
      <form
        className={styles.form}
        noValidate
        onSubmit={form.handleSubmit(async (values) => {
          setFormError(undefined)
          try {
            await reset.mutateAsync({
              email: values.email,
              code: values.code,
              new_password: values.password,
            })
          } catch (error) {
            setFormError(serverError(error))
          }
        })}
      >
        <Link to="/login" className={styles.back}>
          ← {t.auth.backToLogin}
        </Link>
        <h1 className={styles.title}>{t.auth.resetTitle}</h1>
        {params.get('email') && (
          <p role="status" className={styles.notice}>
            {interpolate(t.auth.resetNotice, { email: params.get('email') ?? '' })}
          </p>
        )}
        <TextField
          label={t.auth.email}
          type="email"
          autoComplete="email"
          error={errors.email?.message}
          {...form.register('email')}
        />
        <TextField
          label={t.auth.code}
          variant="code"
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          placeholder="000000"
          error={errors.code?.message}
          {...form.register('code')}
        />
        <TextField
          label={t.auth.newPassword}
          type="password"
          autoComplete="new-password"
          placeholder={t.auth.passwordPlaceholder}
          error={errors.password?.message}
          {...form.register('password')}
        />
        <FormError message={formError} />
        <Button type="submit" size="lg" block disabled={form.formState.isSubmitting}>
          {t.auth.resetCta}
        </Button>
        <p className={styles.muted}>
          {t.auth.codeExpiry}{' '}
          <button
            type="button"
            className={styles.linkButton}
            disabled={resend.isPending || !email}
            onClick={() =>
              resend.mutate(email, {
                onSuccess: () => toast(t.auth.resent),
                onError: (error) => toast(errorMessage(error)),
              })
            }
          >
            {t.auth.resend}
          </button>
        </p>
      </form>
    </AuthLayout>
  )
}
