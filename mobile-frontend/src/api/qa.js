import request from '@/utils/request'
import { withBase, shouldUseMockApi } from '@/config'
import { storageGet } from '@/utils/storage'
import { mockAskQuestion } from '@/api/mockGateway'

export function askQuestion({
  user_id,
  question,
  video_id,
  mode = 'free',
  chat_mode = 'direct',
  model = '',
  history = []
}) {
  if (shouldUseMockApi()) {
    return mockAskQuestion({ user_id, question, video_id, mode, chat_mode, model, history, stream: false })
  }
  return request({
    url: '/api/qa/ask',
    method: 'post',
    data: { user_id, question, video_id, mode, chat_mode, model, history, stream: false }
  })
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const toStreamError = (detail, status = 0) => {
  const message = String(detail || '请求失败，请稍后再试。')
  const error = new Error(message)
  error.response = {
    status,
    data: { detail: message }
  }
  return error
}

const parseStreamErrorBody = async (response) => {
  const text = await response.text()
  if (!text) return `请求失败（HTTP ${response.status}）`
  try {
    const payload = JSON.parse(text)
    const detail = payload?.message || payload?.detail || payload?.msg
    return typeof detail === 'string' && detail.trim() ? detail.trim() : text
  } catch {
    return text
  }
}

const resolveProviderAndThinking = (chatMode) => {
  if (chatMode === 'deep_think') {
    return { provider: 'deepseek', deep_thinking: true }
  }
  return { provider: 'qwen', deep_thinking: false }
}

const dispatchMockStream = async (payload, onEvent) => {
  const { provider, deep_thinking } = resolveProviderAndThinking(payload.chat_mode || 'direct')
  const providerText = provider === 'deepseek' ? 'DeepSeek' : '通义千问'
  const modelText = provider === 'deepseek'
    ? (deep_thinking ? 'deepseek-reasoner' : 'deepseek-chat')
    : (payload.model || 'qwen-plus')
  const answerText = (await mockAskQuestion(payload)).data?.answer || '【UI 模式】暂无回答。'
  const isDeepThink = provider === 'deepseek' && deep_thinking

  const events = [
    { type: 'status', stage: 'accepted', message: '问题已提交，等待处理', progress: 5 },
    {
      type: 'status',
      stage: payload.mode === 'video' ? 'retrieving' : 'answering',
      message: payload.mode === 'video' ? '正在检索视频字幕、摘要与标签' : `正在调用 ${providerText} 回答`,
      progress: payload.mode === 'video' ? 25 : 45,
      provider,
      provider_label: providerText,
      model: modelText
    }
  ]

  if (isDeepThink) {
    events.push(
      {
        type: 'status',
        stage: 'reasoning',
        message: '正在深度思考...',
        progress: 50,
        provider,
        provider_label: providerText,
        model: modelText
      }
    )

    const thinkingChunks = [
      '首先，我需要仔细分析这个问题涉及的各个方面...\n',
      '让我回顾一下视频中提到的核心概念：\n',
      '  1. 理解问题的本质诉求\n',
      '  2. 对照视频内容寻找相关证据\n',
      '  3. 综合分析形成逻辑链\n',
      '基于以上分析，我可以看出这是一个涉及多个知识点的综合问题...\n',
      '现在让我进一步推理，得出最终结论。'
    ]

    for (const chunk of thinkingChunks) {
      events.push({
        type: 'thinking',
        stage: 'streaming',
        thinking: chunk,
        delta: chunk,
        progress: 52,
        provider,
        provider_label: providerText,
        model: modelText
      })
    }

    events.push({
      type: 'thinking_complete',
      stage: 'completed',
      thinking: thinkingChunks.join(''),
      progress: 65,
      provider,
      provider_label: providerText,
      model: modelText
    })
  }

  events.push(
    {
      type: 'status',
      stage: 'organizing',
      message: '正在整理回答与引用片段',
      progress: isDeepThink ? 80 : 85,
      provider,
      provider_label: providerText,
      model: modelText
    },
    {
      type: 'answer',
      stage: 'completed',
      message: '回答已完成',
      progress: 100,
      answer: answerText,
      provider,
      provider_label: providerText,
      model: modelText,
      references: []
    }
  )

  let finalEvent = null
  for (const event of events) {
    onEvent?.(event)
    finalEvent = event
    await sleep(event.type === 'answer' ? 0 : event.type === 'thinking' ? 280 : 220)
  }
  return finalEvent
}

export async function askQuestionStream(
  { user_id, question, video_id, mode = 'free', chat_mode = 'direct', model = '', history = [] },
  { onEvent } = {}
) {
  const payload = { user_id, question, video_id, mode, chat_mode, model, history, stream: true }

  if (shouldUseMockApi()) {
    return dispatchMockStream(payload, onEvent)
  }

  const headers = { 'Content-Type': 'application/json', Accept: 'application/x-ndjson' }
  const token = storageGet('m_token')
  if (token) headers.Authorization = `Bearer ${token}`

  const response = await fetch(withBase('/api/qa/ask'), {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
    credentials: 'include'
  })

  if (!response.ok) {
    throw toStreamError(await parseStreamErrorBody(response), response.status)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw toStreamError('当前环境不支持问答进度流，请稍后重试。', response.status)
  }

  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  let finalEvent = null

  const handleLine = (line) => {
    if (!line) return

    let event = null
    try {
      event = JSON.parse(line)
    } catch {
      return
    }

    onEvent?.(event)
    if (event?.type === 'error') {
      const detail = event.message || event.detail || '问答处理失败，请稍后重试。'
      throw toStreamError(detail, response.status)
    }
    if (event?.type === 'answer') {
      finalEvent = event
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done })

    let newlineIndex = buffer.indexOf('\n')
    while (newlineIndex >= 0) {
      const line = buffer.slice(0, newlineIndex).trim()
      buffer = buffer.slice(newlineIndex + 1)
      handleLine(line)
      newlineIndex = buffer.indexOf('\n')
    }

    if (done) break
  }

  const rest = `${buffer}${decoder.decode()}`.trim()
  if (rest) handleLine(rest)

  if (!finalEvent) {
    throw toStreamError('问答进度流已结束，但未收到最终回答。', response.status)
  }

  return finalEvent
}

export function getQuestionHistory({ user_id, video_id, mode = 'video' }) {
  if (shouldUseMockApi()) {
    return Promise.resolve({
      data: {
        message: 'UI 模式历史为空',
        total: 0,
        questions: [],
        messages: []
      },
      status: 200,
      headers: { 'x-edumind-ui-only': 'true' }
    })
  }

  return request({
    url: `/api/qa/history/${video_id}`,
    method: 'get',
    params: { user_id, mode }
  })
}
