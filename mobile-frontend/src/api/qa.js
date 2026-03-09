import request from '@/utils/request'

export function askQuestion({ question, video_id, mode = 'free', use_ollama = false, deep_thinking = false }) {
  return request({
    url: '/api/qa/ask',
    method: 'post',
    data: { question, video_id, mode, use_ollama, deep_thinking, stream: false }
  })
}

