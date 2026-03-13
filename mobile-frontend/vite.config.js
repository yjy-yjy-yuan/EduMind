import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const isIOS = mode === 'ios'
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget =
    env.VITE_MOBILE_PROXY_TARGET ||
    env.VITE_MOBILE_API_BASE_URL ||
    'http://127.0.0.1:2004'

  return {
    base: mode === 'android' || isIOS ? './' : '/',
    plugins: [vue()],
    build: isIOS
      ? {
          // Xcode may flatten copied resource paths; place hashed assets at bundle root for iOS build.
          assetsDir: '',
          rollupOptions: {
            output: {
              // Keep stable filenames for native container integration.
              entryFileNames: 'index.js',
              chunkFileNames: 'chunk-[name].js',
              assetFileNames: '[name][extname]'
            }
          }
        }
      : undefined,
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    server: {
      host: true,
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
          secure: false,
          ws: true
        }
      }
    }
  }
})
