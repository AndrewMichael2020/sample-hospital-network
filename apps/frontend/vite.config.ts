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
    // Allow configurable API target via environment variable VITE_API_PROXY_TARGET (useful in Codespaces)
    // Default to http://localhost:8000 which matches `make api-start`. For the extended API use
    // VITE_API_PROXY_TARGET=http://localhost:8080 when launching the extended backend.
    proxy: (() => {
      const apiTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000';
      return {
        '/reference': { target: apiTarget, changeOrigin: true },
        '/scenarios': { target: apiTarget, changeOrigin: true },
        '/facilities': { target: apiTarget, changeOrigin: true },
        '/patients': { target: apiTarget, changeOrigin: true },
      };
    })()
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    exclude: ['**/tests/**', '**/node_modules/**'],
  },
})
