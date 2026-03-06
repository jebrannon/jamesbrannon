import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'happy-dom',
    globals: true,
    css: false,
    include: ['src/tests/**/*.test.js'],
    reporters: ['verbose']
  }
});
