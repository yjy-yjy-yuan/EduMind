import { OFFLINE_MEMORY_LIMITS, OFFLINE_SYNC_STATUS, normalizeIsoTime, nowIso, offlineMemoryDb } from '@/services/offlineMemory/storage/db'
import { bulkDeleteByPrimaryKeys, deleteByVideoId, getAllRows, getCacheSize, getTable } from '@/services/offlineMemory/storage/repository'

const STALE_MS = OFFLINE_MEMORY_LIMITS.STALE_DAYS * 24 * 60 * 60 * 1000

const isSyncedRow = (row) => row?.sync_status !== OFFLINE_SYNC_STATUS.PENDING

const sortByLeastRecentlyUsed = (rows = []) =>
  [...rows].sort((left, right) => {
    const leftTime = new Date(left?.lastAccessedAt || left?.updated_at || 0).getTime()
    const rightTime = new Date(right?.lastAccessedAt || right?.updated_at || 0).getTime()
    return leftTime - rightTime
  })

const collectPendingVideoIds = async () => {
  const [notes, questions] = await Promise.all([
    getTable('offline_notes').where('sync_status').equals(OFFLINE_SYNC_STATUS.PENDING).toArray(),
    getTable('offline_questions').where('sync_status').equals(OFFLINE_SYNC_STATUS.PENDING).toArray()
  ])
  return new Set(
    [...notes, ...questions]
      .map((row) => Number(row?.video_id || 0))
      .filter((videoId) => Number.isInteger(videoId) && videoId > 0)
  )
}

const pruneRowsPerVideo = async (tableName, videoId, limit) => {
  const table = getTable(tableName)
  const rows = await table.where('video_id').equals(Number(videoId)).toArray()
  if (rows.length <= limit) return

  const protectedRows = rows.filter((row) => row.sync_status === OFFLINE_SYNC_STATUS.PENDING)
  const removableRows = sortByLeastRecentlyUsed(rows.filter((row) => row.sync_status !== OFFLINE_SYNC_STATUS.PENDING))
  const keepCount = Math.max(0, limit - protectedRows.length)
  const toDelete = removableRows.slice(0, Math.max(0, removableRows.length - keepCount))
  await bulkDeleteByPrimaryKeys(tableName, toDelete.map((row) => row.local_id))
}

const cleanupFreeModeRows = async (tableName, cutoffIso, { preservePending = true } = {}) => {
  const rows = await getAllRows(tableName)
  const cutoff = new Date(cutoffIso).getTime()
  const toDelete = rows
    .filter((row) => !row?.video_id)
    .filter((row) => {
      if (preservePending && row?.sync_status === OFFLINE_SYNC_STATUS.PENDING) return false
      const timestamp = new Date(row?.lastAccessedAt || row?.updated_at || 0).getTime()
      return Number.isFinite(timestamp) && timestamp > 0 && timestamp < cutoff
    })
    .map((row) => row.local_id)
  await bulkDeleteByPrimaryKeys(tableName, toDelete)
}

export const deleteCacheByVideoId = async (videoId, { preserveNotes = false, preservePending = false } = {}) => {
  const numericVideoId = Number(videoId)
  if (!Number.isInteger(numericVideoId) || numericVideoId <= 0) return

  await deleteByVideoId('offline_videos', numericVideoId)
  await deleteByVideoId('offline_learning_state', numericVideoId)
  await deleteByVideoId('offline_subtitles', numericVideoId)

  const questionRows = await getTable('offline_questions').where('video_id').equals(numericVideoId).toArray()
  const questionDeleteKeys = questionRows
    .filter((row) => !preservePending || row.sync_status !== OFFLINE_SYNC_STATUS.PENDING)
    .map((row) => row.local_id)
  await bulkDeleteByPrimaryKeys('offline_questions', questionDeleteKeys)

  if (!preserveNotes) {
    const noteRows = await getTable('offline_notes').where('video_id').equals(numericVideoId).toArray()
    const noteDeleteKeys = noteRows
      .filter((row) => !preservePending || row.sync_status !== OFFLINE_SYNC_STATUS.PENDING)
      .map((row) => row.local_id)
    await bulkDeleteByPrimaryKeys('offline_notes', noteDeleteKeys)
  }
}

export const clearCache = async () => {
  await Promise.all([
    getTable('offline_videos').clear(),
    getTable('offline_subtitles').clear(),
    getTable('offline_notes').clear(),
    getTable('offline_questions').clear(),
    getTable('offline_sync_queue').clear(),
    getTable('offline_learning_state').clear()
  ])
}

