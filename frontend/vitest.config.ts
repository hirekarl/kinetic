import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['e2e/**', 'node_modules/**', 'dist/**'],
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      // Measure only files with testable runtime logic — exclude entry points,
      // ambient type declarations, config files, and test infrastructure.
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/main.tsx', // React entry point — boilerplate, not unit-testable
        'src/vite-env.d.ts', // ambient type declarations only
        'src/types/**', // type-only files, no runtime code
        'src/test/**', // test setup
        '**/*.test.{ts,tsx}',
        '**/*.spec.{ts,tsx}',
        'e2e/**',
        'node_modules/**',
        'dist/**',
      ],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
