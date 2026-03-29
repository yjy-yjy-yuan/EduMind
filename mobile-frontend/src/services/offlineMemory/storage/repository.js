import { OFFLINE_MEMORY_LIMITS, estimateSizeInBytes, normalizeIsoTime, nowIso, offlineMemoryDb } from '@/services/offlineMemory/storage/db'

export const OFFLINE_MEMORY_TABLES = Object.freeze([
  'offline_videos',
  'offline_subtitles',
  'offline_notes',
  'offline_questions',
  'offline_sync_queue',
  'offline_learning_state'
])

export const getTable = (tableName) => offlineMemoryDb.table(tableName)

export const getAllRows = async (tableName) => getTable(tableName).toArray()

export const getCacheSize = async ({ maxBytes = OFFLINE_MEMORY_LIMITS.MAX_CACHE_BYTES } = {}) => {
  const entries = await Promise.all(
    OFFLINE_MEMORY_TABLES.map(async (tableName) => {
      const rows = await getAllRows(tableName)
      return {
        table: tableName,
        rowCount: rows.length,
        bytes: rows.reduce((total, row) => total + estimateSizeInBytes(row), 0)
      }
    })
  )

  const bytes = entries.reduce((total, item) => total + item.bytes, 0)
  return {
    bytes,
    limitBytes: maxBytes,
    exceeded: bytes > maxBytes,
    tables: entries
  }
}

export const findExistingRecord = async (tableName, { localId = null, serverId = null, composite = null } = {}) => {
  const table = getTable(tableName)

  if (localId) {
    const current = await table.get(String(localId))
    if (current) return current
  }

  if (serverId != null && serverId !== '') {
    const current = await table.where('server_id').equals(String(serverId)).first()
    if (current) return current
  }

  if (composite?.index && Array.isArray(composite.value)) {
    return table.where(composite.index).equals(composite.value).first()
  }

  return null
}

export const upsertRecord = async (tableName, nextRecord, { composite = null } = {}) => {
  const existing = await findExistingRecord(tableName, {
    localId: nextRecord?.local_id,
    serverId: nextRecord?.server_id,
    composite
  })
  const merged = {
    ...existing,
    ...nextRecord,
    local_id: existing?.local_id || nextRecord.local_id,
    updated_at: normalizeIsoTime(nextRecord?.updated_at || existing?.updated_at || nowIso(), nowIso()),
    lastAccessedAt: normalizeIsoTime(
      nextRecord?.lastAccessedAt || existing?.lastAccessedAt || nextRecord?.updated_at || nowIso(),
      nowIso()
    )
  }
  await getTable(tableName).put(merged)
  return merged
}

export const bulkDeleteByPrimaryKeys = async (tableName, keys = []) => {
  const normalized = keys.filter(Boolean)
  if (normalized.length === 0) return
  await getTable(tableName).bulkDelete(normalized)
}

export const deleteByVideoId = async (tableName, videoId) => {
  if (videoId == null) return
  await getTable(tableName).where('video_id').equals(Number(videoId)).delete()
}

export const purgeOlderThan = async (tableName, fieldName, cutoffIso, { syncStatus } = {}) => {
  const table = getTable(tableName)
  const rows = await table.toArray()
  const cutoff = new Date(cutoffIso).getTime()
  const keys = rows
    .filter((row) => {
      if (syncStatus && row?.sync_status !== syncStatus) return false
      const value = new Date(row?.[fieldName] || 0).getTime()
      return Number.isFinite(value) && value > 0 && value < cutoff
    })
    .map((row) => row.local_id)
  await bulkDeleteByPrimaryKeys(tableName, keys)
}
