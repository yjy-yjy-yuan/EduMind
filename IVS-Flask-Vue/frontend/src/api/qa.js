import request from '@/utils/request'

// 提问（支持视频问答和自由对话两种模式）
export function askQuestion(data) {
  return request({
    url: '/api/qa/ask',
    method: 'post',
    data
  })
}

// 获取视频问答历史
export function getQAHistory(videoId) {
  return request({
    url: `/api/qa/history/${videoId}`,
    method: 'get'
  })
}
