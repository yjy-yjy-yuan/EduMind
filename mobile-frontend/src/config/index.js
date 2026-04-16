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

const fromOverrideStorage = (() => {
  try {
    const raw = typeof localStorage !== 'undefined' ? localStorage.getItem('m_api_base_url_override') : null
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

const pickBuildEnvValue = (buildValue, viteValue = '') => {
  const fromBuild = String(buildValue || '').trim()
  if (fromBuild) return fromBuild
  return String(viteValue || '').trim()
}

const ENV_API_BASE_URL = pickBuildEnvValue(
  globalThis.__EDUMIND_ENV_API_BASE_URL__,
  import.meta.env.VITE_MOBILE_API_BASE_URL || ''
)
const ENV_UI_ONLY = pickBuildEnvValue(
  globalThis.__EDUMIND_ENV_UI_ONLY__,
  import.meta.env.VITE_MOBILE_UI_ONLY || ''
)
const ENV_ALLOW_UI_ONLY_IN_PROD = pickBuildEnvValue(
  globalThis.__EDUMIND_ENV_ALLOW_UI_ONLY_IN_PROD__,
  import.meta.env.VITE_ALLOW_UI_ONLY_IN_PROD || ''
)
const ENV_RECOMMENDATION_INCLUDE_EXTERNAL = pickBuildEnvValue(
  globalThis.__EDUMIND_ENV_RECOMMENDATION_INCLUDE_EXTERNAL__,
  import.meta.env.VITE_RECOMMENDATION_INCLUDE_EXTERNAL || ''
)
const ENV_RECOMMENDATION_HOME_INCLUDE_EXTERNAL = pickBuildEnvValue(
  globalThis.__EDUMIND_ENV_RECOMMENDATION_HOME_INCLUDE_EXTERNAL__,
  import.meta.env.VITE_RECOMMENDATION_HOME_INCLUDE_EXTERNAL || ''
)

const parseAbsoluteApiBaseUrl = (value) => {
  const text = String(value || '').trim()
  if (!text) return null
  try {
    const url = new URL(text)
    if (!['http:', 'https:'].includes(url.protocol)) return null
    return url
  } catch {
    return null
  }
}

const normalizeApiBaseUrl = (value) => {
  const parsed = parseAbsoluteApiBaseUrl(value)
  return parsed ? parsed.href.replace(/\/+$/, '') : ''
}

const LOCK_RUNTIME_API_BASE_IN_PROD = import.meta.env.PROD || Boolean(fromNative)

const TRUSTED_API_BASE_ORIGINS = (() => {
  const origins = new Set()
  for (const candidate of [fromNative, ENV_API_BASE_URL]) {
    const parsed = parseAbsoluteApiBaseUrl(candidate)
    if (parsed) origins.add(parsed.origin)
  }
  return origins
})()

const canUseRuntimeApiBase = (value, source) => {
  const normalized = normalizeApiBaseUrl(value)
  if (!normalized) return ''
  if (!LOCK_RUNTIME_API_BASE_IN_PROD) return normalized
  if (source === 'native' || source === 'env') return normalized
  if (TRUSTED_API_BASE_ORIGINS.size === 0) return ''

  const parsed = parseAbsoluteApiBaseUrl(normalized)
  return parsed && TRUSTED_API_BASE_ORIGINS.has(parsed.origin) ? normalized : ''
}

const resolveApiBaseConfig = ({
  queryValue = '',
  overrideValue = '',
  storageValue = '',
  nativeValue = '',
  envValue = ''
} = {}) => {
  const normalizedQuery = canUseRuntimeApiBase(queryValue, 'query')
  if (normalizedQuery) {
    return {
      apiBaseUrl: normalizedQuery,
      source: 'query'
    }
  }

  const normalizedOverride = canUseRuntimeApiBase(overrideValue, 'override')
  if (normalizedOverride) {
    return {
      apiBaseUrl: normalizedOverride,
      source: 'override'
    }
  }

  const normalizedNative = canUseRuntimeApiBase(nativeValue, 'native')
  if (normalizedNative) {
    return {
      apiBaseUrl: normalizedNative,
      source: 'native'
    }
  }

  const normalizedStorage = canUseRuntimeApiBase(storageValue, 'storage')
  if (normalizedStorage) {
    return {
      apiBaseUrl: normalizedStorage,
      source: 'storage'
    }
  }

  const normalizedEnv = canUseRuntimeApiBase(envValue, 'env')
  if (normalizedEnv) {
    return {
      apiBaseUrl: normalizedEnv,
      source: 'env'
    }
  }

  return {
    apiBaseUrl: '',
    source: 'empty'
  }
}

const getRuntimeApiBaseConfig = () => {
  try {
    const queryValue = typeof window !== 'undefined' && window.location?.search
      ? new URLSearchParams(window.location.search).get('apiBase') || ''
      : ''
    const overrideValue = typeof localStorage !== 'undefined'
      ? localStorage.getItem('m_api_base_url_override') || ''
      : ''
    const storageValue = typeof localStorage !== 'undefined'
      ? localStorage.getItem('m_api_base_url') || ''
      : ''
    const nativeValue = window.__edumindNativeConfig?.apiBaseUrl || ''
    return resolveApiBaseConfig({
      queryValue,
      overrideValue,
      storageValue,
      nativeValue,
      envValue: ENV_API_BASE_URL
    })
  } catch {
    return initialApiBaseConfig
  }
}

const initialApiBaseConfig = resolveApiBaseConfig({
  queryValue: fromQuery,
  overrideValue: fromOverrideStorage,
  storageValue: fromStorage,
  nativeValue: fromNative,
  envValue: ENV_API_BASE_URL
})

export const API_BASE_URL = initialApiBaseConfig.apiBaseUrl

console.info(
  `[INFO][Config] api base=${API_BASE_URL || '<empty>'} source=${initialApiBaseConfig.source}`
)

if (fromNative && fromNative !== fromStorage && !fromOverrideStorage) {
  try {
    localStorage.setItem('m_api_base_url', normalizeApiBaseUrl(fromNative))
  } catch {
    // Ignore storage write failures in restricted WebView contexts.
  }
}

export function isTrustedApiBaseUrl(url) {
  const normalized = normalizeApiBaseUrl(url)
  if (!normalized) return false
  if (!LOCK_RUNTIME_API_BASE_IN_PROD || TRUSTED_API_BASE_ORIGINS.size === 0) return true

  const parsed = parseAbsoluteApiBaseUrl(normalized)
  return Boolean(parsed && TRUSTED_API_BASE_ORIGINS.has(parsed.origin))
}

/** 运行时设置 API 基地址（换 Wi‑Fi/换地点后可用，避免因本机 IP 变化导致请求失败） */
export function setApiBaseUrl(url) {
  try {
    const value = normalizeApiBaseUrl(url)
    const allowOverride = !value || isTrustedApiBaseUrl(value)
    if (typeof localStorage !== 'undefined') {
      if (value && allowOverride) localStorage.setItem('m_api_base_url_override', value)
      else localStorage.removeItem('m_api_base_url_override')
    }
    if (value && !allowOverride) {
      console.warn('[WARN][Config] ignore untrusted api base override:', value)
    }
    const runtimeConfig = getRuntimeApiBaseConfig()
    console.info(
      `[INFO][Config] api base=${runtimeConfig.apiBaseUrl || '<empty>'} source=${runtimeConfig.source}`
    )
    return value
  } catch {
    return ''
  }
}

/** 当前 API 基地址（每次调用都会重新读取 localStorage，便于换网络后生效） */
export function getApiBaseUrl() {
  try {
    return getRuntimeApiBaseConfig().apiBaseUrl
  } catch {
    return API_BASE_URL
  }
}

export function getApiBaseSource() {
  return getRuntimeApiBaseConfig().source
}

export const UI_ONLY_MODE = toBool(
  fromUiOnlyQuery || ENV_UI_ONLY,
  false
)

const ALLOW_UI_ONLY_IN_PROD = toBool(ENV_ALLOW_UI_ONLY_IN_PROD, false)

export const shouldUseMockApi = () => {
  if (!UI_ONLY_MODE || getApiBaseUrl()) return false
  if (!import.meta.env.PROD) return true
  return ALLOW_UI_ONLY_IN_PROD
}

/** 推荐接口是否默认附带站外检索（历史名；未单独配置首页时仍可读此变量） */
export const shouldIncludeExternalRecommendationsByDefault = () =>
  toBool(ENV_RECOMMENDATION_INCLUDE_EXTERNAL, false)

/**
 * 首页「推荐预览」是否附带站外检索与后端自动入库闭环。
 * 默认 true：与推荐中枢一致，登录态下后端可将可导入站外候选写入 videos 后再返回可打开详情的条目。
 * 弱网/仅站内时可设 VITE_RECOMMENDATION_HOME_INCLUDE_EXTERNAL=false。
 */
export const shouldIncludeExternalRecommendationsOnHome = () =>
  toBool(ENV_RECOMMENDATION_HOME_INCLUDE_EXTERNAL, true)

export const withBase = (path) => {
  const p = String(path || '')
  const base = getApiBaseUrl()
  if (!p) return base || ''
  if (!base) return p.startsWith('/') ? p : `/${p}`
  return p.startsWith('/') ? `${base}${p}` : `${base}/${p}`
}
