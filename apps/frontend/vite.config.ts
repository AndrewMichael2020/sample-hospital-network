/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5176,
  // Allow all hosts in dev so Codespaces / preview domains can reach the dev server.
  // This is safe for local development but should not be used in production builds.
  allowedHosts: true,
    proxy: {
      // Proxy API requests to backend running on the Codespace host
      '/reference': {
        target: 'http://localhost:8080',
        changeOrigin: true
      },
      '/scenarios': {
        target: 'http://localhost:8080',
        changeOrigin: true
      },
      '/facilities': {
        target: 'http://localhost:8080',
        changeOrigin: true
      },
      '/patients': {
        target: 'http://localhost:8080',
        changeOrigin: true
      }
    }
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    exclude: ['**/tests/**', '**/node_modules/**'],
  },
})
