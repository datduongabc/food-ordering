// Sign-in attempts at a fixed rate, each with a new unknown email (the server still hashes).
import http from 'k6/http'
export const options = {
  scenarios: { logins: { executor: 'constant-arrival-rate', rate: Number(__ENV.RATE), timeUnit: '1s', duration: '20s', preAllocatedVUs: 100, maxVUs: 400 } },
  thresholds: { 'http_req_duration{name:login}': [] },
  summaryTrendStats: ['med', 'p(95)', 'max'],
}
export default function () {
  const jar = http.cookieJar()
  if (!jar.cookiesForURL('http://web/').dateno_csrf) http.get('http://web/api/health')
  const token = jar.cookiesForURL('http://web/').dateno_csrf[0]
  http.post('http://web/api/auth/login', JSON.stringify({ email: `x${__VU}-${__ITER}@example.com`, password: 'wrong-password' }), {
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': token },
    tags: { name: 'login' },
  })
}
export function handleSummary(data) {
  const d = data.metrics['http_req_duration{name:login}'] || data.metrics.http_req_duration
  const m = data.metrics
  return { stdout: `logins/s=${(m.iterations.values.rate).toFixed(1)} dropped=${m.dropped_iterations ? m.dropped_iterations.values.count : 0} med=${d.values.med.toFixed(0)}ms p95=${d.values['p(95)'].toFixed(0)}ms max=${d.values.max.toFixed(0)}ms\n` }
}
