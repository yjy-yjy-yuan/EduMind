/**
 * 聊天API
 * 提供以下功能：
 * 1. 发送问题并获取回答
 * 2. 获取聊天历史
 * 3. 清空聊天历史
 * 4. 支持两种问答模式：基于视频内容的RAG问答和自由问答
 */

import { API_BASE_URL } from '@/config'

/**
 * 发送聊天消息并获取回答
 * @param {string} message - 用户消息
 * @param {string} mode - 问答模式，'free'为自由问答，'video'为基于视频内容的问答
 * @param {string} videoId - 视频ID（仅在视频问答模式下需要）
 * @param {function} onData - 处理流式数据的回调函数
 * @param {function} onError - 处理错误的回调函数
 * @param {function} onComplete - 完成时的回调函数
 */
export async function sendChatMessage(message, { mode = 'free', videoId = null, onData, onError, onComplete }) {
  try {
    // 构建请求数据
    const requestData = {
      message: message,
      mode: mode
    }
    
    // 如果是视频问答模式，添加视频ID
    if (mode === 'video' && videoId) {
      requestData.videoId = videoId
    }
    
    // 发送请求
    const response = await fetch(`${API_BASE_URL}/api/chat/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestData),
      // 设置超时时间
      signal: AbortSignal.timeout(30000) // 30秒超时
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
    console.error('发送聊天消息出错:', error)
    if (onError) {
      onError(error.message || '网络错误，请检查后端服务是否正常运行')
    }
  }
}

/**
 * 获取聊天历史
 * @param {string} mode - 问答模式，'free'为自由问答，'video'为基于视频内容的问答
 * @returns {Promise<Array>} 聊天历史数组
 */
export async function getChatHistory(mode = 'free') {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/history?mode=${mode}`, {
      // 设置超时时间
      signal: AbortSignal.timeout(10000) // 10秒超时
    })
    
    if (!response.ok) {
      throw new Error(`请求失败: ${response.status}`)
    }
    
    const data = await response.json()
    return data.history || []
  } catch (error) {
    console.error('获取聊天历史出错:', error)
    // 返回空数组，让调用方处理
    return []
  }
}

/**
 * 清空聊天历史
 * @param {string} mode - 问答模式，可选值：'free'（自由问答）或 'video'（基于视频内容）
 * @returns {Promise<boolean>} 是否成功
 */
export async function clearChatHistory(mode = 'free') {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/clear`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ mode }),
      // 设置超时时间
      signal: AbortSignal.timeout(10000) // 10秒超时
    })
    
    if (!response.ok) {
      throw new Error(`请求失败: ${response.status}`)
    }
    
    return true
  } catch (error) {
    console.error('清空聊天历史出错:', error)
    throw error
  }
}
