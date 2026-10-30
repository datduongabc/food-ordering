import http from 'k6/http'
import { Counter } from 'k6/metrics'
const BASE = __ENV.BASE || 'http://web'
const conn = new Counter('conn_errors')
const client = new Counter('http_4xx')
const server = new Counter('http_5xx')
let sampled = false
export const options = {
  vus: Number(__ENV.VUS || 50),
  duration: __ENV.DURATION || '20s',
  summaryTrendStats: ['med', 'p(95)', 'p(99)', 'max'],
}
export default function () {
  const r = http.get(`${BASE}${__ENV.TARGET}`)
  if (r.status === 0) conn.add(1)
  else if (r.status >= 500) server.add(1)
  else if (r.status >= 400) client.add(1)
  if (r.status !== 200 && !sampled) {
    sampled = true
    console.log(`sample ${r.status} ${r.error_code} ${r.error}`)
  }
}
export function handleSummary(data) {
  const m = data.metrics
  const count = (name) => (m[name] ? m[name].values.count : 0)
  const why = { conn: count('conn_errors'), '4xx': count('http_4xx'), '5xx': count('http_5xx') }
  const d = m.http_req_duration.values
  return {
    stdout: `rps=${m.http_reqs.values.rate.toFixed(0)} fail=${(m.http_req_failed.values.rate * 100).toFixed(1)}% med=${d.med.toFixed(1)}ms p95=${d['p(95)'].toFixed(1)}ms p99=${d['p(99)'].toFixed(1)}ms ${JSON.stringify(why)}\n`,
  }
}
