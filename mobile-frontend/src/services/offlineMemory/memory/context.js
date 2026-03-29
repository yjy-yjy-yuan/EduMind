import { getOfflineNotes } from '@/services/offlineMemory/cache/noteCache'
import { getOfflineQuestions } from '@/services/offlineMemory/cache/questionCache'
import { getAllCachedSubtitles, getCachedLearningState, getCachedVideo, touchVideoAccess } from '@/services/offlineMemory/cache/videoCache'
import { OFFLINE_MEMORY_LIMITS, normalizeString } from '@/services/offlineMemory/storage/db'

const tokenizeText = (value) => {
  const text = normalizeString(value, 4000).toLowerCase()
  const tokenSet = new Set()
  const latinMatches = text.match(/[a-z0-9]{2,}/g) || []
  latinMatches.forEach((item) => tokenSet.add(item))

  const chineseMatches = text.match(/[\u4e00-\u9fa5]{2,}/g) || []
  chineseMatches.forEach((item) => {
    tokenSet.add(item)
    for (let size = 2; size <= Math.min(4, item.length); size += 1) {
      for (let index = 0; index <= item.length - size; index += 1) {
        tokenSet.add(item.slice(index, index + size))
      }
    }
  })

  return [...tokenSet]
}

const estimateTokensByChars = (text) => Math.ceil(String(text || '').length / 4)

const truncateByEstimatedTokens = (text, maxTokens) => {
  const content = String(text || '')
  const maxChars = Math.max(0, maxTokens * 4)
  if (content.length <= maxChars) return content
  return `${content.slice(0, maxChars)}…`
}

const sortRecent = (rows = []) =>
  [...rows].sort((left, right) => {
    const leftTime = new Date(left?.lastAccessedAt || left?.updated_at || 0).getTime()
    const rightTime = new Date(right?.lastAccessedAt || right?.updated_at || 0).getTime()
    return rightTime - leftTime
  })

const buildSubtitleOrdering = (subtitles = [], learningState = null) => {
  const currentPosition = Number(learningState?.current_position_seconds || NaN)
  const rows = subtitles.map((fragment) => ({
    ...fragment,
    _distance:
      Number.isFinite(currentPosition)
        ? Math.abs(((Number(fragment.start_time || 0) + Number(fragment.end_time || fragment.start_time || 0)) / 2) - currentPosition)
        : Number.POSITIVE_INFINITY
  }))

  return rows
    .sort((left, right) => {
      if (left._distance !== right._distance) return left._distance - right._distance
      return Number(right.start_time || 0) - Number(left.start_time || 0)
    })
    .slice(0, 24)
    .sort((left, right) => Number(left.start_time || 0) - Number(right.start_time || 0))
}

const compactReferencePreview = (value, maxLength = 80) => {
  const text = normalizeString(value, 400).replace(/\s+/g, ' ')
  if (text.length <= maxLength) return text
  return `${text.slice(0, maxLength)}…`
}

export const buildVideoMemoryContext = async (videoId = null) => {
  const numericVideoId = videoId == null || videoId === '' ? null : Number(videoId)
  const [video, learningState, notes, questions, subtitles] = await Promise.all([
    numericVideoId ? getCachedVideo(numericVideoId) : null,
    numericVideoId ? getCachedLearningState(numericVideoId) : null,
    getOfflineNotes({ videoId: numericVideoId || null }),
    getOfflineQuestions({
      videoId: numericVideoId || null,
      limit: OFFLINE_MEMORY_LIMITS.MAX_QUESTIONS_PER_VIDEO
    }),
    numericVideoId ? getAllCachedSubtitles(numericVideoId) : []
  ])

  if (numericVideoId) {
    await touchVideoAccess(numericVideoId)
  }

  const orderedNotes = sortRecent(notes).slice(0, 12)
  const orderedQuestions = sortRecent(questions).slice(0, 10)
  const orderedSubtitles = buildSubtitleOrdering(subtitles, learningState)

  return {
    video_id: numericVideoId,
    summary: normalizeString(video?.summary, OFFLINE_MEMORY_LIMITS.MAX_SUMMARY_CHARS),
    tags: Array.isArray(video?.tags) ? video.tags : [],
    subtitles: orderedSubtitles,
    notes: orderedNotes,
    questions: orderedQuestions,
    learning_state:
      learningState ||
      (video
        ? {
            status: video.status,
            last_viewed_at: video.lastAccessedAt || video.updated_at || ''
          }
        : null),
    video
  }
}

const appendBlockWithinBudget = (parts, text, budgetChars) => {
  if (!text) return budgetChars
  if (budgetChars <= 0) return 0
  const next = text.length <= budgetChars ? text : `${text.slice(0, budgetChars)}…`
  if (!next.trim()) return budgetChars
  parts.push(next)
  return Math.max(0, budgetChars - next.length - 2)
}

