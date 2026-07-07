import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ command }) => ({
  plugins: [react()],
  base: command === 'build' ? '/study-agent/' : '/',
  build: {
    outDir: '../static',
    emptyOutDir: false,
    sourcemap: false,
    chunkSizeWarningLimit: 900,
  },
  server: {
    port: 5181,
    open: '/',
    proxy: {
      '/api/study-agent': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/plugins/study-agent': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
}));
