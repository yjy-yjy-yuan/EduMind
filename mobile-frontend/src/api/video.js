import request from '@/utils/request'

export function getVideoList(page = 1, pageSize = 10) {
  return request({ url: '/api/videos/list', method: 'get', params: { page, per_page: pageSize } })
}

export function getVideo(videoId) {
  return request({ url: `/api/videos/${videoId}`, method: 'get' })
}

export function getVideoStatus(videoId) {
  return request({ url: `/api/videos/${videoId}/status`, method: 'get' })
}

export function processVideo(videoId, language = 'Other', model = 'turbo') {
  return request({ url: `/api/videos/${videoId}/process`, method: 'post', data: { language, model } })
}

export function deleteVideo(videoId) {
  return request({ url: `/api/videos/${videoId}/delete`, method: 'delete' })
}

export function uploadLocalVideo(formData, { onUploadProgress } = {}) {
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
  return request({ url: '/api/videos/upload-url', method: 'post', data, timeout: 600000, retry: 0 })
}
