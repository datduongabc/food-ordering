import { useCallback } from 'react'
import { useToast } from '@/components/ui/toastContext'
import { useI18n } from '@/i18n/context'
import { useErrorMessage } from '@/i18n/errors'
import { interpolate } from '@/lib/format'
import type { Product } from '@/features/catalog/schemas'
import { useCartActions } from './useCart'

/** Adds a dish and tells the customer what happened, success or not. */
export function useAddToCart(): (product: Product, quantity?: number) => Promise<void> {
  const { t } = useI18n()
  const toast = useToast()
  const errorMessage = useErrorMessage()
  const { add } = useCartActions()

  return useCallback(
    async (product: Product, quantity = 1) => {
      try {
        await add(product.id, quantity)
        toast(interpolate(t.common.addedToCart, { name: product.name }))
      } catch (error) {
        toast(errorMessage(error))
      }
    },
    [add, errorMessage, t, toast],
  )
}
