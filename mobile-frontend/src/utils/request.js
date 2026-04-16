import axios from 'axios'
import { getApiBaseUrl, isTrustedApiBaseUrl } from '@/config'
import { storageGet } from '@/utils/storage'

const DEFAULT_TIMEOUT_MS = 10000
const DEFAULT_RETRY_COUNT = 2
const DEFAULT_RETRY_DELAY_MS = 500
const RETRYABLE_METHODS = new Set(['get', 'head', 'options'])
const RETRYABLE_STATUS = new Set([408, 429, 500, 502, 503, 504])

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))
const normalizeMethod = (method) => String(method || 'get').toLowerCase()
const toPositiveInt = (value, fallback) => {
  const n = Number(value)
  return Number.isInteger(n) && n >= 0 ? n : fallback
}

const shouldRetryRequest = (error) => {
  const config = error?.config || {}
  if (config.__retryDisabled) return false

  const retryCount = toPositiveInt(config.retry, DEFAULT_RETRY_COUNT)
  if (retryCount <= 0) return false

  const retryMethods = Array.isArray(config.retryMethods)
    ? new Set(config.retryMethods.map((m) => normalizeMethod(m)))
    : RETRYABLE_METHODS
  if (!retryMethods.has(normalizeMethod(config.method))) return false

  const status = Number(error?.response?.status || 0)
  if (status > 0) return RETRYABLE_STATUS.has(status)

  const code = String(error?.code || '')
  return code === 'ECONNABORTED' || code === 'ETIMEDOUT' || code === 'ERR_NETWORK' || !error?.response
}

const service = axios.create({
  baseURL: '',
  timeout: DEFAULT_TIMEOUT_MS,
  withCredentials: true
})

service.interceptors.request.use(
  (config) => {
    config.baseURL = getApiBaseUrl()
    config.timeout = Number(config.timeout) > 0 ? Number(config.timeout) : DEFAULT_TIMEOUT_MS
    config.headers = config.headers || {}

    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }

    const requestBaseUrl = String(config.baseURL || '').trim()
    const token = storageGet('m_token')
    if (!requestBaseUrl || isTrustedApiBaseUrl(requestBaseUrl)) {
      if (token) config.headers.Authorization = `Bearer ${token}`
    } else {
      delete config.headers.Authorization
      delete config.headers.authorization
    }

    return config
  },
  (error) => Promise.reject(error)
)

const networkErrorDetail =
  '网络不可达，请检查是否与后端在同一 Wi‑Fi，或更换网络/重新配置后端地址后重试。'

function normalizeNetworkError(error) {
  if (error?.response?.data != null) return
  const code = String(error?.code || '')
  const msg = String(error?.message || '')
  if (code === 'ERR_NETWORK' || code === 'ETIMEDOUT' || code === 'ECONNABORTED' || msg.includes('Network')) {
    error.response = error.response || {}
    error.response.data = error.response.data || { detail: networkErrorDetail }
  }
}

service.interceptors.response.use(
  (response) => ({ data: response.data, status: response.status, headers: response.headers }),
  async (error) => {
    if (!shouldRetryRequest(error)) {
      normalizeNetworkError(error)
      return Promise.reject(error)
    }

    const config = error.config || {}
    const retryCount = toPositiveInt(config.retry, DEFAULT_RETRY_COUNT)
    config.__retryCount = toPositiveInt(config.__retryCount, 0)

    if (config.__retryCount >= retryCount) {
      normalizeNetworkError(error)
      return Promise.reject(error)
    }

    config.__retryCount += 1
    const retryDelay = toPositiveInt(config.retryDelay, DEFAULT_RETRY_DELAY_MS)
    const backoffDelay = Math.min(4000, retryDelay * (2 ** (config.__retryCount - 1)))
    await sleep(backoffDelay)

    return service(config)
  }
)

export default service
