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

const LOCAL_DELETED_VIDEO_IDS_KEY = 'm_deleted_video_ids'

export const hasLiveVideoBackend = () => hasReachableBackendConfig()
export const isVideoUploadQueueableError = (error) => isBackendUnavailableError(error)
export const getVideoUploadQueueableMessage = (error, fallback = '后端暂时不可达') =>
  getBackendUnavailableMessage(error, fallback)

const parseDeletedVideoIds = () => {
  try {
    const raw = localStorage.getItem(LOCAL_DELETED_VIDEO_IDS_KEY)
    const list = JSON.parse(raw || '[]')
    if (!Array.isArray(list)) return new Set()
    return new Set(list.map((item) => Number(item)).filter((item) => Number.isFinite(item) && item > 0))
  } catch {
    return new Set()
  }
}

const writeDeletedVideoIds = (idsSet) => {
  try {
    localStorage.setItem(LOCAL_DELETED_VIDEO_IDS_KEY, JSON.stringify([...idsSet]))
  } catch {
    // ignore storage failures
  }
}

const resolveVideoId = (video) => {
  const n = Number(video?.id ?? video?.video_id ?? video?.server_id ?? video?.local_id ?? 0)
  return Number.isFinite(n) && n > 0 ? Math.floor(n) : 0
}

export const markVideoDeletedLocally = (videoId) => {
  const id = Number(videoId)
  if (!Number.isFinite(id) || id <= 0) return
  const ids = parseDeletedVideoIds()
  ids.add(Math.floor(id))
  writeDeletedVideoIds(ids)
}

export const filterDeletedVideosLocally = (videos = []) => {
  const ids = parseDeletedVideoIds()
  if (ids.size === 0) return Array.isArray(videos) ? videos : []
  const list = Array.isArray(videos) ? videos : []
  return list.filter((video) => !ids.has(resolveVideoId(video)))
}

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

export async function deleteVideo(videoId) {
  if (shouldUseMockApi()) return mockDeleteVideo(videoId)

  try {
    return await request({ url: `/api/videos/${videoId}/delete`, method: 'delete' })
  } catch (error) {
    const status = Number(error?.response?.status || 0)
    if (status !== 404) throw error
  }

  try {
    return await request({ url: `/api/videos/${videoId}`, method: 'delete' })
  } catch (error) {
    const status = Number(error?.response?.status || 0)
    if (status !== 404) throw error
  }

  return request({ url: `/api/video/${videoId}/delete`, method: 'delete' })
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

export function syncOfflineTranscriptToVideo(data = {}) {
  void data
  return Promise.reject(new Error('离线转录同步能力已从当前项目移除'))
}

export function generateVideoTags(videoId, data = {}) {
  if (shouldUseMockApi()) return mockGenerateVideoTags(videoId, data)
  return request({ url: `/api/videos/${videoId}/generate-tags`, method: 'post', data, timeout: 120000, retry: 0 })
}
