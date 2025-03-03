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
    timeout: 600000 // 10分钟超时
  })
}

// 获取视频详情
export function getVideo(videoId) {
  return request({
    url: `/api/videos/${videoId}`,
    method: 'get'
  })
}

// 获取视频状态
export function getVideoStatus(videoId) {
  return request({
    url: `/api/videos/${videoId}/status`,
    method: 'get'
  })
}

// 获取视频预览图
export function getVideoPreview(videoId) {
  return request({
    url: `/api/videos/${videoId}/preview`,
    method: 'get',
    responseType: 'blob'
  })
}

// 获取视频字幕
export async function getSubtitle(videoId, format = 'srt', isDownload = false) {
  const params = { format }
  if (isDownload) {
    params.download = 'true'
  }
  
  return await request({
    url: `/api/videos/${videoId}/subtitle`,
    method: 'get',
    params,
    responseType: 'blob'
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
export function processVideo(videoId, language = 'Other', model = 'turbo') {
  return request({
    url: `/api/videos/${videoId}/process`,
    method: 'post',
    data: {
      language,
      model
    }
  })
}

// 删除视频
export function deleteVideo(videoId) {
  return request({
    url: `/api/videos/${videoId}/delete`,
    method: 'delete'
  })
}
