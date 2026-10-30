import { spawn, spawnSync } from 'node:child_process'
import { cpSync, mkdtempSync, openSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { API_PORT, WEB_PORT } from './ports.ts'
import { startWebServer } from './support/webServer.ts'

const FRONTEND_DIR = resolve(import.meta.dirname, '../..')
const BACKEND_DIR = resolve(FRONTEND_DIR, '../backend')

function run(args: string[], env: NodeJS.ProcessEnv) {
  const result = spawnSync('uv', ['run', ...args], {
    cwd: BACKEND_DIR,
    env,
    encoding: 'utf8',
  })
  if (result.status !== 0) {
    throw new Error(`uv run ${args.join(' ')} failed:\n${result.stdout}\n${result.stderr}`)
  }
}

const RESET_SCHEMA = `
import os
from sqlalchemy import create_engine, text
with create_engine(os.environ["DATABASE_URL"]).begin() as conn:
    conn.execute(text("DROP SCHEMA public CASCADE"))
    conn.execute(text("CREATE SCHEMA public"))
`

async function waitForHealth(url: string, timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    try {
      if ((await fetch(url)).ok) return
    } catch {
      // Not listening yet.
    }
    await new Promise((done) => setTimeout(done, 250))
  }
  throw new Error(`Backend did not become healthy at ${url}`)
}

/**
 * Builds a throwaway database with the real migrations (including the menu and local admin
 * seeds), starts uvicorn and serves a production build in front of it. Its log is kept
 * because the console email sender writes one-time codes there, which the auth journeys read.
 */
export default async function globalSetup() {
  const workDir = mkdtempSync(join(tmpdir(), 'dateno-e2e-'))
  const mediaDir = join(workDir, 'media')
  cpSync(join(BACKEND_DIR, 'media'), mediaDir, { recursive: true })

  const env: NodeJS.ProcessEnv = {
    ...process.env,
    APP_ENV: 'local',
    // Journeys sign up many accounts from one address; the API tests cover the limits.
    RATE_LIMITS_ENABLED: 'false',
    SECRET_KEY: 'e2e-secret-key-not-for-production-0123456789',
    DATABASE_URL: process.env.E2E_DATABASE_URL ?? `sqlite:///${join(workDir, 'e2e.db')}`,
    MEDIA_DIR: mediaDir,
  }
  // A reused Postgres database still holds the last run's orders, which a migration
  // downgrade rightly refuses to delete; start from an empty schema instead.
  if (process.env.E2E_DATABASE_URL) run(['python', '-c', RESET_SCHEMA], env)
  run(['alembic', 'upgrade', 'head'], env)
  const logPath = join(workDir, 'backend.log')
  const log = openSync(logPath, 'a')
  const server = spawn('uv', ['run', 'uvicorn', 'app.main:app', '--port', String(API_PORT)], {
    cwd: BACKEND_DIR,
    env,
    stdio: ['ignore', log, log],
  })
  process.env.DATENO_E2E_BACKEND_LOG = logPath
  await waitForHealth(`http://127.0.0.1:${API_PORT}/api/health`)

  // E2E exercises the production bundle rather than the dev server.
  const distDir = join(workDir, 'dist')
  const build = spawnSync('npx', ['vite', 'build', '--outDir', distDir, '--emptyOutDir'], {
    cwd: FRONTEND_DIR,
    encoding: 'utf8',
  })
  if (build.status !== 0) throw new Error(`vite build failed:\n${build.stdout}\n${build.stderr}`)
  const web = await startWebServer(distDir, `http://127.0.0.1:${API_PORT}`, WEB_PORT)

  return async () => {
    await new Promise((done) => web.close(done))
    server.kill('SIGTERM')
    await new Promise((done) => server.once('exit', done))
    rmSync(workDir, { recursive: true, force: true })
  }
}
