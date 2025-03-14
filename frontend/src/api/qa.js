import request from '@/utils/request'
import { API_BASE_URL } from '@/config'

// 提问（支持视频问答和自由对话两种模式）
export function askQuestion(data) {
  return request({
    url: '/api/qa/ask',
    method: 'post',
    data: {
      ...data,
      stream: false // 使用非流式响应
    }
  })
}

// 提问（流式响应）
export async function askQuestionStream(data, { onData, onError, onComplete }) {
  try {
    // 构建请求数据
    const requestData = {
      ...data,
      stream: true // 使用流式响应
    }
    
    // 发送请求
    const response = await fetch(`${API_BASE_URL}/api/qa/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestData),
      // 设置超时时间
      signal: AbortSignal.timeout(60000) // 60秒超时
    })
    
    if (!response.ok) {
      throw new Error(`请求失败: ${response.status}`)
    }
    
    // 处理流式响应
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        if (buffer.trim() && onData) {
          onData(buffer)
        }
        if (onComplete) {
          onComplete()
        }
        break
      }
      
      // 解码并处理数据
      const text = decoder.decode(value)
      buffer += text
      
      if (onData) {
        onData(buffer)
      }
    }
  } catch (error) {
    console.error('提问失败:', error)
    if (onError) {
      onError(error.message || '网络错误，请检查后端服务是否正常运行')
    }
  }
}

// 获取视频问答历史
export function getQAHistory(videoId) {
  return request({
    url: `/api/qa/history/${videoId}`,
    method: 'get'
  })
}
