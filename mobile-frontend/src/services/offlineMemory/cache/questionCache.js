import {
  OFFLINE_ENTITY_TYPE,
  OFFLINE_MEMORY_LIMITS,
  OFFLINE_SYNC_STATUS,
  createBaseRecord,
  createLocalId,
  normalizeIntegerId,
  normalizeString,
  nowIso
} from '@/services/offlineMemory/storage/db'
import { ensureOfflineCachePolicy } from '@/services/offlineMemory/cache/policies'
import { findExistingRecord, getTable, upsertRecord } from '@/services/offlineMemory/storage/repository'
import { cacheLearningState, touchVideoAccess } from '@/services/offlineMemory/cache/videoCache'

const MAX_THINKING = OFFLINE_MEMORY_LIMITS.MAX_THINKING_CHARS

const parseTimeRangeStartSeconds = (timeRange = '') => {
  const start = String(timeRange || '')
    .split('-')[0]
    .trim()
  if (!start) return Number.POSITIVE_INFINITY

  const parts = start.split(':').map((part) => Number(part))
  if (parts.some((part) => Number.isNaN(part) || part < 0)) return Number.POSITIVE_INFINITY
  if (parts.length === 2) return parts[0] * 60 + parts[1]
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2]
  return Number.POSITIVE_INFINITY
}

const applySubtitleTimeOrder = (references = []) => {
  const subtitles = references.filter((item) => item?.source_type === 'subtitle')
  if (subtitles.length === 0) return references

  const orderedSubtitles = subtitles
    .slice()
    .sort((left, right) => {
      const startDiff = parseTimeRangeStartSeconds(left?.time_range) - parseTimeRangeStartSeconds(right?.time_range)
      if (startDiff !== 0) return startDiff
      return Number(left?.index || 0) - Number(right?.index || 0)
    })

  const subtitleOrderMap = new Map()
  orderedSubtitles.forEach((item, index) => {
    subtitleOrderMap.set(item, index + 1)
  })

  return references.map((item) =>
    item?.source_type === 'subtitle'
      ? {
          ...item,
          time_order: subtitleOrderMap.get(item) || null
        }
      : item
  )
}

const normalizeReferences = (references = []) =>
  applySubtitleTimeOrder(
    (Array.isArray(references) ? references : [])
      .map((item, index) => ({
        index: Number(item?.index || index + 1),
        label: normalizeString(item?.label, 120),
        preview: normalizeString(item?.preview, 240),
        time_range: normalizeString(item?.time_range, 40),
        source_type: normalizeString(item?.source_type, 40),
        time_order: typeof item?.time_order === 'number' ? Number(item.time_order) : null
      }))
      .filter((item) => item.preview)
  )

const buildQuestionRecord = (input = {}, existing = null) => {
  const prior = existing ?? {}
  const updatedAt = input.updated_at || input.created_at || prior.updated_at || nowIso()
  const serverId = input.server_id || input.id || prior.server_id || null
  return createBaseRecord({
    local_id: prior.local_id || input.local_id || createLocalId('offline-question'),
    server_id: serverId,
    updated_at: updatedAt,
    sync_status: input.sync_status || prior.sync_status || OFFLINE_SYNC_STATUS.SYNCED,
    lastAccessedAt: input.lastAccessedAt || prior.lastAccessedAt || updatedAt,
    entity_type: OFFLINE_ENTITY_TYPE.QUESTION,
    video_id: normalizeIntegerId(input.video_id ?? prior.video_id),
    user_id: normalizeIntegerId(input.user_id ?? prior.user_id),
    mode: normalizeString(input.mode ?? prior.mode ?? 'video', 16) || 'video',
    chat_mode: normalizeString(input.chat_mode ?? prior.chat_mode ?? 'direct', 16) || 'direct',
    provider: normalizeString(input.provider ?? prior.provider ?? 'qwen', 32) || 'qwen',
    model: normalizeString(input.model ?? prior.model, 64),
    question: normalizeString(input.question ?? input.content ?? prior.question, OFFLINE_MEMORY_LIMITS.MAX_QUESTION_CHARS),
    answer: normalizeString(input.answer ?? prior.answer, OFFLINE_MEMORY_LIMITS.MAX_ANSWER_CHARS),
    thinking: normalizeString(input.thinking ?? prior.thinking, MAX_THINKING),
    references: normalizeReferences(input.references ?? prior.references),
    source: normalizeString(input.source ?? prior.source ?? 'online', 32),
    deep_thinking: Boolean(input.deep_thinking ?? prior.deep_thinking),
    history: Array.isArray(input.history) ? input.history : Array.isArray(prior.history) ? prior.history : []
  })
}

