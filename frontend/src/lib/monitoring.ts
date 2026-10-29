/**
 * Error reporting to Sentry, switched on by VITE_SENTRY_DSN at build time. The SDK is loaded
 * only then, and after the first render, so it costs visitors nothing otherwise.
 */
type Reporter = (error: unknown) => void

let report: Reporter = () => {}

export function startMonitoring(dsn: string | undefined = import.meta.env.VITE_SENTRY_DSN) {
  if (!dsn) return Promise.resolve()
  return import('@sentry/react').then((Sentry) => {
    Sentry.init({
      dsn,
      environment: import.meta.env.MODE,
      // No IP addresses, cookies or form contents: they hold customers' personal data.
      sendDefaultPii: false,
    })
    report = (error) => Sentry.captureException(error)
  })
}

/** Sends an error the app caught itself, such as one shown on the error page. */
export function reportError(error: unknown) {
  report(error)
}
