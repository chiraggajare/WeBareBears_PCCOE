import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Dev: the React app runs on :5173 and proxies /api to the FastAPI backend on :8000.
// Build: `npm run build` -> web/dist, which FastAPI also serves on :8000 (single-command demo).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5173, proxy: { '/api': 'http://127.0.0.1:8000' } },
  build: {
    // "Baseline widely available" browsers: current Chrome/Edge, Firefox, Safari (macOS + iOS/iPadOS),
    // Samsung Internet and Android WebView. Tailwind CSS 4 needs Safari 16.4+, Chrome 111+, Firefox 128+.
    target: 'baseline-widely-available',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (id.includes('node_modules/recharts') || id.includes('node_modules/d3-')) return 'charts'
          if (/node_modules\/(react|react-dom|react-router|react-router-dom|scheduler)\//.test(id)) return 'react'
        },
      },
    },
  },
})
