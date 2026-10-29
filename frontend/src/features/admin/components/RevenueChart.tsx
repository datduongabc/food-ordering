import { useState } from 'react'
import { useI18n } from '@/i18n/context'
import type { Lang } from '@/i18n/dictionary'
import { formatDayParts, formatVnd, interpolate } from '@/lib/format'
import type { RevenueTrend } from '../schemas'
import { niceTicks } from './ticks'
import styles from './RevenueChart.module.css'

const COMPACT: Record<Lang, Intl.NumberFormat> = {
  vi: new Intl.NumberFormat('vi-VN', { notation: 'compact', maximumFractionDigits: 1 }),
  en: new Intl.NumberFormat('en-GB', { notation: 'compact', maximumFractionDigits: 1 }),
}

/** Daily revenue from completed orders as columns; the table beside it carries every value. */
export function RevenueChart({ trend }: { trend: RevenueTrend }) {
  const { t, lang } = useI18n()
  const [hovered, setHovered] = useState<number>()
  const labels = t.admin.dashboard
  const ticks = niceTicks(Math.max(...trend.days.map((day) => day.revenue)))
  const top = ticks[ticks.length - 1] || 1
  const count = trend.days.length
  // Seven days fit a label each; longer ranges label about six evenly spaced days.
  const labelEvery = count <= 7 ? 1 : Math.ceil(count / 6)
  const active = hovered === undefined ? undefined : trend.days[hovered]

  return (
    <figure className={styles.figure}>
      <div className={styles.plot} aria-hidden="true" onMouseLeave={() => setHovered(undefined)}>
        {ticks.map((tick) => (
          <div key={tick} className={styles.grid} style={{ bottom: `${(tick / top) * 100}%` }}>
            <span className={styles.tick}>{COMPACT[lang].format(tick)}</span>
          </div>
        ))}
        <div className={styles.bars}>
          {trend.days.map((day, index) => (
            <div
              key={day.date}
              className={styles.slot}
              data-active={index === hovered}
              onMouseEnter={() => setHovered(index)}
            >
              <span
                className={styles.bar}
                style={{ height: `${(day.revenue / top) * 100}%` }}
                data-empty={day.revenue === 0}
              />
            </div>
          ))}
        </div>
        {active && hovered !== undefined && (
          <div
            className={styles.tooltip}
            // Bars start after the 52px axis gutter.
            style={{ left: `calc(52px + (100% - 52px) * ${(hovered + 0.5) / count})` }}
            data-edge={hovered < count / 4 ? 'start' : hovered >= (count * 3) / 4 ? 'end' : 'mid'}
          >
            <strong>{formatDayParts(active.date, lang).full}</strong>
            <span>{formatVnd(active.revenue)}</span>
            <span className={styles.tooltipMuted}>
              {interpolate(labels.dayTooltip, { orders: active.orders })}
            </span>
          </div>
        )}
      </div>
      <div className={styles.axis} aria-hidden="true">
        {trend.days.map((day, index) => {
          const parts = formatDayParts(day.date, lang)
          return (
            <span key={day.date} className={styles.axisLabel}>
              {index % labelEvery === 0 || index === count - 1
                ? count <= 7
                  ? parts.weekday
                  : `${parts.day} ${parts.month}`
                : ''}
            </span>
          )
        })}
      </div>
      <table className="visually-hidden">
        <caption>{labels.trendTable}</caption>
        <thead>
          <tr>
            <th scope="col">{labels.day}</th>
            <th scope="col">{labels.orders}</th>
            <th scope="col">{labels.revenueCol}</th>
          </tr>
        </thead>
        <tbody>
          {trend.days.map((day) => (
            <tr key={day.date}>
              <th scope="row">{formatDayParts(day.date, lang).full}</th>
              <td>{day.orders}</td>
              <td>{formatVnd(day.revenue)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  )
}
