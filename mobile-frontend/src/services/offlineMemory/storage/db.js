import Dexie from 'dexie'

export const OFFLINE_MEMORY_DB_NAME = 'edumind_offline_memory'

export const OFFLINE_SYNC_STATUS = Object.freeze({
  SYNCED: 'synced',
  PENDING: 'pending',
  FAILED: 'failed'
})

export const OFFLINE_ENTITY_TYPE = Object.freeze({
  VIDEO: 'video',
  SUBTITLE: 'subtitle',
  NOTE: 'note',
  QUESTION: 'question',
  LEARNING_STATE: 'learning_state',
  SYNC_QUEUE: 'sync_queue'
})

export const OFFLINE_MEMORY_LIMITS = Object.freeze({
  MAX_VIDEOS: 30,
  MAX_NOTES_PER_VIDEO: 50,
  MAX_QUESTIONS_PER_VIDEO: 20,
  MAX_SUBTITLE_SEGMENTS_PER_VIDEO: 200,
  SUBTITLE_PAGE_SIZE: 40,
  MAX_SUBTITLE_TEXT_CHARS: 240,
  MAX_SUMMARY_CHARS: 4000,
  MAX_TAGS: 12,
  MAX_QUESTION_CHARS: 2000,
  MAX_ANSWER_CHARS: 6000,
  MAX_CONTEXT_CHARS: 9000,
  MAX_CACHE_BYTES: 100 * 1024 * 1024,
  STALE_DAYS: 30
})

class EduMindOfflineMemoryDB extends Dexie {
  constructor() {
    super(OFFLINE_MEMORY_DB_NAME)

    this.version(1).stores({
      offline_videos:
        '&local_id, server_id, video_id, updated_at, sync_status, lastAccessedAt, status, [video_id+updated_at]',
      offline_subtitles:
        '&local_id, server_id, video_id, page, updated_at, sync_status, lastAccessedAt, [video_id+page], [video_id+updated_at]',
      offline_notes:
        '&local_id, server_id, video_id, updated_at, sync_status, lastAccessedAt, note_type, [video_id+updated_at], [video_id+sync_status]',
      offline_questions:
        '&local_id, server_id, video_id, updated_at, sync_status, lastAccessedAt, mode, provider, user_id, [video_id+updated_at], [video_id+provider], [mode+provider]',
      offline_sync_queue:
        '&local_id, server_id, entity_local_id, entity_type, action, updated_at, sync_status, created_at, run_after, [entity_type+entity_local_id], [sync_status+updated_at]',
      offline_learning_state:
        '&local_id, server_id, video_id, updated_at, sync_status, lastAccessedAt, [video_id+updated_at]'
    })
  }
}

export const offlineMemoryDb = new EduMindOfflineMemoryDB()

const encoder = typeof TextEncoder !== 'undefined' ? new TextEncoder() : null

const randomSuffix = () => Math.random().toString(36).slice(2, 10)

export const nowIso = () => new Date().toISOString()

export const normalizeIsoTime = (value, fallback = nowIso()) => {
  if (!value) return fallback
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? fallback : date.toISOString()
}

export const clamp = (value, min, max) => Math.max(min, Math.min(max, value))

export const createLocalId = (prefix = 'local') => {
  const cryptoApi = typeof globalThis !== 'undefined' ? globalThis.crypto : undefined
  if (cryptoApi?.randomUUID) {
    return `${prefix}-${cryptoApi.randomUUID()}`
  }
  return `${prefix}-${Date.now()}-${randomSuffix()}-${randomSuffix()}`
}

export const normalizeSyncStatus = (value) => {
  const normalized = String(value || '').trim().toLowerCase()
  return Object.values(OFFLINE_SYNC_STATUS).includes(normalized)
    ? normalized
    : OFFLINE_SYNC_STATUS.SYNCED
}

export const normalizeNumber = (value, fallback = 0) => {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : fallback
}

export const normalizeOptionalNumber = (value) => {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : null
}

export const normalizeIntegerId = (value) => {
  const numeric = Number(value)
  return Number.isInteger(numeric) && numeric > 0 ? numeric : null
}

export const normalizeString = (value, maxLength = 0) => {
  const normalized = String(value || '').trim()
  if (!maxLength || normalized.length <= maxLength) return normalized
  return normalized.slice(0, maxLength)
}

export const ensureArray = (value) => (Array.isArray(value) ? value : [])

export const uniqueTextList = (value, maxLength = 32) => {
  const seen = new Set()
  const source = Array.isArray(value) ? value : String(value || '').split(',')
  return source
    .map((item) => normalizeString(item, maxLength))
    .filter((item) => {
      if (!item || seen.has(item)) return false
      seen.add(item)
      return true
    })
}

export const estimateSizeInBytes = (value) => {
  const serialized = JSON.stringify(value ?? null)
  if (!encoder) return serialized.length
  return encoder.encode(serialized).length
}

export const cloneJson = (value) => JSON.parse(JSON.stringify(value ?? null))

export const createBaseRecord = ({
  local_id,
  server_id = null,
  updated_at,
  sync_status = OFFLINE_SYNC_STATUS.SYNCED,
  lastAccessedAt,
  ...rest
} = {}) => {
  const timestamp = normalizeIsoTime(updated_at, nowIso())
  return {
    local_id: local_id || createLocalId('offline'),
    server_id: server_id == null || server_id === '' ? null : String(server_id),
    updated_at: timestamp,
    sync_status: normalizeSyncStatus(sync_status),
    lastAccessedAt: normalizeIsoTime(lastAccessedAt, timestamp),
    ...rest
  }
}
