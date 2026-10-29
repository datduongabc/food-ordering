import { useMemo, useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router'
import { z } from 'zod'
import { FormError } from '@/components/form/FormError'
import { TextField } from '@/components/form/TextField'
import { Button, ButtonLink } from '@/components/ui/Button'
import { Loading } from '@/components/ui/StatusView'
import { useToast } from '@/components/ui/toastContext'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { interpolate } from '@/lib/format'
import { useRequestVerification, useVerifyEmail } from '../api'
import { AuthLayout } from '../components/AuthLayout'
import styles from '../components/AuthForm.module.css'
import { useCurrentUser } from '../queries'
import { useServerErrors } from '../useFieldErrors'
import { authRules, safeNext } from '../validation'

export function VerifyEmailPage() {
  const { t } = useI18n()
  const user = useCurrentUser()
  const navigate = useNavigate()
  const toast = useToast()
  const errorMessage = useErrorMessage()
  const [params] = useSearchParams()
  const next = safeNext(params.get('next'))
  const verify = useVerifyEmail()
  const resend = useRequestVerification()
  const [formError, setFormError] = useState<string>()

  const schema = useMemo(() => z.object({ code: authRules(t).code }), [t])
  const form = useForm({ resolver: zodResolver(schema), defaultValues: { code: '' } })
  const serverError = useServerErrors(form, {
    invalid_code: 'code',
    too_many_code_attempts: 'code',
  })

  if (user === undefined) return <Loading />
  if (user === null) return <Navigate to="/login?next=/verify-email" replace />

  if (user.is_email_verified && verify.isIdle) {
    return (
      <AuthLayout>
        <div className={styles.done}>
          <span aria-hidden="true" className={styles.doneIcon}>
            ✓
          </span>
          <h1 className={styles.title}>{t.auth.alreadyVerified}</h1>
          <ButtonLink to={next} size="lg">
            {t.common.backHome}
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
        onSubmit={form.handleSubmit(async ({ code }) => {
          setFormError(undefined)
          try {
            await verify.mutateAsync(code)
            toast(t.auth.verified)
            navigate(next, { replace: true })
          } catch (error) {
            setFormError(serverError(error))
          }
        })}
      >
        <h1 className={styles.title}>{t.auth.verifyTitle}</h1>
        <p className={styles.body}>{interpolate(t.auth.verifyBody, { email: user.email })}</p>
        <TextField
          label={t.auth.code}
          variant="code"
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          placeholder="000000"
          error={form.formState.errors.code?.message}
          {...form.register('code')}
        />
        <FormError message={formError} />
        <Button type="submit" size="lg" block disabled={form.formState.isSubmitting}>
          {t.auth.verifyCta}
        </Button>
        <p className={styles.muted}>
          {t.auth.codeExpiry}{' '}
          <button
            type="button"
            className={styles.linkButton}
            disabled={resend.isPending}
            onClick={() =>
              resend.mutate(undefined, {
                onSuccess: () => toast(t.auth.resent),
                onError: (error) => toast(errorMessage(error)),
              })
            }
          >
            {t.auth.resend}
          </button>
        </p>
        <Link to={next} className={styles.link}>
          {t.auth.later}
        </Link>
      </form>
    </AuthLayout>
  )
}
