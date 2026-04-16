import { fileURLToPath, URL } from 'node:url'
import fs from 'node:fs'
import path from 'node:path'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ command, mode }) => {
  const isWebBuild = mode === 'web'
  const isNativeBuild = command === 'build' && !isWebBuild
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget =
    env.VITE_MOBILE_PROXY_TARGET ||
    env.VITE_MOBILE_API_BASE_URL ||
    'http://127.0.0.1:2004'
  const injectedRuntimeConfig = {
    'globalThis.__EDUMIND_ENV_API_BASE_URL__': JSON.stringify(env.VITE_MOBILE_API_BASE_URL || ''),
    'globalThis.__EDUMIND_ENV_UI_ONLY__': JSON.stringify(env.VITE_MOBILE_UI_ONLY || ''),
    'globalThis.__EDUMIND_ENV_ALLOW_UI_ONLY_IN_PROD__': JSON.stringify(env.VITE_ALLOW_UI_ONLY_IN_PROD || ''),
    'globalThis.__EDUMIND_ENV_RECOMMENDATION_INCLUDE_EXTERNAL__': JSON.stringify(
      env.VITE_RECOMMENDATION_INCLUDE_EXTERNAL || ''
    ),
    'globalThis.__EDUMIND_ENV_RECOMMENDATION_HOME_INCLUDE_EXTERNAL__': JSON.stringify(
      env.VITE_RECOMMENDATION_HOME_INCLUDE_EXTERNAL || ''
    )
  }

  const iosClassicScriptPlugin = {
    name: 'ios-classic-script',
    closeBundle() {
      if (!isNativeBuild) return
      const htmlPath = path.resolve(process.cwd(), 'dist/index.html')
      if (!fs.existsSync(htmlPath)) return

      const cssPath = path.resolve(process.cwd(), 'dist/style.css')
      const targetCssPath = path.resolve(process.cwd(), 'dist/index.css')
      if (fs.existsSync(cssPath)) {
        fs.renameSync(cssPath, targetCssPath)
      }

      const original = fs.readFileSync(htmlPath, 'utf8')
      let updated = original.replace(
        /<script type="module"(?:\s+crossorigin)? src="\.\/index\.js"><\/script>/,
        '<script defer src="./index.js"></script>'
      )
      updated = updated.replace(/href="\.\/style\.css"/, 'href="./index.css"')

      if (updated !== original) {
        fs.writeFileSync(htmlPath, updated)
      }
    }
  }

  return {
    // Use relative asset paths for packaged builds (file:// in WebView).
    base: isNativeBuild ? './' : '/',
    define: injectedRuntimeConfig,
    plugins: [vue(), iosClassicScriptPlugin],
    build: isNativeBuild
      ? {
          modulePreload: false,
          cssCodeSplit: false,
          // iOS WKWebView 采用单文件 iife 输出（inlineDynamicImports=true），
          // 路由懒加载不会生成独立 chunk，默认 500KB 告警在该模式下噪声较大。
          chunkSizeWarningLimit: 700,
          // Xcode may flatten copied resource paths; place hashed assets at bundle root for iOS build.
          assetsDir: '',
          rollupOptions: {
            output: {
              format: 'iife',
              inlineDynamicImports: true,
              // Keep stable filenames for native container integration.
              entryFileNames: 'index.js',
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
