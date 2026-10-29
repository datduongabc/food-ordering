import type { ReactNode } from 'react'
import { QueryClientProvider, type QueryClient } from '@tanstack/react-query'
import { ToastProvider } from '@/components/ui/ToastProvider'
import type { Lang } from '@/i18n/dictionary'
import { I18nProvider } from '@/i18n/I18nProvider'

interface Props {
  queryClient: QueryClient
  lang?: Lang
  children: ReactNode
}

/** Everything a page needs around it; shared by the app and the integration tests. */
export function Providers({ queryClient, lang, children }: Props) {
  return (
    <QueryClientProvider client={queryClient}>
      <I18nProvider lang={lang}>
        <ToastProvider>{children}</ToastProvider>
      </I18nProvider>
    </QueryClientProvider>
  )
}
