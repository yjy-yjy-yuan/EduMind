import request from '@/utils/request'

// 上传本地视频
export function uploadLocalVideo(data, onUploadProgress) {
  return request({
    url: '/api/videos/upload',
    method: 'post',
    data,
    onUploadProgress,
    timeout: 600000, // 10分钟超时
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 上传视频链接
export function uploadVideoUrl(data) {
  return request({
    url: '/api/videos/upload-url',
    method: 'post',
    data,
    timeout: 600000 // 10分钟超时，与本地视频上传保持一致
  })
}

// 获取视频信息
export const getVideoInfo = (videoId) => {
  return request({
    url: `/api/videos/${videoId}`,
    method: 'get'
  })
}

// 获取单个视频详情
export function getVideo(videoId) {
  return request({
    url: `/api/videos/${videoId}`,
    method: 'get'
  })
}

// 获取视频上传状态
export const getUploadStatus = (taskId) => {
  return request({
    url: `/api/videos/status/${taskId}`,
    method: 'get'
  })
}

// 获取视频预览
export const getVideoPreview = (videoId) => {
  return request({
    url: `/api/videos/${videoId}/preview`,
    method: 'get'
  })
}

// 获取视频字幕
export const getSubtitles = async (videoId) => {
  return request({
    url: `/api/video/${videoId}/subtitles`,
    method: 'get'
  })
}

// 更新视频字幕
export const updateSubtitle = async (videoId, subtitleId, data) => {
  return request({
    url: `/api/video/${videoId}/subtitles/${subtitleId}`,
    method: 'put',
    data
  })
}

// 导出视频字幕
export const exportSubtitles = async (videoId, format) => {
  return request({
    url: `/api/video/${videoId}/subtitles/export`,
    method: 'get',
    params: { format },
    responseType: 'blob'
  })
}

// 生成视频字幕
export const generateSubtitles = async (videoId, language = 'zh', model = 'base') => {
  return request({
    url: `/api/video/${videoId}/subtitles/generate`,
    method: 'post',
    data: {
      language,
      model
    }
  })
}

// 获取视频列表
export function getVideoList() {
  return request({
    url: '/api/videos/list',
    method: 'get'
  })
}

// 开始处理视频
export function processVideo(videoId) {
  return request({
    url: `/api/videos/${videoId}/process`,
    method: 'post'
  })
}

// 获取视频预览图
export function getVideoPreviewImage(videoId) {
  return request({
    url: `/api/videos/${videoId}/preview`,
    method: 'get',
    responseType: 'blob'
  })
}

// 删除视频
export function deleteVideo(videoId) {
  return request({
    url: `/api/videos/${videoId}/delete`,
    method: 'delete'
  })
}

// 获取视频状态
export function getVideoStatus(videoId) {
  return request({
    url: `/api/videos/${videoId}/status`,
    method: 'get'
  })
}
