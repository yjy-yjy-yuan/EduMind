import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './styles.css'

const renderBootError = (title, details) => {
  const root = document.getElementById('app') || document.body
  if (!root) return
  root.innerHTML = `
    <div style="padding:16px;font-family:-apple-system, BlinkMacSystemFont, 'PingFang SC', sans-serif;color:#111827;">
      <h3 style="margin:0 0 8px;">${title}</h3>
      <pre style="white-space:pre-wrap;word-break:break-word;background:#f3f4f6;border-radius:8px;padding:10px;">${details || ''}</pre>
    </div>
  `
}

window.addEventListener('error', (event) => {
  const msg = event?.error?.stack || event?.message || 'Unknown runtime error'
  renderBootError('页面启动异常', msg)
})

window.addEventListener('unhandledrejection', (event) => {
  const reason = event?.reason
  const msg = reason?.stack || String(reason || 'Unknown rejection')
  renderBootError('页面启动异常（Promise）', msg)
})

try {
  createApp(App).use(router).mount('#app')
} catch (error) {
  const msg = error?.stack || String(error || 'Unknown bootstrap error')
  renderBootError('页面初始化失败', msg)
}
