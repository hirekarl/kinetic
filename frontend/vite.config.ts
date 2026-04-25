import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  // In dev, proxy /api to the local FastAPI backend.
  // In production on Render, VITE_API_BASE_URL is set to the API service URL;
  // the frontend makes absolute requests to that URL directly.
  server:
    mode === 'development'
      ? {
          port: 5173,
          host: '127.0.0.1',
          proxy: {
            '/api': {
              target: 'http://127.0.0.1:8000',
              changeOrigin: true,
            },
          },
        }
      : undefined,
}));