export const formatMemoryPrompt = (context, question, { maxChars = OFFLINE_MEMORY_LIMITS.MAX_CONTEXT_CHARS } = {}) => {
  const parts = []
  let remaining = maxChars

  remaining = appendBlockWithinBudget(parts, `问题：${normalizeString(question, OFFLINE_MEMORY_LIMITS.MAX_QUESTION_CHARS)}`, remaining)

  if (context?.summary) {
    remaining = appendBlockWithinBudget(parts, `摘要：${context.summary}`, remaining)
  }

  if (Array.isArray(context?.tags) && context.tags.length > 0) {
    remaining = appendBlockWithinBudget(parts, `标签：${context.tags.join('、')}`, remaining)
  }

  sortRecent(context?.notes || []).forEach((note) => {
    if (remaining <= 0) return
    const block = `笔记：${normalizeString(note.title, 120)}\n${truncateByEstimatedTokens(note.content, 220)}`
    remaining = appendBlockWithinBudget(parts, block, remaining)
  })

  sortRecent(context?.questions || []).forEach((item) => {
    if (remaining <= 0) return
    const block = `最近问答：Q ${item.question}\nA ${truncateByEstimatedTokens(item.answer, 180)}`
    remaining = appendBlockWithinBudget(parts, block, remaining)
  })

  ;(context?.subtitles || []).forEach((item) => {
    if (remaining <= 0) return
    const timeRange = `[${Number(item.start_time || 0).toFixed(1)}-${Number(item.end_time || item.start_time || 0).toFixed(1)}]`
    remaining = appendBlockWithinBudget(parts, `字幕 ${timeRange} ${item.text}`, remaining)
  })

  return {
    text: parts.join('\n\n'),
    estimated_tokens: estimateTokensByChars(parts.join('\n\n'))
  }
}

const buildCandidateSources = (context) => {
  const sources = []

  if (context?.summary) {
    sources.push({
      source_type: 'summary',
      label: '视频摘要',
      preview: compactReferencePreview(context.summary),
      rawText: context.summary,
      time_range: ''
    })
  }

  ;(context?.notes || []).forEach((note) => {
    sources.push({
      source_type: 'note',
      label: note.title || '本地笔记',
      preview: compactReferencePreview(note.content),
      rawText: `${note.title || ''} ${note.content || ''}`,
      time_range: Array.isArray(note.timestamps) && note.timestamps[0]
        ? `${Number(note.timestamps[0].time_seconds || 0).toFixed(1)}s`
        : ''
    })
  })

  ;(context?.questions || []).forEach((item) => {
    sources.push({
      source_type: 'qa',
      label: `最近问答: ${item.question || '问题'}`,
      preview: compactReferencePreview(item.answer),
      rawText: `${item.question || ''} ${item.answer || ''}`,
      time_range: ''
    })
  })

  ;(context?.subtitles || []).forEach((item) => {
    sources.push({
      source_type: 'subtitle',
      label: item.title || '字幕片段',
      preview: compactReferencePreview(item.text),
      rawText: item.text || '',
      time_range: `${Number(item.start_time || 0).toFixed(1)}s-${Number(item.end_time || item.start_time || 0).toFixed(1)}s`
    })
  })

  return sources
}

const scoreCandidate = (candidate, tokens = [], index = 0) => {
  const haystack = String(candidate.rawText || '').toLowerCase()
  let score = 0
  tokens.forEach((token) => {
    if (haystack.includes(token)) {
      score += token.length
    }
  })
  if (candidate.source_type === 'summary') score += 2
  if (candidate.source_type === 'note') score += 4
  if (candidate.source_type === 'subtitle') score += 3
  return score - index * 0.01
}

export const answerOfflineFromContext = (context, question, { topK = 3 } = {}) => {
  const tokens = tokenizeText(question)
  const candidates = buildCandidateSources(context)
    .map((candidate, index) => ({
      ...candidate,
      score: scoreCandidate(candidate, tokens, index)
    }))
    .filter((candidate) => candidate.score > 0)
    .sort((left, right) => right.score - left.score)
    .slice(0, topK)
    .map((candidate, index) => ({
      index: index + 1,
      source_type: candidate.source_type,
      label: candidate.label,
      time_range: candidate.time_range,
      preview: candidate.preview,
      rawText: candidate.rawText
    }))

  if (candidates.length === 0) {
    return {
      answer:
        '当前处于离线状态，本地缓存里没有足够的摘要、字幕或笔记可以支撑这个问题。建议先在联网状态下打开视频详情页缓存内容后再离线提问。',
      references: []
    }
  }

  const answerLines = [
    '离线检索结果基于本地缓存整理：',
    ...candidates.map((item) => `[${item.index}] ${truncateByEstimatedTokens(item.rawText, 120)}`)
  ]

  return {
    answer: answerLines.join('\n'),
    references: candidates.map(({ rawText, ...rest }) => rest)
  }
}
