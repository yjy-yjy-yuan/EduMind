import { getApiBaseUrl, shouldUseMockApi } from '@/config'

const RETRYABLE_SERVER_STATUS = new Set([500, 502, 503, 504])
const NETWORK_ERROR_CODES = new Set(['ERR_NETWORK', 'ETIMEDOUT', 'ECONNABORTED'])

const getStatusCode = (error) => Number(error?.response?.status || 0)

export const hasReachableBackendConfig = () => Boolean(getApiBaseUrl()) && !shouldUseMockApi()

export const isNetworkTransportError = (error) => {
  const code = String(error?.code || '').toUpperCase()
  const message = String(error?.message || '')
  if (NETWORK_ERROR_CODES.has(code)) return true
  if (!error?.response) return true
  return message.includes('Network Error') || message.includes('timeout')
}

export const isRetryableServerError = (error) => RETRYABLE_SERVER_STATUS.has(getStatusCode(error))

export const isBackendUnavailableError = (error) => {
  if (!hasReachableBackendConfig()) return false
  return isNetworkTransportError(error) || isRetryableServerError(error)
}

export const getBackendUnavailableMessage = (error, fallback = '后端暂时不可达') => {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) return detail.trim()
  const message = error?.response?.data?.message || error?.response?.data?.msg
  if (typeof message === 'string' && message.trim()) return message.trim()
  return error?.message || fallback
}
