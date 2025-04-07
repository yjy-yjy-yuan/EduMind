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
  console.log('发送请求数据:', JSON.stringify(data))
  
  try {
    // 创建一个普通的JavaScript对象，避免响应式对象可能导致的循环引用问题
    const requestData = {
      question: data.question,
      video_id: data.video_id,
      api_key: data.api_key || 'sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', // 使用阿里云API密钥
      mode: data.mode,
      use_ollama: data.use_ollama,
      deep_thinking: data.deep_thinking
    }
    
    console.log('请求参数:', requestData)
    console.log('use_ollama的值和类型:', requestData.use_ollama, typeof requestData.use_ollama)
    console.log('deep_thinking的值和类型:', requestData.deep_thinking, typeof requestData.deep_thinking)
    
    // 确保use_ollama是布尔值
    if (typeof requestData.use_ollama === 'string') {
      requestData.use_ollama = requestData.use_ollama.toLowerCase() === 'true'
    } else {
      requestData.use_ollama = Boolean(requestData.use_ollama)
    }
    
    // 确保deep_thinking是布尔值
    if (typeof requestData.deep_thinking === 'string') {
      requestData.deep_thinking = requestData.deep_thinking.toLowerCase() === 'true'
    } else {
      requestData.deep_thinking = Boolean(requestData.deep_thinking)
    }
    
    console.log('处理后的use_ollama:', requestData.use_ollama, typeof requestData.use_ollama)
    console.log('处理后的deep_thinking:', requestData.deep_thinking, typeof requestData.deep_thinking)
    
    // 使用正确的API基础URL
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '';
    console.log('使用的API基础URL:', apiBaseUrl);
    
    const response = await fetch(`${apiBaseUrl}/api/qa/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestData),
      signal: AbortSignal.timeout(60000) // 60秒超时
    })
    
    console.log('收到流式响应:', response.status);
    
    if (!response.ok) {
      throw new Error(`HTTP错误! 状态: ${response.status}`);
    }
    
    // 处理流式响应
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    
    console.log('开始读取流式响应')
    
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        console.log('流式响应读取完成，最终内容长度:', buffer.length)
        if (buffer.trim() && onData) {
          onData(buffer)
        } else if (buffer.trim() === '' && onData) {
          // 如果收到空响应，显示错误信息
          console.error('收到空响应')
          onData('无法获取回答，请检查Ollama服务是否正常运行，或尝试使用在线模式。')
        }
        if (onComplete) {
          onComplete()
        }
        break
      }
      
      // 解码二进制数据
      const chunk = decoder.decode(value, { stream: true })
      console.log('收到数据块:', chunk ? chunk.substring(0, 50) + '...' : '空数据')
      
      if (chunk) {
        // 检查是否包含思考过程的标记
        const hasThinkTag = chunk.includes('<think>') || chunk.includes('</think>')
        
        // 将新数据添加到缓冲区
        buffer += chunk
        
        // 如果是深度思考模式，尝试提取和格式化思考过程
        if (requestData.deep_thinking && hasThinkTag) {
          // 提取所有思考过程
          const thinkMatches = buffer.match(/<think>(.*?)<\/think>/gs)
          if (thinkMatches) {
            // 提取思考内容
            const thinkingProcess = thinkMatches
              .map(match => match.replace(/<think>|<\/think>/g, '').trim())
              .join('\n\n')
            
            // 创建实时更新的格式化答案
            const formattedAnswer = `<div class="thinking-process">
<p><strong>🧠 思考中...</strong></p>
<p>${thinkingProcess}</p>
</div>`
            
            if (onData) {
              onData(formattedAnswer)
            }
          } else {
            // 如果没有找到思考标签但有内容，直接显示
            if (onData) {
              onData(buffer)
            }
          }
        } else {
          // 非深度思考模式或没有思考标签，直接显示内容
          if (onData) {
            onData(buffer)
          }
        }
      }
    }
  } catch (error) {
    console.error('请求出错:', error)
    if (onError) {
      onError(error.message || '请求失败')
    }
    if (onComplete) {
      onComplete()
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
