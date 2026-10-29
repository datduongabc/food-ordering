import type { FieldValues, Path, UseFormReturn } from 'react-hook-form'
import { ApiError } from '@/lib/api/client'
import { useErrorMessage } from '@/i18n/errors'

/**
 * Shows server errors that are about one field (e.g. "email already registered") under
 * that field; returns the message for anything else, to show above the submit button.
 */
export function useServerErrors<T extends FieldValues>(
  form: UseFormReturn<T>,
  fieldsByCode: Partial<Record<string, Path<T>>>,
) {
  const message = useErrorMessage()
  return (error: unknown): string | undefined => {
    const field = error instanceof ApiError && error.code ? fieldsByCode[error.code] : undefined
    if (field) {
      form.setError(field, { message: message(error) }, { shouldFocus: true })
      return undefined
    }
    return message(error)
  }
}
