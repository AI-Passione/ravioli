import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    },
    fs: {
      allow: ['../../..']
    }
  },
  test: {
    environment: 'happy-dom',
    globals: true,
    include: ['../../../tests/ravioli/frontend/**/*.{test,spec}.ts']
  }
})
