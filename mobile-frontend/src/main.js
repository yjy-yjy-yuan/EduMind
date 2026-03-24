import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { bootstrapNativeBridge } from '@/services/nativeBridge'
import './styles.css'

window.__edumindBootStarted = true
window.__edumindBootMounted = false
window.__edumindBootTrace = window.__edumindBootTrace || []

const emitBootLog = (level, scope, label, details = '') => {
  const entry = details ? `${label} | ${details}` : label
  console[level](`[${String(level).toUpperCase()}][${scope}] ${entry}`)
  return entry
}

const pushBootTrace = (label, details = '') => {
  const entry = emitBootLog('log', 'Trace', label, details)
  window.__edumindBootTrace.push(entry)
  if (window.__edumindBootTrace.length > 40) {
    window.__edumindBootTrace = window.__edumindBootTrace.slice(-40)
  }
}

const pushBootInfo = (scope, label, details = '') => emitBootLog('info', scope, label, details)
const pushBootDebug = (scope, label, details = '') => emitBootLog('debug', scope, label, details)
const pushBootError = (scope, label, details = '') => emitBootLog('error', scope, label, details)

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

pushBootTrace('main:module-start', `protocol=${window.location.protocol}`)
pushBootTrace('document:readyState', document.readyState)
pushBootInfo('Bootstrap', 'started', `href=${window.location.href}`)
pushBootDebug('Bootstrap', 'user-agent', navigator.userAgent)

bootstrapNativeBridge()
  .then((state) => {
    if (!state?.available) {
      pushBootDebug('NativeBridge', 'unavailable', 'running without iOS native bridge')
      return
    }
    pushBootInfo('NativeBridge', 'ready', JSON.stringify(state.capabilities || {}))
  })
  .catch((error) => {
    pushBootError('NativeBridge', 'bootstrap-failed', error?.message || String(error || 'Unknown native bridge error'))
  })

document.addEventListener('DOMContentLoaded', () => {
  pushBootTrace('document:DOMContentLoaded', describeContainer())
  pushBootDebug('Bootstrap', 'DOMContentLoaded', `title=${document.title || '<empty>'}`)
})

window.addEventListener('load', () => {
  pushBootTrace('window:load', describeContainer())
  pushBootDebug('Bootstrap', 'window-load', `readyState=${document.readyState}`)
})

const describeContainer = () => {
  const root = document.getElementById('app')
  if (!root) return 'container=<missing>'
  return `container=present childCount=${root.childElementCount} textLength=${String(root.textContent || '').trim().length}`
}

const waitForMountTarget = () =>
  new Promise((resolve) => {
    const existing = document.getElementById('app')
    if (existing) {
      pushBootTrace('mount-target:ready', describeContainer())
      pushBootDebug('Bootstrap', 'mount-target:ready', `readyState=${document.readyState}`)
      resolve(existing)
      return
    }

    pushBootTrace('mount-target:wait', `readyState=${document.readyState}`)

    const onReady = () => {
      const root = document.getElementById('app')
      pushBootTrace('mount-target:dom-ready', describeContainer())
      pushBootDebug('Bootstrap', 'mount-target:dom-ready', `hasRoot=${Boolean(root)}`)
      if (root) {
        resolve(root)
        return
      }

      // Give the parser one more frame in file:// WebView scenes.
      window.requestAnimationFrame(() => {
        pushBootTrace('mount-target:raf-check', describeContainer())
        resolve(document.getElementById('app'))
      })
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', onReady, { once: true })
      return
    }

    onReady()
  })

window.addEventListener('error', (event) => {
  const msg = event?.error?.stack || event?.message || 'Unknown runtime error'
  pushBootTrace('window:error', msg)
  pushBootError('Bootstrap', 'window-error', msg)
  renderBootError('页面启动异常', msg)
})

window.addEventListener('unhandledrejection', (event) => {
  const reason = event?.reason
  const msg = reason?.stack || String(reason || 'Unknown rejection')
  pushBootTrace('window:unhandledrejection', msg)
  pushBootError('Bootstrap', 'unhandledrejection', msg)
  renderBootError('页面启动异常（Promise）', msg)
})

try {
  pushBootTrace('app:create')
  const app = createApp(App)
  pushBootTrace('app:use-router')
  app.use(router)
  pushBootTrace('router:isReady:wait')
  router
    .isReady()
    .then(async () => {
      pushBootTrace('router:isReady:resolved', `path=${router.currentRoute.value.fullPath}`)
      const root = await waitForMountTarget()
      if (!root) {
        pushBootTrace('mount-target:missing-after-wait', `readyState=${document.readyState}`)
        renderBootError('页面挂载失败', '未找到 #app 容器，请检查 index.html 是否包含 <div id="app"></div>。')
        return
      }

      pushBootTrace('app:mount:start', describeContainer())
      pushBootInfo('Bootstrap', 'app:mount:start', describeContainer())
      pushBootDebug('Router', 'current-route', router.currentRoute.value.fullPath)
      app.mount(root)
      pushBootTrace('app:mount:end', describeContainer())
      pushBootDebug('Bootstrap', 'app:mount:end', describeContainer())
      window.requestAnimationFrame(() => {
        const containerState = describeContainer()
        window.__edumindBootMounted = true
        pushBootTrace('app:mounted:raf', `${router.currentRoute.value.fullPath} | ${containerState}`)
        pushBootInfo('Bootstrap', 'app:mounted', `${router.currentRoute.value.fullPath} | ${containerState}`)
        pushBootDebug('Bootstrap', 'trace-size', String(window.__edumindBootTrace.length))
      })
    })
    .catch((error) => {
      const msg = error?.stack || String(error || 'Unknown router bootstrap error')
      pushBootTrace('router:isReady:rejected', msg)
      pushBootError('Router', 'isReady:rejected', msg)
      renderBootError('页面路由初始化失败', msg)
    })
} catch (error) {
  const msg = error?.stack || String(error || 'Unknown bootstrap error')
  pushBootTrace('app:create-failed', msg)
  pushBootError('Bootstrap', 'create-failed', msg)
  renderBootError('页面初始化失败', msg)
}
