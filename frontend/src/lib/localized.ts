import { z } from 'zod'

/** Catalog text from the API in both UI languages. */
export const localizedTextSchema = z.object({ vi: z.string(), en: z.string() })

export type LocalizedText = z.infer<typeof localizedTextSchema>

export function isLocalizedText(value: unknown): value is LocalizedText {
  return localizedTextSchema.safeParse(value).success
}
