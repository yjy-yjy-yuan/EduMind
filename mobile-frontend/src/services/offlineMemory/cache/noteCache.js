import {
  OFFLINE_ENTITY_TYPE,
  OFFLINE_MEMORY_LIMITS,
  OFFLINE_SYNC_STATUS,
  createBaseRecord,
  createLocalId,
  normalizeIntegerId,
  normalizeIsoTime,
  normalizeNumber,
  normalizeString,
  nowIso,
  uniqueTextList
} from '@/services/offlineMemory/storage/db'
import { ensureOfflineCachePolicy } from '@/services/offlineMemory/cache/policies'
import { findExistingRecord, getTable, upsertRecord } from '@/services/offlineMemory/storage/repository'
import { cacheLearningState, touchVideoAccess } from '@/services/offlineMemory/cache/videoCache'

const normalizeTimestamps = (timestamps = []) =>
  (Array.isArray(timestamps) ? timestamps : [])
    .map((item, index) => ({
      id: item?.id == null ? null : Number(item.id),
      time_seconds: Math.max(0, normalizeNumber(item?.time_seconds, 0)),
      subtitle_text: normalizeString(item?.subtitle_text, 255),
      created_at: normalizeIsoTime(item?.created_at, nowIso()),
      order: index
    }))
    .sort((left, right) => left.time_seconds - right.time_seconds)

const buildNoteRecord = (input = {}, existing = null) => {
  const prior = existing ?? {}
  const serverId = input.server_id || input.id || prior.server_id || null
  const updatedAt = input.updated_at || input.created_at || prior.updated_at || nowIso()
  return createBaseRecord({
    local_id: prior.local_id || input.local_id || createLocalId('offline-note'),
    server_id: serverId,
    updated_at: updatedAt,
    sync_status: input.sync_status || prior.sync_status || OFFLINE_SYNC_STATUS.SYNCED,
    lastAccessedAt: input.lastAccessedAt || prior.lastAccessedAt || updatedAt,
    entity_type: OFFLINE_ENTITY_TYPE.NOTE,
    video_id: normalizeIntegerId(input.video_id ?? prior.video_id),
    title: normalizeString(input.title ?? prior.title, 255),
    content: normalizeString(input.content ?? prior.content, 12000),
    note_type: normalizeString(input.note_type ?? prior.note_type ?? 'text', 32) || 'text',
    tags: uniqueTextList(input.tags ?? prior.tags),
    timestamps: normalizeTimestamps(input.timestamps ?? prior.timestamps),
    video_title: normalizeString(input.video_title ?? prior.video_title, 255)
  })
}

const mapNoteForUi = (note) => ({
  ...note,
  id: note?.server_id || note?.local_id || '',
  tags: Array.isArray(note?.tags) ? note.tags : [],
  timestamps: Array.isArray(note?.timestamps) ? note.timestamps : []
})

export const cacheNoteRecord = async (noteInput, { syncStatus = OFFLINE_SYNC_STATUS.SYNCED } = {}) => {
  const existing = await findExistingRecord('offline_notes', {
    localId: noteInput?.local_id,
    serverId: noteInput?.server_id || noteInput?.id
  })
  const record = buildNoteRecord(
    {
      ...noteInput,
      sync_status: syncStatus
    },
    existing
  )
  const saved = await upsertRecord('offline_notes', record)
  if (saved.video_id) {
    await touchVideoAccess(saved.video_id)
    await cacheLearningState(saved.video_id, {
      last_note_at: saved.updated_at
    })
    await ensureOfflineCachePolicy({ touchedVideoId: saved.video_id })
  }
  return saved
}

export const cacheNotes = async (notes = [], { syncStatus = OFFLINE_SYNC_STATUS.SYNCED } = {}) => {
  const saved = []
  for (const note of notes) {
    if (!note) continue
    saved.push(await cacheNoteRecord(note, { syncStatus }))
  }
  return saved
}

export const getOfflineNoteByIdentifier = async (identifier) => {
  if (!identifier) return null
  const text = String(identifier)
  const byLocalId = await getTable('offline_notes').get(text)
  if (byLocalId) return mapNoteForUi(byLocalId)
  const byServerId = await getTable('offline_notes').where('server_id').equals(text).first()
  return byServerId ? mapNoteForUi(byServerId) : null
}

export const getOfflineNotes = async ({ videoId = null, search = '', tag = '' } = {}) => {
  let rows = await getTable('offline_notes').toArray()
  if (videoId) {
    rows = rows.filter((row) => Number(row.video_id || 0) === Number(videoId))
  }
  if (search) {
    const keyword = String(search).trim().toLowerCase()
    rows = rows.filter((row) =>
      `${row.title || ''} ${row.content || ''} ${(row.tags || []).join(' ')}`
        .toLowerCase()
        .includes(keyword)
    )
  }
  if (tag) {
    rows = rows.filter((row) => Array.isArray(row.tags) && row.tags.includes(tag))
  }
  return rows
    .filter(Boolean)
    .sort((left, right) => new Date(right?.updated_at || 0) - new Date(left?.updated_at || 0))
    .map((row) => mapNoteForUi(row))
}

export const getOfflineNoteTags = async () => {
  const rows = await getTable('offline_notes').toArray()
  const buckets = new Map()
  rows.filter(Boolean).forEach((row) => {
    ;(Array.isArray(row.tags) ? row.tags : []).forEach((tagName) => {
      buckets.set(tagName, (buckets.get(tagName) || 0) + 1)
    })
  })
  return [...buckets.entries()]
    .sort((left, right) => right[1] - left[1])
    .map(([name, count]) => ({ name, count }))
}

export const buildNotePayloadForSync = (note) => ({
  title: normalizeString(note?.title, 255),
  content: normalizeString(note?.content, 12000),
  note_type: normalizeString(note?.note_type || 'text', 32) || 'text',
  video_id: normalizeIntegerId(note?.video_id),
  tags: uniqueTextList(note?.tags).join(','),
  timestamps: normalizeTimestamps(note?.timestamps)
})

export const markOfflineNoteFailed = async (localId, errorMessage) => {
  if (!localId) return null
  await getTable('offline_notes').update(String(localId), {
    sync_status: OFFLINE_SYNC_STATUS.FAILED,
    sync_error: normalizeString(errorMessage, 500),
    updated_at: nowIso()
  })
  return getTable('offline_notes').get(String(localId))
}
