// One attacker address sending a fixed rate, just under nginx's per-address limit.
import http from 'k6/http'
export const options = {
  scenarios: { steady: { executor: 'constant-arrival-rate', rate: Number(__ENV.RATE || 18), timeUnit: '1s', duration: '25s', preAllocatedVUs: 50, maxVUs: 200 } },
}
export default function () {
  http.get(`http://web${__ENV.TARGET}`)
}
export function handleSummary(data) {
  const m = data.metrics
  return { stdout: `sent=${m.http_reqs.values.count} fail=${(m.http_req_failed.values.rate * 100).toFixed(1)}% p95=${m.http_req_duration.values['p(95)'].toFixed(0)}ms\n` }
}
