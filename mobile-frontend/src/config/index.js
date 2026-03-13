const fromQuery = (() => {
  try {
    const url = new URL(window.location.href)
    const value = url.searchParams.get('apiBase')
    return value ? String(value) : ''
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
  fromQuery || import.meta.env.VITE_MOBILE_API_BASE_URL || ''
).replace(/\/+$/, '')

export const UI_ONLY_MODE = toBool(
  fromUiOnlyQuery || import.meta.env.VITE_MOBILE_UI_ONLY,
  true
)

export const withBase = (path) => {
  const p = String(path || '')
  if (!p) return API_BASE_URL || ''
  if (!API_BASE_URL) return p.startsWith('/') ? p : `/${p}`
  return p.startsWith('/') ? `${API_BASE_URL}${p}` : `${API_BASE_URL}/${p}`
}
