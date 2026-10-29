import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'

const backend = process.env.DATENO_API_URL ?? 'http://127.0.0.1:8000'

// The API is proxied rather than called cross-origin so the session and CSRF cookies stay
// first-party (SameSite=Lax) and the backend needs no CORS configuration.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': backend,
      '/media': backend,
    },
  },
})
