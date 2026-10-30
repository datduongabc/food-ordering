import { useQuery } from '@tanstack/react-query'
import { EmptyView, ErrorView, Loading } from '@/components/ui/StatusView'
import { Pagination } from '@/features/catalog/components/Pagination'
import { useI18n } from '@/i18n/context'
import { formatDateTime, formatVnd, interpolate } from '@/lib/format'
import { isLocalizedText } from '@/lib/localized'
import { adminQueries } from '../api'
import { FilterChips } from '../components/FilterChips'
import { AUDIT_GROUPS, type AuditEntry } from '../schemas'
import { oneOf, useUrlFilters } from '../useUrlFilters'
import shared from '../admin.module.css'
import styles from './AuditPage.module.css'

export function AdminAuditPage() {
  const { t } = useI18n()
  const labels = t.admin.audit
  const { params, page, update } = useUrlFilters()
  const group = oneOf(AUDIT_GROUPS, params.get('group'))
  const log = useQuery(adminQueries.auditLog({ group, page }))

  let body
  if (log.error) {
    body = <ErrorView error={log.error} onRetry={() => log.refetch()} />
  } else if (!log.data) {
    body = <Loading />
  } else if (log.data.items.length === 0) {
    body = <EmptyView title={t.admin.noResults}>{labels.empty}</EmptyView>
  } else {
    body = (
      <>
        <div className={shared.tableWrap}>
          <table className={shared.table}>
            <thead>
              <tr>
                <th scope="col">{labels.when}</th>
                <th scope="col">{labels.actor}</th>
                <th scope="col">{labels.action}</th>
                <th scope="col">{labels.target}</th>
                <th scope="col">{labels.changes}</th>
              </tr>
            </thead>
            <tbody>
              {log.data.items.map((entry) => (
                <AuditRow key={entry.id} entry={entry} />
              ))}
            </tbody>
          </table>
        </div>
        {log.data.total_pages > 1 && (
          <div className={shared.pager}>
            <Pagination
              page={page}
              totalPages={log.data.total_pages}
              onChange={(next) => update({ page: String(next) })}
            />
          </div>
        )}
      </>
    )
  }

  return (
    <>
      <div className={shared.head}>
        <h1 className={shared.title}>{labels.title}</h1>
        {log.data && (
          <span className={shared.count}>
            {interpolate(t.admin.total, { count: log.data.total })}
          </span>
        )}
      </div>
      <div className={shared.filters}>
        <FilterChips
          label={labels.action}
          options={[
            { value: undefined, label: t.admin.all },
            ...AUDIT_GROUPS.map((value) => ({ value, label: labels.groups[value] })),
          ]}
          value={group}
          onChange={(value) => update({ group: value })}
        />
      </div>
      {body}
    </>
  )
}

function AuditRow({ entry }: { entry: AuditEntry }) {
  const { t, lang } = useI18n()
  const labels = t.admin.audit
  const changes = Object.entries(entry.changes)

  function show(field: string, value: unknown): string {
    if (value === null || value === undefined || value === '') return '—'
    if (isLocalizedText(value)) return value[lang]
    if (field === 'price' && typeof value === 'number') return formatVnd(value)
    if (field === 'status' && typeof value === 'string') {
      const reservation: Record<string, string> = t.reservationStatus
      return t.orderStatus[value] ?? reservation[value] ?? value
    }
    if (typeof value === 'boolean') return value ? '✓' : '✗'
    if (Array.isArray(value)) return value.join(', ')
    return String(value)
  }

  return (
    <tr>
      <td data-label={labels.when}>{formatDateTime(entry.created_at, lang)}</td>
      <td data-label={labels.actor}>
        {entry.actor_name}
        {entry.actor_id === null && <span className={shared.muted}> {labels.removedActor}</span>}
      </td>
      <td data-label={labels.action}>
        {labels.actions[entry.action.replace('.', '_')] ?? entry.action}
      </td>
      <td data-label={labels.target}>{entry.target_label || '—'}</td>
      <td data-label={labels.changes}>
        {changes.length === 0 ? (
          '—'
        ) : (
          <dl className={styles.changes}>
            {changes.map(([field, [before, after]]) => (
              <div key={field}>
                <dt>{labels.fields[field] ?? field}</dt>
                <dd>
                  {before !== null && (
                    <>
                      <del>{show(field, before)}</del>
                      {' → '}
                    </>
                  )}
                  {show(field, after)}
                </dd>
              </div>
            ))}
          </dl>
        )}
      </td>
    </tr>
  )
}
