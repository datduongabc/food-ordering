import { readFileSync } from 'node:fs'

/**
 * The backend runs with the console email sender, which writes each email to its log.
 * Emails go out in a background task after the response, so this polls for the
 * `count`-th code sent to `email`.
 */
export async function emailedCode(email: string, count = 1, timeoutMs = 5000): Promise<string> {
  const logPath = process.env.DATENO_E2E_BACKEND_LOG
  if (!logPath) throw new Error('DATENO_E2E_BACKEND_LOG is not set; is global-setup running?')
  const escaped = email.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const pattern = new RegExp(`Email to ${escaped} \\|[^\\n]*\\n[\\s\\S]*?\\b(\\d{6})\\b`, 'g')
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    const codes = [...readFileSync(logPath, 'utf8').matchAll(pattern)].map((match) => match[1])
    if (codes.length >= count) return codes[count - 1]!
    await new Promise((done) => setTimeout(done, 100))
  }
  throw new Error(`No code #${count} for ${email} in the backend log`)
}

export function uniqueEmail(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`
}

export function uniquePhone(): string {
  return `09${String(Math.floor(Math.random() * 1e8)).padStart(8, '0')}`
}
