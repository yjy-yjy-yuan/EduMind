import request from '@/utils/request'
import { UI_ONLY_MODE } from '@/config'
import { mockAskQuestion } from '@/api/mockGateway'

export function askQuestion({ question, video_id, mode = 'free', use_ollama = false, deep_thinking = false }) {
  if (UI_ONLY_MODE) {
    return mockAskQuestion({ question, video_id, mode, use_ollama, deep_thinking, stream: false })
  }
  return request({
    url: '/api/qa/ask',
    method: 'post',
    data: { question, video_id, mode, use_ollama, deep_thinking, stream: false }
  })
}
