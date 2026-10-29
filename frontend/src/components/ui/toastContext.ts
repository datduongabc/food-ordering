import { createContext, use } from 'react'

export const ToastContext = createContext<((message: string) => void) | null>(null)

/** Shows a short status message at the bottom of the screen. */
export function useToast(): (message: string) => void {
  const show = use(ToastContext)
  if (!show) throw new Error('useToast must be used inside <ToastProvider>')
  return show
}
