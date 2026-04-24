import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath } from 'url'
import path from 'path'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [
    tailwindcss(),
  ],
  resolve: {
    alias: {
      'postcss': path.resolve(__dirname, 'node_modules/postcss'),
      '@tailwindcss/postcss': path.resolve(__dirname, 'node_modules/@tailwindcss/postcss')
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://backend:8000',
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