export const cleanupExpiredCache = async () => {
  const cutoffIso = new Date(Date.now() - STALE_MS).toISOString()
  const pendingVideoIds = await collectPendingVideoIds()
  const videos = await getAllRows('offline_videos')

  for (const videoRow of sortByLeastRecentlyUsed(videos)) {
    const videoId = Number(videoRow?.video_id || 0)
    const lastAccess = new Date(videoRow?.lastAccessedAt || videoRow?.updated_at || 0).getTime()
    if (!Number.isInteger(videoId) || videoId <= 0) continue
    if (pendingVideoIds.has(videoId)) continue
    if (!Number.isFinite(lastAccess) || lastAccess <= 0) continue
    if (lastAccess >= new Date(cutoffIso).getTime()) continue
    await deleteCacheByVideoId(videoId, { preserveNotes: false, preservePending: true })
  }

  await cleanupFreeModeRows('offline_notes', cutoffIso, { preservePending: true })
  await cleanupFreeModeRows('offline_questions', cutoffIso, { preservePending: true })

  const queueRows = await getAllRows('offline_sync_queue')
  const syncedQueueKeys = queueRows
    .filter((row) => row?.sync_status === OFFLINE_SYNC_STATUS.SYNCED)
    .filter((row) => {
      const timestamp = new Date(row?.updated_at || row?.created_at || 0).getTime()
      return Number.isFinite(timestamp) && timestamp > 0 && timestamp < new Date(cutoffIso).getTime()
    })
    .map((row) => row.local_id)
  await bulkDeleteByPrimaryKeys('offline_sync_queue', syncedQueueKeys)
}

export const enforcePerVideoItemLimits = async (videoId) => {
  await pruneRowsPerVideo('offline_notes', videoId, OFFLINE_MEMORY_LIMITS.MAX_NOTES_PER_VIDEO)
  await pruneRowsPerVideo('offline_questions', videoId, OFFLINE_MEMORY_LIMITS.MAX_QUESTIONS_PER_VIDEO)
}

export const enforceVideoLruLimit = async () => {
  const pendingVideoIds = await collectPendingVideoIds()
  const videos = await getAllRows('offline_videos')
  if (videos.length <= OFFLINE_MEMORY_LIMITS.MAX_VIDEOS) return

  const removableVideos = sortByLeastRecentlyUsed(videos)
    .filter((row) => Number(row?.video_id || 0) > 0)
    .filter((row) => !pendingVideoIds.has(Number(row.video_id)))

  while ((await getTable('offline_videos').count()) > OFFLINE_MEMORY_LIMITS.MAX_VIDEOS && removableVideos.length > 0) {
    const next = removableVideos.shift()
    await deleteCacheByVideoId(next.video_id, { preserveNotes: true, preservePending: true })
  }
}

export const cleanupByCacheSize = async ({ maxBytes = OFFLINE_MEMORY_LIMITS.MAX_CACHE_BYTES } = {}) => {
  let cacheState = await getCacheSize({ maxBytes })
  if (!cacheState.exceeded) return cacheState

  const pendingVideoIds = await collectPendingVideoIds()
  const videos = sortByLeastRecentlyUsed(await getAllRows('offline_videos'))
    .filter((row) => Number(row?.video_id || 0) > 0)
    .filter((row) => !pendingVideoIds.has(Number(row.video_id)))

  while (cacheState.exceeded && videos.length > 0) {
    const next = videos.shift()
    await deleteCacheByVideoId(next.video_id, { preserveNotes: true, preservePending: true })
    cacheState = await getCacheSize({ maxBytes })
  }

  if (!cacheState.exceeded) return cacheState

  const freeModeQuestions = sortByLeastRecentlyUsed(
    (await getAllRows('offline_questions')).filter((row) => !row?.video_id && isSyncedRow(row))
  )
  for (const row of freeModeQuestions) {
    if (!cacheState.exceeded) break
    await bulkDeleteByPrimaryKeys('offline_questions', [row.local_id])
    cacheState = await getCacheSize({ maxBytes })
  }

  return cacheState
}

let cleanupPromise = null

export const ensureOfflineCachePolicy = async ({ touchedVideoId = null } = {}) => {
  if (cleanupPromise) return cleanupPromise

  cleanupPromise = (async () => {
    await cleanupExpiredCache()
    if (touchedVideoId) {
      await enforcePerVideoItemLimits(touchedVideoId)
    }
    await enforceVideoLruLimit()
    return cleanupByCacheSize()
  })()

  try {
    return await cleanupPromise
  } finally {
    cleanupPromise = null
  }
}

export const touchRowsByVideoId = async (tableName, videoId, accessTime = nowIso()) => {
  const numericVideoId = Number(videoId)
  if (!Number.isInteger(numericVideoId) || numericVideoId <= 0) return
  const rows = await getTable(tableName).where('video_id').equals(numericVideoId).toArray()
  await Promise.all(
    rows.map((row) =>
      getTable(tableName).update(row.local_id, {
        lastAccessedAt: normalizeIsoTime(accessTime, nowIso())
      })
    )
  )
}

export const runInOfflineMemoryTransaction = async (runner) =>
  offlineMemoryDb.transaction(
    'rw',
    offlineMemoryDb.offline_videos,
    offlineMemoryDb.offline_subtitles,
    offlineMemoryDb.offline_notes,
    offlineMemoryDb.offline_questions,
    offlineMemoryDb.offline_sync_queue,
    offlineMemoryDb.offline_learning_state,
    runner
  )
