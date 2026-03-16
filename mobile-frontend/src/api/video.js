import request from '@/utils/request'
import { shouldUseMockApi } from '@/config'
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

export function processVideo(videoId, language = 'Other', model = 'base') {
  if (shouldUseMockApi()) return mockProcessVideo(videoId, language, model)
  return request({ url: `/api/videos/${videoId}/process`, method: 'post', data: { language, model } })
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
