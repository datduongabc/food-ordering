import http from 'k6/http'
import { sleep } from 'k6'
import { Counter } from 'k6/metrics'

const API_BASE = __ENV.API_BASE || 'http://backend:8000'
const WEB_BASE = __ENV.WEB_BASE || 'http://web'
const VUS = Number(__ENV.VUS || 100)
const DURATION = __ENV.DURATION || '20s'
const TIER = Number(__ENV.TIER || 1)

const SLUGS = [
  'caesar-salad',
  'french-onion-soup',
  'nha-trang-grilled-pork',
  'shrimp-pork-spring-rolls',
  'silken-tofu-salted-egg',
]
const QUERIES = ['bo', 'ga', 'ca', 'sup', ' goi']

const http2xx = new Counter('http_2xx')
const http429 = new Counter('http_429')
const http5xx = new Counter('http_5xx')

export const options = {
  vus: VUS,
  duration: DURATION,
  summaryTrendStats: ['avg', 'med', 'p(95)', 'p(99)', 'max'],
}

export default function () {
  // Simulate 1,000 - 2,000 distinct client IPs across the 10,000-user base
  const userIdx = ((__VU - 1) * 10 + (__ITER % 10)) % 2000
  const ip = `10.${TIER}.${Math.floor(userIdx / 250) + 1}.${(userIdx % 250) + 1}`
  const headers = { 'X-Forwarded-For': ip }

  const slug = SLUGS[(__VU + __ITER) % SLUGS.length]
  const q = QUERIES[(__VU + __ITER) % QUERIES.length].trim()

  const responses = http.batch([
    ['GET', `${WEB_BASE}/`, null, { headers }],
    ['GET', `${API_BASE}/api/categories`, null, { headers }],
    ['GET', `${API_BASE}/api/products?page=${1 + (__ITER % 3)}`, null, { headers }],
    ['GET', `${API_BASE}/api/products/${slug}`, null, { headers }],
    ['GET', `${API_BASE}/api/products/search?q=${q}`, null, { headers }],
  ])

  for (const r of responses) {
    if (r.status >= 200 && r.status < 300) http2xx.add(1)
    else if (r.status === 429) http429.add(1)
    else if (r.status >= 500 || r.status === 0) http5xx.add(1)
  }

  sleep(0.2)
}

export function handleSummary(data) {
  const m = data.metrics
  const count = (name) => (m[name] ? m[name].values.count : 0)
  const d = m.http_req_duration.values
  return {
    stdout: `reqs=${m.http_reqs.values.count} rps=${m.http_reqs.values.rate.toFixed(1)} avg=${d.avg.toFixed(1)}ms med=${d.med.toFixed(1)}ms p95=${d['p(95)'].toFixed(1)}ms p99=${d['p(99)'].toFixed(1)}ms max=${d.max.toFixed(1)}ms ok_2xx=${count('http_2xx')} rate_limited_429=${count('http_429')} err_5xx=${count('http_5xx')}\n`,
  }
}
