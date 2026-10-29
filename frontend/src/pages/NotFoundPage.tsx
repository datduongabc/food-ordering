import { ButtonLink } from '@/components/ui/Button'
import { EmptyView } from '@/components/ui/StatusView'
import { useI18n } from '@/i18n/context'

export function NotFoundPage() {
  const { t } = useI18n()
  return (
    <div className="page">
      <EmptyView title={t.notFound.title}>
        <p>{t.notFound.body}</p>
        <ButtonLink to="/" variant="outline">
          {t.common.backHome}
        </ButtonLink>
      </EmptyView>
    </div>
  )
}
