import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  publicDir: 'public',  // 明确指定 public 目录
  server: {
    port: 328,   // 前端端口
    host: true,  // ✅ 添加此行，允许网络访问
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:2004',
        changeOrigin: true,
        secure: false,
        ws: true,
        headers: {
          'Origin': 'http://127.0.0.1:2004'
        }
      }
    }
  }
})
