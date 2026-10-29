import { z } from 'zod'

const CSRF_COOKIE = 'dateno_csrf'
const CSRF_HEADER = 'X-CSRF-Token'
const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS'])

const errorBodySchema = z.object({
  detail: z.unknown(),
  code: z.string().optional(),
  params: z.record(z.string(), z.unknown()).optional(),
})

/** A non-2xx API response. `code` is what the UI translates; `detail` is English. */
export class ApiError extends Error {
  readonly status: number
  readonly code: string | undefined
  readonly params: Record<string, unknown>

  constructor(
    status: number,
    code: string | undefined,
    params: Record<string, unknown>,
    detail: string,
  ) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.params = params
  }
}

/** The server answered with data that does not match what the UI was built against. */
export class ContractError extends Error {
  constructor(path: string, cause: z.ZodError) {
    super(`Unexpected response from ${path}: ${z.prettifyError(cause)}`)
    this.name = 'ContractError'
  }
}

function readCookie(name: string): string | undefined {
  const prefix = `${name}=`
  return document.cookie
    .split('; ')
    .find((part) => part.startsWith(prefix))
    ?.slice(prefix.length)
}

// The backend sets the CSRF cookie on any response; a first-time visitor whose first call is
// a POST has not received one yet, so fetch it once before sending the request.
async function csrfToken(): Promise<string | undefined> {
  const existing = readCookie(CSRF_COOKIE)
  if (existing) return existing
  await fetch('/api/health', { credentials: 'same-origin' })
  return readCookie(CSRF_COOKIE)
}

type Query = Record<string, string | number | boolean | undefined>

interface RequestOptions<T> {
  schema: z.ZodType<T>
  query?: Query
  body?: unknown
}

function buildUrl(path: string, query?: Query): string {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== '') params.set(key, String(value))
  }
  const search = params.toString()
  return search ? `/api${path}?${search}` : `/api${path}`
}

async function toApiError(response: Response): Promise<ApiError> {
  const parsed = errorBodySchema.safeParse(await response.json().catch(() => null))
  if (!parsed.success) return new ApiError(response.status, undefined, {}, response.statusText)
  const { detail, code, params } = parsed.data
  return new ApiError(
    response.status,
    code,
    params ?? {},
    typeof detail === 'string' ? detail : response.statusText,
  )
}

export async function apiRequest<T>(
  method: string,
  path: string,
  { schema, query, body }: RequestOptions<T>,
): Promise<T> {
  const headers = new Headers({ Accept: 'application/json' })
  // The browser sets a multipart Content-Type, boundary included, for FormData itself.
  const isForm = body instanceof FormData
  if (body !== undefined && !isForm) headers.set('Content-Type', 'application/json')
  if (!SAFE_METHODS.has(method)) {
    const token = await csrfToken()
    if (token) headers.set(CSRF_HEADER, token)
  }

  const response = await fetch(buildUrl(path, query), {
    method,
    headers,
    credentials: 'same-origin',
    body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
  })
  if (!response.ok) throw await toApiError(response)

  const data: unknown = response.status === 204 ? null : await response.json()
  const parsed = schema.safeParse(data)
  if (!parsed.success) throw new ContractError(path, parsed.error)
  return parsed.data
}

export const api = {
  get: <T>(path: string, schema: z.ZodType<T>, query?: Query) =>
    apiRequest('GET', path, { schema, query }),
  post: <T>(path: string, schema: z.ZodType<T>, body?: unknown) =>
    apiRequest('POST', path, { schema, body }),
  put: <T>(path: string, schema: z.ZodType<T>, body?: unknown) =>
    apiRequest('PUT', path, { schema, body }),
  patch: <T>(path: string, schema: z.ZodType<T>, body?: unknown) =>
    apiRequest('PATCH', path, { schema, body }),
  delete: <T>(path: string, schema: z.ZodType<T>) => apiRequest('DELETE', path, { schema }),
}

export const noContent = z.null()

export function isApiError(error: unknown, status?: number): error is ApiError {
  return error instanceof ApiError && (status === undefined || error.status === status)
}
