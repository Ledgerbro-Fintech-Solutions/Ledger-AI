import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/extract-ocr-data': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/process-invoices': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/photo-to-csv': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/image-to-csv': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
