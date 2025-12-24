import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0', // Allow access from local network (for mobile testing)
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // Update this to your backend Gateway URL
        changeOrigin: true,
        // rewrite: (path) => path.replace(/^\/api/, ''), // Keep /api if backend expects it
      },
    },
  },
})
