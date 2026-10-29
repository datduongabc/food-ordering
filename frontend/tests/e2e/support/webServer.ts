import { createReadStream, existsSync, statSync } from 'node:fs'
import { createServer, request, type Server } from 'node:http'
import { extname, join, normalize } from 'node:path'

const TYPES: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.webp': 'image/webp',
  '.json': 'application/json',
}

/**
 * Serves the production build the way it will be deployed: static files, an SPA fallback to
 * index.html, and /api + /media proxied to the backend so cookies stay first-party.
 */
export function startWebServer(distDir: string, apiOrigin: string, port: number): Promise<Server> {
  const api = new URL(apiOrigin)
  const server = createServer((req, res) => {
    const url = req.url ?? '/'
    if (url.startsWith('/api/') || url.startsWith('/media/')) {
      const upstream = request(
        {
          hostname: api.hostname,
          port: api.port,
          path: url,
          method: req.method,
          headers: req.headers,
        },
        (response) => {
          res.writeHead(response.statusCode ?? 502, response.headers)
          response.pipe(res)
        },
      )
      upstream.on('error', () => res.writeHead(502).end())
      req.pipe(upstream)
      return
    }

    const pathname = decodeURIComponent(new URL(url, 'http://local').pathname)
    let file = normalize(join(distDir, pathname))
    if (!file.startsWith(distDir) || !existsSync(file) || statSync(file).isDirectory()) {
      file = join(distDir, 'index.html')
    }
    res.writeHead(200, { 'Content-Type': TYPES[extname(file)] ?? 'application/octet-stream' })
    createReadStream(file).pipe(res)
  })
  return new Promise((resolve) => server.listen(port, '127.0.0.1', () => resolve(server)))
}
