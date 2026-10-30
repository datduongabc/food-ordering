import { useEffect, useId, useRef, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router'
import { useLogout } from '@/features/auth/api'
import { useCurrentUser } from '@/features/auth/queries'
import { useToast } from '@/components/ui/toastContext'
import { useI18n } from '@/i18n/context'
import styles from './UserMenu.module.css'

function UserIcon() {
  return (
    <svg
      aria-hidden="true"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </svg>
  )
}

/** The account button: sign-in links for guests; admin, account and sign-out once signed in. */
export function UserMenu() {
  const { t } = useI18n()
  const user = useCurrentUser()
  const location = useLocation()
  const navigate = useNavigate()
  const logout = useLogout()
  const toast = useToast()
  // As with the phone menu, remembering where it was opened closes it on navigation.
  const [openOn, setOpenOn] = useState<string | null>(null)
  const open = openOn === location.pathname
  const panelId = useId()
  const root = useRef<HTMLDivElement>(null)
  const button = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!open) return
    const closeOutside = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpenOn(null)
    }
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return
      setOpenOn(null)
      button.current?.focus()
    }
    document.addEventListener('pointerdown', closeOutside)
    document.addEventListener('keydown', closeOnEscape)
    return () => {
      document.removeEventListener('pointerdown', closeOutside)
      document.removeEventListener('keydown', closeOnEscape)
    }
  }, [open])

  const close = () => setOpenOn(null)
  const itemClass = ({ isActive }: { isActive: boolean }) =>
    isActive ? `${styles.item} ${styles.active}` : styles.item

  return (
    <div className={styles.root} ref={root}>
      <button
        ref={button}
        type="button"
        className={styles.button}
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={t.nav.userMenu}
        data-signed-in={Boolean(user)}
        onClick={() => setOpenOn(open ? null : location.pathname)}
      >
        {user ? (
          <span aria-hidden="true" className={styles.initial}>
            {user.name.trim().charAt(0).toUpperCase()}
          </span>
        ) : (
          <UserIcon />
        )}
      </button>

      {open && (
        <div id={panelId} className={styles.panel}>
          {user ? (
            <>
              <div className={styles.who}>
                <span className={styles.name}>{user.name}</span>
                <span className={styles.email}>{user.email}</span>
              </div>
              {user.role === 'ADMIN' && (
                <NavLink to="/admin" className={itemClass} onClick={close}>
                  {t.nav.admin}
                </NavLink>
              )}
              <NavLink to="/account" className={itemClass} onClick={close}>
                {t.nav.account}
              </NavLink>
              <button
                type="button"
                className={`${styles.item} ${styles.signOut}`}
                disabled={logout.isPending}
                onClick={() =>
                  logout.mutate(undefined, {
                    onSettled: () => {
                      close()
                      toast(t.auth.loggedOut)
                      navigate('/')
                    },
                  })
                }
              >
                {t.auth.logout}
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className={`${styles.item} ${styles.primary}`} onClick={close}>
                {t.nav.signIn}
              </Link>
              <Link to="/register" className={styles.item} onClick={close}>
                {t.auth.register}
              </Link>
            </>
          )}
        </div>
      )}
    </div>
  )
}