const mapQuestionToMessagePair = (item) => ([
  {
    role: 'user',
    text: item.question || ''
  },
  {
    role: 'ai',
    text: item.answer || '',
    thinking: item.thinking || '',
    providerLabel: item.source === 'offline' ? '离线记忆' : '',
    model: item.model || '',
    references: Array.isArray(item.references) ? item.references : []
  }
])

export const cacheQuestionRecord = async (questionInput, { syncStatus = OFFLINE_SYNC_STATUS.SYNCED } = {}) => {
  if (!questionInput) return null
  const existing = await findExistingRecord('offline_questions', {
    localId: questionInput?.local_id,
    serverId: questionInput?.server_id || questionInput?.id
  })
  const record = buildQuestionRecord(
    {
      ...questionInput,
      sync_status: syncStatus
    },
    existing
  )
  const saved = await upsertRecord('offline_questions', record)
  if (saved.video_id) {
    await touchVideoAccess(saved.video_id)
    await cacheLearningState(saved.video_id, {
      last_question_at: saved.updated_at
    })
    await ensureOfflineCachePolicy({ touchedVideoId: saved.video_id })
  }
  return saved
}

export const getOfflineQuestions = async ({
  videoId = null,
  mode = '',
  chatMode = '',
  userId = null,
  limit = OFFLINE_MEMORY_LIMITS.MAX_QUESTIONS_PER_VIDEO
} = {}) => {
  const questionTable = getTable('offline_questions')
  let rows = await questionTable.toArray()
  const backfillQueue = []

  rows = rows.map((row) => {
    if (!row) return row
    const normalizedRefs = normalizeReferences(row.references)
    const originalRefs = Array.isArray(row.references) ? row.references : []
    const changed = JSON.stringify(originalRefs) !== JSON.stringify(normalizedRefs)
    if (changed && row.local_id) {
      backfillQueue.push({
        localId: String(row.local_id),
        references: normalizedRefs
      })
    }
    return {
      ...row,
      references: normalizedRefs
    }
  })

  if (backfillQueue.length > 0) {
    await Promise.all(backfillQueue.map((item) => questionTable.update(item.localId, { references: item.references })))
  }

  if (videoId != null) {
    rows = rows.filter((row) => Number(row.video_id || 0) === Number(videoId))
  }
  if (mode) {
    rows = rows.filter((row) => row.mode === mode)
  }
  if (chatMode) {
    rows = rows.filter((row) => row.chat_mode === chatMode)
  }
  if (userId != null) {
    rows = rows.filter((row) => Number(row.user_id || 0) === Number(userId))
  }
  return rows
    .filter(Boolean)
    .sort(
      (left, right) =>
        new Date(right?.lastAccessedAt || right?.updated_at || 0) - new Date(left?.lastAccessedAt || left?.updated_at || 0)
    )
    .slice(0, limit)
}

export const getOfflineQaMessages = async (scope = {}) => {
  const rows = await getOfflineQuestions(scope)
  return rows
    .slice()
    .reverse()
    .flatMap((row) => mapQuestionToMessagePair(row))
}

export const buildQuestionPayloadForSync = (question) => ({
  user_id: question?.user_id || null,
  video_id: question?.video_id || null,
  question: question?.question || '',
  mode: question?.mode || 'video',
  chat_mode: question?.chat_mode || 'direct',
  model: question?.model || '',
  history: Array.isArray(question?.history) ? question.history : []
})

export const markOfflineQuestionFailed = async (localId, errorMessage) => {
  if (!localId) return null
  await getTable('offline_questions').update(String(localId), {
    sync_status: OFFLINE_SYNC_STATUS.FAILED,
    sync_error: normalizeString(errorMessage, 500),
    updated_at: nowIso()
  })
  return getTable('offline_questions').get(String(localId))
}
