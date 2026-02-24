import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    port: 5173, // React dev server port (changed from 3000 due to AirPlay conflict)
    proxy: {
      // Proxy API requests to Flask backend
      '/api': {
        target: 'http://127.0.0.1:5000', // Flask backend URL (using 127.0.0.1 to avoid AirPlay on IPv6)
        changeOrigin: true,
      },
      // Proxy healthie routes to Flask backend
      '/healthie': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      // Proxy routes to FastAPI backend
      '/fastapi': {
        target: 'http://127.0.0.1:8000/api/v1', // FastAPI backend URL
        changeOrigin: true,
      },
      // NOTE: Removed '/iframe_healthie' proxy - these routes are now handled by React Router
      // The React app serves: /iframe_healthie_provider_sidebar, /iframe_healthie_provider_tab, /iframe_healthie_client_sidebar
    },
  },
})
