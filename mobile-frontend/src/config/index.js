const fromQuery = (() => {
  try {
    const url = new URL(window.location.href)
    const value = url.searchParams.get('apiBase')
    return value ? String(value) : ''
  } catch {
    return ''
  }
})()

const fromStorage = (() => {
  try {
    const raw = typeof localStorage !== 'undefined' ? localStorage.getItem('m_api_base_url') : null
    return raw ? String(raw).trim() : ''
  } catch {
    return ''
  }
})()

const fromNative = (() => {
  try {
    const value = window.__edumindNativeConfig?.apiBaseUrl
    return value ? String(value).trim() : ''
  } catch {
    return ''
  }
})()

const fromUiOnlyQuery = (() => {
  try {
    const url = new URL(window.location.href)
    const value = url.searchParams.get('uiOnly')
    return value == null ? '' : String(value).trim()
  } catch {
    return ''
  }
})()

const toBool = (value, fallback = false) => {
  const text = String(value || '').trim().toLowerCase()
  if (!text) return fallback
  if (['1', 'true', 'yes', 'on'].includes(text)) return true
  if (['0', 'false', 'no', 'off'].includes(text)) return false
  return fallback
}

export const API_BASE_URL = String(
  fromQuery || fromStorage || fromNative || import.meta.env.VITE_MOBILE_API_BASE_URL || ''
).replace(/\/+$/, '')

if (!fromStorage && fromNative) {
  try {
    localStorage.setItem('m_api_base_url', fromNative.replace(/\/+$/, ''))
  } catch {
    // Ignore storage write failures in restricted WebView contexts.
  }
}

/** 运行时设置 API 基地址（换 Wi‑Fi/换地点后可用，避免因本机 IP 变化导致请求失败） */
export function setApiBaseUrl(url) {
  try {
    const value = url ? String(url).trim().replace(/\/+$/, '') : ''
    if (typeof localStorage !== 'undefined') {
      if (value) localStorage.setItem('m_api_base_url', value)
      else localStorage.removeItem('m_api_base_url')
    }
    return value
  } catch {
    return ''
  }
}

/** 当前 API 基地址（每次调用都会重新读取 localStorage，便于换网络后生效） */
export function getApiBaseUrl() {
  try {
    const q = typeof window !== 'undefined' && window.location?.search
      ? new URLSearchParams(window.location.search).get('apiBase') || ''
      : ''
    const s = typeof localStorage !== 'undefined' ? localStorage.getItem('m_api_base_url') || '' : ''
    const n = window.__edumindNativeConfig?.apiBaseUrl || ''
    return String(q || s || n || import.meta.env.VITE_MOBILE_API_BASE_URL || '').replace(/\/+$/, '')
  } catch {
    return API_BASE_URL
  }
}

export const UI_ONLY_MODE = toBool(
  fromUiOnlyQuery || import.meta.env.VITE_MOBILE_UI_ONLY,
  true
)

export const shouldUseMockApi = () => UI_ONLY_MODE && !getApiBaseUrl()

export const withBase = (path) => {
  const p = String(path || '')
  const base = getApiBaseUrl()
  if (!p) return base || ''
  if (!base) return p.startsWith('/') ? p : `/${p}`
  return p.startsWith('/') ? `${base}${p}` : `${base}/${p}`
}
