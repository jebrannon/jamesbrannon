import { defineConfig } from 'vite';
import { fileURLToPath, URL } from 'url';

const projectRoot = fileURLToPath(new URL('.', import.meta.url));

export default defineConfig({
  root: projectRoot,
  server: {
    host: '127.0.0.1',
    port: 3000,
    proxy: {
      '/api':   'http://127.0.0.1:8000',
      '/admin': 'http://127.0.0.1:8000',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
});
