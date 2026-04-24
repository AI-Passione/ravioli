import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    tailwindcss(),
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://app:8000',
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
    include: [
      '../../../tests/ravioli/frontend/**/*.{test,spec}.ts',
      './src/**/*.{test,spec}.ts'
    ]
  }
})
