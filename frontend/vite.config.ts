import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://backend:6565',
        changeOrigin: true,
      },
      '/nav_icons': {
        target: 'http://backend:6565',
        changeOrigin: true,
      },
      '/nav_backgrounds': {
        target: 'http://backend:6565',
        changeOrigin: true,
      },
    },
  },
})
