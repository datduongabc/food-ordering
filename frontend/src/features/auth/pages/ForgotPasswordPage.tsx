import { useMemo, useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router'
import { z } from 'zod'
import { FormError } from '@/components/form/FormError'
import { TextField } from '@/components/form/TextField'
import { Button } from '@/components/ui/Button'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { useForgotPassword } from '../api'
import { AuthLayout } from '../components/AuthLayout'
import styles from '../components/AuthForm.module.css'
import { authRules } from '../validation'

export function ForgotPasswordPage() {
  const { t } = useI18n()
  const navigate = useNavigate()
  const errorMessage = useErrorMessage()
  const forgot = useForgotPassword()
  const [formError, setFormError] = useState<string>()

  const schema = useMemo(() => z.object({ email: authRules(t).email }), [t])
  const form = useForm({ resolver: zodResolver(schema), defaultValues: { email: '' } })

  return (
    <AuthLayout>
      <form
        className={styles.form}
        noValidate
        onSubmit={form.handleSubmit(async ({ email }) => {
          setFormError(undefined)
          try {
            await forgot.mutateAsync(email)
            navigate(`/reset-password?email=${encodeURIComponent(email)}`)
          } catch (error) {
            setFormError(errorMessage(error))
          }
        })}
      >
        <Link to="/login" className={styles.back}>
          ← {t.auth.backToLogin}
        </Link>
        <h1 className={styles.title}>{t.auth.forgotTitle}</h1>
        <p className={styles.body}>{t.auth.forgotBody}</p>
        <TextField
          label={t.auth.email}
          type="email"
          autoComplete="email"
          placeholder="ban@vidu.vn"
          error={form.formState.errors.email?.message}
          {...form.register('email')}
        />
        <FormError message={formError} />
        <Button type="submit" size="lg" block disabled={form.formState.isSubmitting}>
          {t.auth.sendCode}
        </Button>
      </form>
    </AuthLayout>
  )
}
