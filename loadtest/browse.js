// Many visitors browsing the menu at once, ramping up to 300: the site's main read traffic.
import http from 'k6/http'
import { check } from 'k6'

const BASE = __ENV.BASE || 'http://web'
const SLUGS = ['caesar-salad', 'french-onion-soup', 'nha-trang-grilled-pork', 'shrimp-pork-spring-rolls', 'silken-tofu-salted-egg']

export const options = {
  stages: JSON.parse(__ENV.STAGES || '[{"duration":"20s","target":20},{"duration":"30s","target":100},{"duration":"30s","target":300},{"duration":"10s","target":0}]'),
  summaryTrendStats: ['avg', 'med', 'p(95)', 'p(99)', 'max'],
}

export default function () {
  const pick = SLUGS[Math.floor(Math.random() * SLUGS.length)]
  const responses = http.batch([
    ['GET', `${BASE}/api/products?page=1`],
    ['GET', `${BASE}/api/categories`],
    ['GET', `${BASE}/api/products/${pick}`],
    ['GET', `${BASE}/api/products/search?q=bo`],
    ['GET', `${BASE}/`],
  ])
  for (const r of responses) check(r, { 'status 2xx/404': (x) => x.status < 300 || x.status === 404 })
}
