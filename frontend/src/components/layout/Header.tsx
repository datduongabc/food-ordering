import { useId, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router'
import { useLogout } from '@/features/auth/api'
import { useCurrentUser } from '@/features/auth/queries'
import { useToast } from '@/components/ui/toastContext'
import { useCart } from '@/features/cart/useCart'
import { useI18n } from '@/i18n/context'
import { interpolate } from '@/lib/format'
import { LanguageToggle } from './LanguageToggle'
import styles from './Header.module.css'

function CartIcon() {
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
      <path d="M3 4h2l2.4 11.2a2 2 0 0 0 2 1.6h7.7a2 2 0 0 0 2-1.5L21 8H6" />
      <circle cx="10" cy="20.5" r="1.2" />
      <circle cx="17" cy="20.5" r="1.2" />
    </svg>
  )
}

export function Header() {
  const { t } = useI18n()
  const user = useCurrentUser()
  const { cart } = useCart()
  const location = useLocation()
  const navigate = useNavigate()
  const logout = useLogout()
  const toast = useToast()
  // Remembering where the mobile menu was opened closes it once the customer navigates away.
  const [openOn, setOpenOn] = useState<string | null>(null)
  const open = openOn === location.pathname
  const navId = useId()
  const count = cart?.total_count ?? 0

  const navClass = ({ isActive }: { isActive: boolean }) =>
    isActive ? `${styles.navLink} ${styles.active}` : styles.navLink

  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <Link to="/" className={styles.brand}>
          <span className={styles.brandKicker}>{t.common.brandKicker}</span>
          <span className={styles.brandName}>DaTeNO</span>
        </Link>

        <div className={styles.tools}>
          <Link to="/cart" className={styles.cart} aria-label={interpolate(t.nav.cart, { count })}>
            <CartIcon />
            <span>{count}</span>
          </Link>
          <LanguageToggle />
          <button
            type="button"
            className={styles.menuButton}
            aria-expanded={open}
            aria-controls={navId}
            aria-label={t.nav.label}
            onClick={() => setOpenOn(open ? null : location.pathname)}
          >
            <span aria-hidden="true">{open ? '✕' : '☰'}</span>
          </button>
        </div>

        <nav id={navId} aria-label={t.nav.label} className={styles.nav} data-open={open}>
          <NavLink to="/menu" className={navClass}>
            {t.nav.menu}
          </NavLink>
          <Link to="/#book" className={styles.navLink}>
            {t.nav.book}
          </Link>
          <a href="#branches" className={styles.navLink}>
            {t.nav.branches}
          </a>
          {user ? (
            <>
              {user.role === 'ADMIN' && (
                <NavLink to="/admin" className={navClass}>
                  {t.nav.admin}
                </NavLink>
              )}
              <NavLink to="/account" className={navClass}>
                {t.nav.account}
              </NavLink>
              <button
                type="button"
                className={styles.navLink}
                disabled={logout.isPending}
                onClick={() =>
                  logout.mutate(undefined, {
                    onSettled: () => {
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
            <NavLink to="/login" className={`${styles.navLink} ${styles.signIn}`}>
              {t.nav.signIn}
            </NavLink>
          )}
        </nav>
      </div>
    </header>
  )
}
