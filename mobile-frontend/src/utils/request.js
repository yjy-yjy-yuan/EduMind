import axios from 'axios'
import { API_BASE_URL } from '@/config'
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
  baseURL: API_BASE_URL,
  timeout: DEFAULT_TIMEOUT_MS,
  withCredentials: true
})

service.interceptors.request.use(
  (config) => {
    config.timeout = Number(config.timeout) > 0 ? Number(config.timeout) : DEFAULT_TIMEOUT_MS

    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }

    const token = storageGet('m_token')
    if (token) config.headers.Authorization = `Bearer ${token}`

    return config
  },
  (error) => Promise.reject(error)
)

service.interceptors.response.use(
  (response) => ({ data: response.data, status: response.status, headers: response.headers }),
  async (error) => {
    if (!shouldRetryRequest(error)) return Promise.reject(error)

    const config = error.config || {}
    const retryCount = toPositiveInt(config.retry, DEFAULT_RETRY_COUNT)
    config.__retryCount = toPositiveInt(config.__retryCount, 0)

    if (config.__retryCount >= retryCount) return Promise.reject(error)

    config.__retryCount += 1
    const retryDelay = toPositiveInt(config.retryDelay, DEFAULT_RETRY_DELAY_MS)
    const backoffDelay = Math.min(4000, retryDelay * (2 ** (config.__retryCount - 1)))
    await sleep(backoffDelay)

    return service(config)
  }
)

export default service
