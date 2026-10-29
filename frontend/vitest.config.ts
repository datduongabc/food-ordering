import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config.ts'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      include: ['tests/unit/**/*.test.{ts,tsx}', 'tests/integration/**/*.test.{ts,tsx}'],
      setupFiles: ['tests/setup.ts'],
      restoreMocks: true,
      unstubGlobals: true,
      // Every jsdom worker loads the whole environment at start; with one per core they
      // contend for disk and one can miss Vitest's fixed 60 s start timeout, silently dropping
      // its test file from the run.
      maxWorkers: '50%',
    },
  }),
)
