import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // Proxy /api calls to FastAPI during development so you don't need CORS headers
      "/api": {
        target:      "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
})
