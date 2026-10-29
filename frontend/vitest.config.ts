import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config.ts'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      restoreMocks: true,
      unstubGlobals: true,
      // Starting a jsdom worker is mostly disk reads; on a slow filesystem (e.g. WSL reading a
      // Windows drive) one per core can miss Vitest's fixed 60 s worker start timeout, which
      // silently drops that worker's test file from the run.
      maxWorkers: 4,
      coverage: {
        provider: 'v8',
        include: ['src/**'],
        // The entry point only mounts the app; every route is exercised through the router.
        exclude: ['src/main.tsx'],
        thresholds: { statements: 85, lines: 85, functions: 80, branches: 80 },
      },
      projects: [
        {
          extends: true,
          test: {
            // Pure logic needs no DOM, so it skips the cost of a browser environment.
            name: 'unit',
            environment: 'node',
            include: ['tests/unit/*.test.ts'],
          },
        },
        {
          extends: true,
          test: {
            name: 'dom',
            environment: 'jsdom',
            include: ['tests/unit/browser/**/*.test.ts', 'tests/integration/**/*.test.tsx'],
            setupFiles: ['tests/setup.ts'],
          },
        },
      ],
    },
  }),
)
