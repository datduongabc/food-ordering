import { z } from 'zod'
import type { Dictionary } from '@/i18n/dictionary'

/** Zod rules matching the API's, with messages in the current language. */
export function authRules(t: Dictionary) {
  const v = t.validation
  return {
    name: z.string().trim().min(1, v.required).max(255),
    email: z.string().trim().toLowerCase().min(1, v.required).pipe(z.email(v.emailInvalid)),
    // Customers type spaces and dots ("0901 234 567"); the API wants the bare digits.
    phone: z
      .string()
      .transform((value) => value.replace(/[\s.-]/g, ''))
      .pipe(z.string().regex(/^\d{10}$/, v.phoneInvalid)),
    newPassword: z.string().min(8, v.passwordShort).max(128),
    currentPassword: z.string().min(1, v.required).max(128),
    code: z
      .string()
      .trim()
      .regex(/^\d{6}$/, v.codeInvalid),
  }
}

/** Only same-site paths are followed after sign-in, never another origin. */
export function safeNext(next: string | null, fallback = '/'): string {
  if (!next || !next.startsWith('/') || next.startsWith('//') || next.startsWith('/\\')) {
    return fallback
  }
  return next
}
