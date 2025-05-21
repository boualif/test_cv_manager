// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'https://test-cv-manager.onrender.com',
        changeOrigin: true,
        secure: true, // Change to true since you're using HTTPS
      },
    },
  },
})
