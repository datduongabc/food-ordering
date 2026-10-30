import { useEffect } from 'react'
import { useRouteError } from 'react-router'
import { Button } from '@/components/ui/Button'
import { EmptyView } from '@/components/ui/StatusView'
import { useI18n } from '@/i18n/context'
import { reportError } from '@/lib/monitoring'

/** Shown instead of a blank screen when a page fails to render or load. */
export function ErrorPage() {
  const { t } = useI18n()
  const error = useRouteError()
  useEffect(() => reportError(error), [error])
  return (
    <div className="page">
      <EmptyView title={t.errorPage.title}>
        <p>{t.errorPage.body}</p>
        <Button variant="outline" onClick={() => window.location.reload()}>
          {t.errorPage.reload}
        </Button>
      </EmptyView>
    </div>
  )
}
