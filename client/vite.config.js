import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/ats': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/jds': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/pdfs': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
