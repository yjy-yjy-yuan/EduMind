import request from '@/utils/request'
import { shouldUseMockApi } from '@/config'
import { mockAskQuestion } from '@/api/mockGateway'

export function askQuestion({
  question,
  video_id,
  mode = 'free',
  provider = 'qwen',
  model = '',
  deep_thinking = false,
  history = []
}) {
  if (shouldUseMockApi()) {
    return mockAskQuestion({ question, video_id, mode, provider, model, deep_thinking, history, stream: false })
  }
  return request({
    url: '/api/qa/ask',
    method: 'post',
    data: { question, video_id, mode, provider, model, deep_thinking, history, stream: false }
  })
}
