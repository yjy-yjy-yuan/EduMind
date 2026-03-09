const fromQuery = (() => {
  try {
    const url = new URL(window.location.href)
    const value = url.searchParams.get('apiBase')
    return value ? String(value) : ''
  } catch {
    return ''
  }
})()

export const API_BASE_URL = String(
  fromQuery || import.meta.env.VITE_MOBILE_API_BASE_URL || ''
).replace(/\/+$/, '')

export const withBase = (path) => {
  const p = String(path || '')
  if (!p) return API_BASE_URL || ''
  if (!API_BASE_URL) return p.startsWith('/') ? p : `/${p}`
  return p.startsWith('/') ? `${API_BASE_URL}${p}` : `${API_BASE_URL}/${p}`
}
