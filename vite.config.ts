
import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig } from 'vite';

export default defineConfig(() => {
  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      // Configure HMR based on the environment.
      hmr: process.env.DISABLE_HMR !== 'true',

      // Disable file watching when DISABLE_HMR is true.
      watch: process.env.DISABLE_HMR === 'true' ? null : {},

      // Forward API requests to FastAPI.
      proxy: {
        '/api': {
          target:
            process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8010',
          changeOrigin: true,
        },
      },
    },
  };
});
