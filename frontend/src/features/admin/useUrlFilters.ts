import { useCallback } from 'react'
import { useSearchParams } from 'react-router'

/**
 * Admin filters live in the URL, like the menu's, so a filtered list survives a reload and
 * can be sent to a colleague. Changing any filter but the page goes back to page 1.
 */
export function useUrlFilters() {
  const [params, setParams] = useSearchParams()
  const page = Math.max(1, Number.parseInt(params.get('page') ?? '1', 10) || 1)

  const update = useCallback(
    (changes: Record<string, string | undefined>) =>
      setParams(
        (current) => {
          const next = new URLSearchParams(current)
          for (const [key, value] of Object.entries(changes)) {
            if (value === undefined || value === '') next.delete(key)
            else next.set(key, value)
          }
          if (!('page' in changes)) next.delete('page')
          return next
        },
        { replace: 'q' in changes },
      ),
    [setParams],
  )
  return { params, page, update }
}

/** `value` if it is one of `options`, else undefined: URLs are typed by hand. */
export function oneOf<T extends string>(
  options: readonly T[],
  value: string | null,
): T | undefined {
  return options.find((option) => option === value)
}
