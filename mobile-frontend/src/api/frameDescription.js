/**
 * 实时画面描述 API 客户端
 * 协议：NDJSON 流式响应
 * 事件类型：
 *   - status: 阶段状态变化
 *   - description: 描述文本增量
 *   - complete: 本次采样周期完成
 *   - error: 错误
 */

import { withBase, shouldUseMockApi } from '@/config'
import { storageGet } from '@/utils/storage'

const toStreamError = (detail, status) => {
  const message = String(detail || '请求失败，请稍后重试。')
  const error = new Error(message)
  error.response = { status: status || 0, data: { detail: message } }
  return error
}

const parseStreamErrorBody = async (response) => {
  const text = await response.text()
  if (!text) return '请求失败（HTTP ' + response.status + '）'
  try {
    const payload = JSON.parse(text)
    const detail = payload?.message || payload?.detail || payload?.msg
    return typeof detail === 'string' && detail.trim() ? detail.trim() : text
  } catch {
    return text
  }
}

/**
 * 发送画面描述流请求
 * @param {Object} params
 * @param {number} params.video_id
 * @param {string[]} params.frames
 * @param {number} params.timestamp
 * @param {string} [params.video_title]
 * @param {'brief'|'standard'|'detailed'} [params.detail_level='standard']
 * @param {string} [params.session_id]
 * @param {string[]} [params.context_history]
 * @param {boolean} [params.allow_degrade=true]
 * @param {Object} [options]
 * @param {Function} [options.onEvent]
 * @param {AbortSignal} [options.signal]
 */
export async function describeFrameStream(params, options) {
  const {
    video_id,
    frames,
    timestamp,
    video_title,
    detail_level,
    session_id,
    context_history,
    allow_degrade,
  } = params || {}
  const { onEvent, signal } = options || {}

  if (shouldUseMockApi()) {
    return dispatchMockStream({ video_id, frames, timestamp, video_title, detail_level, session_id }, onEvent)
  }

  const payload = {
    video_id,
    frames,
    timestamp,
    video_title: video_title || '',
    detail_level: detail_level || 'standard',
    session_id: session_id || '',
    context_history: context_history || [],
    allow_degrade: allow_degrade !== false,
  }

  const headers = { 'Content-Type': 'application/json', Accept: 'application/x-ndjson' }
  const token = storageGet('m_token')
  if (token) headers.Authorization = 'Bearer ' + token

  const response = await fetch(withBase('/api/frame_description/describe'), {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
    credentials: 'include',
    signal,
  })

  if (!response.ok) {
    throw toStreamError(await parseStreamErrorBody(response), response.status)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw toStreamError('当前环境不支持流式响应', response.status)
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
    if (!event) return
    if (onEvent) onEvent(event)
    if (event?.type === 'error') {
      const detail = event.message || event.detail || '画面描述失败'
      throw toStreamError(detail, response.status)
    }
    if (event?.type === 'complete') {
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

  const rest = (buffer + decoder.decode()).trim()
  if (rest) handleLine(rest)

  return finalEvent
}

/**
 * 管理描述会话（开启/关闭）
 */
export async function manageFrameDescSession(params) {
  const { video_id, action, detail_level, session_id } = params || {}

  if (shouldUseMockApi()) {
    return {
      session_id: session_id || 'mock-session-' + Date.now(),
      status: action === 'start' ? 'active' : 'stopped',
      message: action === 'start' ? '实时描述会话已开启' : '实时描述会话已关闭',
      detail_level: detail_level || 'standard',
    }
  }

  const headers = { 'Content-Type': 'application/json' }
  const token = storageGet('m_token')
  if (token) headers.Authorization = 'Bearer ' + token

  const response = await fetch(withBase('/api/frame_description/session'), {
    method: 'POST',
    headers,
    body: JSON.stringify({ video_id, action, detail_level: detail_level || 'standard', session_id: session_id || '' }),
    credentials: 'include',
  })

  if (!response.ok) {
    const text = await response.text()
    let detail = text
    try {
      const payload = JSON.parse(text)
      detail = payload?.detail || payload?.message || text
    } catch {
      // ignore
    }
    throw new Error(detail || ('请求失败（HTTP ' + response.status + '）'))
  }

  return response.json()
}

/**
 * 查询描述服务健康状态
 */
export async function getFrameDescHealth() {
  if (shouldUseMockApi()) {
    return { enabled: false, service: 'mock', description: 'UI 模拟模式' }
  }

  const response = await fetch(withBase('/api/frame_description/health'), {
    method: 'GET',
    credentials: 'include',
  })
  if (!response.ok) {
    return { enabled: false, service: 'unavailable', description: '服务不可用' }
  }
  return response.json()
}

// ----------------------------------------------------------------------
// Mock 流模拟（UI 模式）
// ----------------------------------------------------------------------

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const formatSeconds = (seconds) => {
  const total = Math.max(0, Math.round(Number(seconds || 0)))
  const mm = Math.floor((total % 3600) / 60)
  const ss = total % 60
  return String(mm).padStart(2, '0') + ':' + String(ss).padStart(2, '0')
}

async function dispatchMockStream(payload, onEvent) {
  const ts = payload.timestamp || 0
  const level = payload.detail_level || 'standard'
  const timeStr = formatSeconds(ts)

  const mockDescriptions = {
    brief: [
      '老师在黑板上书写公式',
      '画面展示例题演示',
      '老师指向屏幕图表',
      '继续推导下一个步骤',
    ],
    standard: [
      '画面中老师正在黑板前书写数学公式，当前时间 ' + timeStr,
      '镜头切换到投影屏幕，显示本节课的例题',
      '老师正在用手指指向屏幕上的图表进行讲解',
      '老师继续在黑板上进行公式推导，当前 ' + timeStr,
    ],
    detailed: [
      '当前画面为教室场景，老师站在黑板前，使用白色粉笔书写公式，时间 ' + timeStr,
      '投影屏幕上显示 PPT 内容，主题为本次课程的例题演示',
      '老师面向学生，一边讲解一边用教鞭指向屏幕上的关键图表',
      '教室后排可见部分学生正在做笔记，老师仍在继续推导公式，当前 ' + timeStr,
    ],
  }

  const descriptions = mockDescriptions[level] || mockDescriptions.standard
  const selected = descriptions[Math.floor(Math.random() * descriptions.length)]

  const events = [
    { type: 'status', stage: 'connecting', message: '正在连接画面描述服务', progress: 5 },
    { type: 'status', stage: 'inferring', message: '正在推理画面内容', progress: 25 },
  ]

  for (const event of events) {
    if (onEvent) onEvent(event)
    await sleep(220)
  }

  if (onEvent) {
    onEvent({ type: 'description', delta: selected, timestamp: ts, confidence: 0.85 })
  }
  await sleep(280)

  if (onEvent) {
    onEvent({
      type: 'complete',
      stage: 'completed',
      full_description: selected,
      timestamp: ts,
      confidence: 0.85,
      context_summary: selected,
      degraded: false,
      latency_ms: Math.round(200 + Math.random() * 300),
      progress: 100,
      message: '描述已完成',
    })
  }

  return { type: 'complete', full_description: selected }
}
