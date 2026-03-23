import request from '@/utils/request'
import { shouldUseMockApi } from '@/config'
import { getBackendUnavailableMessage, hasReachableBackendConfig, isBackendUnavailableError } from '@/services/networkStatus'
import {
  mockDeleteVideo,
  mockGenerateVideoSummary,
  mockGenerateVideoTags,
  mockGetVideo,
  mockGetVideoList,
  mockGetVideoStatus,
  mockProcessVideo,
  mockUploadLocalVideo,
  mockUploadVideoUrl
} from '@/api/mockGateway'

export const hasLiveVideoBackend = () => hasReachableBackendConfig()
export const isVideoUploadQueueableError = (error) => isBackendUnavailableError(error)
export const getVideoUploadQueueableMessage = (error, fallback = '后端暂时不可达') =>
  getBackendUnavailableMessage(error, fallback)

export function getVideoList(page = 1, pageSize = 10) {
  if (shouldUseMockApi()) return mockGetVideoList(page, pageSize)
  return request({ url: '/api/videos/list', method: 'get', params: { page, per_page: pageSize } })
}

export function getVideo(videoId) {
  if (shouldUseMockApi()) return mockGetVideo(videoId)
  return request({ url: `/api/videos/${videoId}`, method: 'get' })
}

export function getVideoStatus(videoId) {
  if (shouldUseMockApi()) return mockGetVideoStatus(videoId)
  return request({ url: `/api/videos/${videoId}/status`, method: 'get' })
}

export function getVideoProcessingOptions() {
  if (shouldUseMockApi()) {
    return Promise.resolve({
      data: {
        default_model: 'base',
        models: []
      },
      status: 200
    })
  }
  return request({ url: '/api/videos/processing-options', method: 'get' })
}

export function processVideo(videoId, options = {}) {
  if (shouldUseMockApi()) return mockProcessVideo(videoId, options)
  return request({ url: `/api/videos/${videoId}/process`, method: 'post', data: options })
}

export function deleteVideo(videoId) {
  if (shouldUseMockApi()) return mockDeleteVideo(videoId)
  return request({ url: `/api/videos/${videoId}/delete`, method: 'delete' })
}

export function uploadLocalVideo(formData, { onUploadProgress } = {}) {
  if (shouldUseMockApi()) return mockUploadLocalVideo(formData, { onUploadProgress })
  return request({
    url: '/api/videos/upload',
    method: 'post',
    data: formData,
    onUploadProgress,
    timeout: 600000,
    retry: 0
  })
}

export function uploadVideoUrl(data) {
  if (shouldUseMockApi()) return mockUploadVideoUrl(data)
  return request({ url: '/api/videos/upload-url', method: 'post', data, timeout: 600000, retry: 0 })
}

export function generateVideoSummary(videoId, data = {}) {
  if (shouldUseMockApi()) return mockGenerateVideoSummary(videoId, data)
  return request({ url: `/api/videos/${videoId}/generate-summary`, method: 'post', data, timeout: 120000, retry: 0 })
}

export function generateTranscriptSummary(data = {}) {
  if (shouldUseMockApi()) {
    const source = String(data?.transcript_text || '').trim()
    const trimmed = source.replace(/\s+/g, ' ')
    const preview = trimmed.slice(0, 120)
    return Promise.resolve({
      data: {
        success: true,
        style: String(data?.style || 'study'),
        provider: 'mock',
        summary: preview ? `UI 模式摘要：${preview}${trimmed.length > preview.length ? '…' : ''}` : 'UI 模式摘要：当前转录文本为空。'
      },
      status: 200
    })
  }
  return request({
    url: '/api/videos/generate-summary-from-transcript',
    method: 'post',
    data,
    timeout: 120000,
    retry: 0
  })
}

export function generateVideoTags(videoId, data = {}) {
  if (shouldUseMockApi()) return mockGenerateVideoTags(videoId, data)
  return request({ url: `/api/videos/${videoId}/generate-tags`, method: 'post', data, timeout: 120000, retry: 0 })
}
