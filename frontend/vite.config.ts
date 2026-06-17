import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
    define: {
      // Make VITE_API_BASE_URL available in the app
      // Falls back to relative '/api' for local dev (proxied by vite below)
      __API_BASE_URL__: JSON.stringify(env.VITE_API_BASE_URL || ''),
    },
    server: {
      // Local dev: proxy /api calls to Django at port 8000
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      // Generate source maps for production debugging (optional)
      sourcemap: false,
      // Chunk size warning threshold
      chunkSizeWarningLimit: 1000,
    },
  }
})
