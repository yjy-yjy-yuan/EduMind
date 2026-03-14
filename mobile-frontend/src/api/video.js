import request from '@/utils/request'
import { UI_ONLY_MODE } from '@/config'
import {
  mockDeleteVideo,
  mockGetVideo,
  mockGetVideoList,
  mockGetVideoStatus,
  mockProcessVideo,
  mockUploadLocalVideo,
  mockUploadVideoUrl
} from '@/api/mockGateway'

export function getVideoList(page = 1, pageSize = 10) {
  if (UI_ONLY_MODE) return mockGetVideoList(page, pageSize)
  return request({ url: '/api/videos/list', method: 'get', params: { page, per_page: pageSize } })
}

export function getVideo(videoId) {
  if (UI_ONLY_MODE) return mockGetVideo(videoId)
  return request({ url: `/api/videos/${videoId}`, method: 'get' })
}

export function getVideoStatus(videoId) {
  if (UI_ONLY_MODE) return mockGetVideoStatus(videoId)
  return request({ url: `/api/videos/${videoId}/status`, method: 'get' })
}

export function processVideo(videoId, language = 'Other', model = 'turbo') {
  if (UI_ONLY_MODE) return mockProcessVideo(videoId, language, model)
  return request({ url: `/api/videos/${videoId}/process`, method: 'post', data: { language, model } })
}

export function deleteVideo(videoId) {
  if (UI_ONLY_MODE) return mockDeleteVideo(videoId)
  return request({ url: `/api/videos/${videoId}/delete`, method: 'delete' })
}

export function uploadLocalVideo(formData, { onUploadProgress } = {}) {
  if (UI_ONLY_MODE) return mockUploadLocalVideo(formData, { onUploadProgress })
  return request({
    url: '/api/videos/upload',
    method: 'post',
    data: formData,
    onUploadProgress,
    timeout: 600000,
    retry: 0,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function uploadVideoUrl(data) {
  if (UI_ONLY_MODE) return mockUploadVideoUrl(data)
  return request({ url: '/api/videos/upload-url', method: 'post', data, timeout: 600000, retry: 0 })
}
