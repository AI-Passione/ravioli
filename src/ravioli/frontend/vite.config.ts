import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath } from 'url'
import path from 'path'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

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
      './tests/**/*.{test,spec}.ts'
    ]
  }
})
