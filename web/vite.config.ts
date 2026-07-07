import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// Built assets are served by FastAPI under /static/dist/. In dev, Vite proxies
// the API to the running FastAPI backend on :8000.
export default defineConfig({
  plugins: [svelte()],
  base: '/static/dist/',
  build: {
    outDir: '../src/zebra_label_gateway/webapp/static/dist',
    emptyOutDir: true,
    assetsDir: 'assets',
  },
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
