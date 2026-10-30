import { useQueryClient } from '@tanstack/react-query'
import { TextField } from '@/components/form/TextField'
import { buttonClasses } from '@/components/ui/buttonClasses'
import { ORDER_STATUSES } from '@/features/orders/schemas'
import { useI18n } from '@/i18n/context'
import { exportUrl } from '../api'
import { FilterChips } from '../components/FilterChips'
import { oneOf, useUrlFilters } from '../useUrlFilters'
import shared from '../admin.module.css'
import styles from './ReportsPage.module.css'

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/
const MAX_DAYS = 366
const DAY_MS = 86_400_000

/** Today at the restaurant as YYYY-MM-DD, whatever the browser's own time zone. */
function restaurantToday(now = new Date()): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Ho_Chi_Minh' }).format(now)
}

function daysBefore(iso: string, days: number): string {
  return new Date(Date.parse(`${iso}T00:00:00Z`) - days * DAY_MS).toISOString().slice(0, 10)
}

function validRange(from: string, to: string): boolean {
  const span = (Date.parse(`${to}T00:00:00Z`) - Date.parse(`${from}T00:00:00Z`)) / DAY_MS
  return span >= 0 && span < MAX_DAYS
}

export function AdminReportsPage() {
  const { t, lang } = useI18n()
  const labels = t.admin.reports
  const queryClient = useQueryClient()
  const { params, update } = useUrlFilters()
  const today = restaurantToday()
  const to = ISO_DATE.test(params.get('to') ?? '') ? params.get('to')! : today
  const from = ISO_DATE.test(params.get('from') ?? '') ? params.get('from')! : daysBefore(to, 29)
  const status = oneOf(ORDER_STATUSES, params.get('status'))
  const ok = validRange(from, to)

  // The download is recorded in the activity log; show it there on the next visit.
  const logged = () => queryClient.invalidateQueries({ queryKey: ['admin', 'audit'] })

  function download(report: 'orders' | 'revenue', extra: Record<string, string | undefined>) {
    const href = exportUrl(report, { from, to, lang, ...extra })
    return ok ? (
      <a href={href} download className={buttonClasses('primary', 'md')} onClick={logged}>
        {labels.download}
      </a>
    ) : (
      <span aria-disabled="true" className={buttonClasses('primary', 'md', false, styles.off)}>
        {labels.download}
      </span>
    )
  }

  return (
    <>
      <div className={shared.head}>
        <h1 className={shared.title}>{labels.title}</h1>
      </div>
      <p className={`${shared.muted} ${styles.intro}`}>{labels.intro}</p>
      <div className={shared.filters}>
        <TextField
          label={labels.from}
          type="date"
          value={from}
          max={today}
          onChange={(event) => update({ from: event.target.value })}
        />
        <TextField
          label={labels.to}
          type="date"
          value={to}
          max={today}
          onChange={(event) => update({ to: event.target.value })}
        />
      </div>
      {!ok && (
        <p role="alert" className={styles.error}>
          {labels.badRange}
        </p>
      )}
      <div className={styles.grid}>
        <section className={shared.card}>
          <h2 className={shared.cardTitle}>{labels.ordersTitle}</h2>
          <p className={shared.muted}>{labels.ordersBody}</p>
          <FilterChips
            label={t.admin.status}
            options={[
              { value: undefined, label: t.admin.all },
              ...ORDER_STATUSES.map((value) => ({ value, label: t.orderStatus[value] ?? value })),
            ]}
            value={status}
            onChange={(value) => update({ status: value })}
          />
          {download('orders', { status })}
        </section>
        <section className={shared.card}>
          <h2 className={shared.cardTitle}>{labels.revenueTitle}</h2>
          <p className={shared.muted}>{labels.revenueBody}</p>
          {download('revenue', {})}
        </section>
      </div>
    </>
  )
}
