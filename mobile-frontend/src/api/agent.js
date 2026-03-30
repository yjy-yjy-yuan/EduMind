import request from '@/utils/request'
import { shouldUseMockApi } from '@/config'

export function executeLearningFlowAgent(data) {
  if (shouldUseMockApi()) {
    const subtitle = String(data?.subtitle_text || '').trim()
    const userInput = String(data?.user_input || '').trim()
    return Promise.resolve({
      data: {
        intent: /笔记|记成/.test(userInput) ? 'create_note' : 'summarize',
        plan: ['读取视频上下文', '生成执行计划', '调用现有能力写回结果'],
        actions: ['summary_generated', 'note_created', 'timestamp_attached'],
        result: {
          note_id: 900001,
          title: 'UI 模式学习笔记',
          summary: subtitle ? subtitle.slice(0, 120) : 'UI 模式下未接入真实后端。'
        },
        created_at: new Date().toISOString(),
        action_records: []
      },
      status: 200
    })
  }

  return request({
    url: '/api/agent/execute',
    method: 'post',
    data
  })
}
