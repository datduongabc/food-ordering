import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router'
import { Loading } from '@/components/ui/StatusView'
import { useCurrentUser } from './queries'
import type { User } from './schemas'

/** Sends visitors to sign in, then back here; renders `children` with the signed-in user. */
export function RequireAuth({ children }: { children: (user: User) => ReactNode }) {
  const user = useCurrentUser()
  const location = useLocation()
  if (user === undefined) return <Loading />
  if (user === null) {
    const next = `${location.pathname}${location.search}`
    return <Navigate to={`/login?next=${encodeURIComponent(next)}`} replace />
  }
  return children(user)
}
