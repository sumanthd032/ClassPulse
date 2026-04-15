import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL ?? 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: process.env.VITE_WS_URL ?? 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // React core — changes least often
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          // Data fetching / state
          'vendor-query': ['@tanstack/react-query', 'axios', 'zustand'],
          // Forms
          'vendor-forms': ['react-hook-form', '@hookform/resolvers', 'zod'],
          // Animation + UI
          'vendor-ui': ['framer-motion', 'lucide-react', 'react-hot-toast'],
          // Date utils
          'vendor-date': ['date-fns'],
        },
      },
    },
  },
})
