import { useCallback } from 'react'
import { useI18n } from '@/i18n/context'
import type { Category } from './schemas'

/** Category names are stored in English; known slugs get a translated label. */
export function useCategoryLabel(): (category: Category) => string {
  const { t } = useI18n()
  return useCallback((category: Category) => t.categories[category.slug] ?? category.name, [t])
}
