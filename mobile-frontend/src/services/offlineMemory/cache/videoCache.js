import {
  OFFLINE_ENTITY_TYPE,
  OFFLINE_MEMORY_LIMITS,
  OFFLINE_SYNC_STATUS,
  clamp,
  createBaseRecord,
  createLocalId,
  normalizeIntegerId,
  normalizeIsoTime,
  normalizeNumber,
  normalizeOptionalNumber,
  normalizeString,
  nowIso,
  uniqueTextList
} from '@/services/offlineMemory/storage/db'
import { ensureOfflineCachePolicy, touchRowsByVideoId } from '@/services/offlineMemory/cache/policies'
import { findExistingRecord, getTable, upsertRecord } from '@/services/offlineMemory/storage/repository'

const normalizeSubtitleFragment = (fragment = {}, index = 0) => {
  const startTime = normalizeNumber(fragment.start_time, 0)
  const endTime = normalizeNumber(fragment.end_time, startTime)
  return {
    index: Number.isInteger(Number(fragment.id)) ? Number(fragment.id) : index + 1,
    server_id: fragment?.id == null ? null : String(fragment.id),
    start_time: startTime,
    end_time: endTime >= startTime ? endTime : startTime,
    title: normalizeString(fragment?.title, 80),
    language: normalizeString(fragment?.language, 12),
    text: normalizeString(fragment?.text, OFFLINE_MEMORY_LIMITS.MAX_SUBTITLE_TEXT_CHARS)
  }
}

const splitSubtitlePages = (segments = [], pageSize = OFFLINE_MEMORY_LIMITS.SUBTITLE_PAGE_SIZE) => {
  const pages = []
  for (let index = 0; index < segments.length; index += pageSize) {
    pages.push(segments.slice(index, index + pageSize))
  }
  return pages
}

const normalizeVideoRecord = (input = {}, existing = null) => {
  const prior = existing ?? {}
  const videoId = normalizeIntegerId(input.video_id ?? input.id ?? prior.video_id)
  const summary = normalizeString(input.summary ?? prior.summary, OFFLINE_MEMORY_LIMITS.MAX_SUMMARY_CHARS)
  return createBaseRecord({
    local_id: prior.local_id || input.local_id || createLocalId('offline-video'),
    server_id: input.server_id || input.id || prior.server_id || (videoId ? String(videoId) : null),
    updated_at: input.updated_at || input.created_at || prior.updated_at || nowIso(),
    sync_status: input.sync_status || prior.sync_status || OFFLINE_SYNC_STATUS.SYNCED,
    lastAccessedAt: input.lastAccessedAt || prior.lastAccessedAt || nowIso(),
    entity_type: OFFLINE_ENTITY_TYPE.VIDEO,
    video_id: videoId,
    title: normalizeString(input.title ?? prior.title, 255),
    status: normalizeString(input.status ?? prior.status, 64),
    summary,
    tags: uniqueTextList(input.tags ?? prior.tags).slice(0, OFFLINE_MEMORY_LIMITS.MAX_TAGS),
    subtitle_page_count: Number(prior.subtitle_page_count || input.subtitle_page_count || 0),
    subtitle_segment_count: Number(prior.subtitle_segment_count || input.subtitle_segment_count || 0),
    metadata: {
      processing_origin: normalizeString(input.processing_origin ?? prior.metadata?.processing_origin, 64),
      requested_model: normalizeString(input.requested_model ?? prior.metadata?.requested_model, 64),
      effective_model: normalizeString(input.effective_model ?? prior.metadata?.effective_model, 64),
      filepath: normalizeString(input.filepath ?? prior.metadata?.filepath, 512)
    }
  })
}

export const cacheVideoMetadata = async (video) => {
  const videoId = normalizeIntegerId(video?.video_id ?? video?.id)
  const existing = await findExistingRecord('offline_videos', {
    localId: video?.local_id,
    serverId: video?.server_id || video?.id
  })
  const cached = await upsertRecord('offline_videos', normalizeVideoRecord(video, existing))
  if (videoId) {
    await cacheLearningState(videoId, {
      status: cached.status
    })
    await ensureOfflineCachePolicy({ touchedVideoId: videoId })
  }
  return cached
}

export const cacheVideoList = async (videos = []) => {
  const saved = []
  for (const item of videos) {
    saved.push(await cacheVideoMetadata(item))
  }
  return saved
}

export const cacheVideoSubtitles = async (
  videoId,
  fragments = [],
  { pageSize = OFFLINE_MEMORY_LIMITS.SUBTITLE_PAGE_SIZE } = {}
) => {
  const numericVideoId = normalizeIntegerId(videoId)
  if (!numericVideoId) return []

  const normalizedFragments = fragments
    .map((fragment, index) => normalizeSubtitleFragment(fragment, index))
    .filter((fragment) => fragment.text)
    .slice(0, OFFLINE_MEMORY_LIMITS.MAX_SUBTITLE_SEGMENTS_PER_VIDEO)

  const pageChunks = splitSubtitlePages(normalizedFragments, pageSize)
  const subtitleTable = getTable('offline_subtitles')
  const previousPages = await subtitleTable.where('video_id').equals(numericVideoId).toArray()
  const nextPageLocalIds = []

  for (let pageIndex = 0; pageIndex < pageChunks.length; pageIndex += 1) {
    const page = pageIndex + 1
    const localId = `offline-subtitles-${numericVideoId}-${page}`
    nextPageLocalIds.push(localId)
    await upsertRecord(
      'offline_subtitles',
      createBaseRecord({
        local_id: localId,
        server_id: `${numericVideoId}:${page}`,
        updated_at: nowIso(),
        sync_status: OFFLINE_SYNC_STATUS.SYNCED,
        entity_type: OFFLINE_ENTITY_TYPE.SUBTITLE,
        video_id: numericVideoId,
        page,
        page_size: pageSize,
        has_more: pageIndex < pageChunks.length - 1,
        fragment_count: pageChunks[pageIndex].length,
        fragments: pageChunks[pageIndex]
      }),
      {
        composite: {
          index: '[video_id+page]',
          value: [numericVideoId, page]
        }
      }
    )
  }

  const stalePageIds = previousPages
    .filter((row) => !nextPageLocalIds.includes(row.local_id))
    .map((row) => row.local_id)
  if (stalePageIds.length > 0) {
    await subtitleTable.bulkDelete(stalePageIds)
  }

  await cacheVideoMetadata({
    id: numericVideoId,
    subtitle_page_count: pageChunks.length,
    subtitle_segment_count: normalizedFragments.length
  })
  await touchVideoAccess(numericVideoId)
  await ensureOfflineCachePolicy({ touchedVideoId: numericVideoId })
  return pageChunks
}

export const getCachedVideo = async (videoId) => {
  const numericVideoId = normalizeIntegerId(videoId)
  if (!numericVideoId) return null
  const video = await getTable('offline_videos').where('video_id').equals(numericVideoId).first()
  if (video) {
    await touchVideoAccess(numericVideoId)
  }
  return video || null
}

export const getCachedVideoOptions = async () => {
  const rows = await getTable('offline_videos').toArray()
  return rows
    .filter((row) => Number(row?.video_id || 0) > 0)
    .sort(
      (left, right) =>
        new Date(right?.lastAccessedAt || right?.updated_at || 0) - new Date(left?.lastAccessedAt || left?.updated_at || 0)
    )
    .map((row) => ({
      id: row.video_id,
      title: row.title || `视频 ${row.video_id}`,
      status: row.status
    }))
}

export const getCachedSubtitlePage = async (videoId, page = 1) => {
  const numericVideoId = normalizeIntegerId(videoId)
  if (!numericVideoId) return null
  const row = await getTable('offline_subtitles').where('[video_id+page]').equals([numericVideoId, Number(page)]).first()
  if (row) {
    await touchVideoAccess(numericVideoId)
  }
  return row || null
}

export const getAllCachedSubtitles = async (videoId) => {
  const numericVideoId = normalizeIntegerId(videoId)
  if (!numericVideoId) return []
  const pages = await getTable('offline_subtitles').where('video_id').equals(numericVideoId).sortBy('page')
  if (pages.length > 0) {
    await touchVideoAccess(numericVideoId)
  }
  return pages.flatMap((page) => Array.isArray(page.fragments) ? page.fragments : [])
}

export const cacheLearningState = async (videoId, patch = {}) => {
  const numericVideoId = normalizeIntegerId(videoId)
  if (!numericVideoId) return null

  const current = await getTable('offline_learning_state').where('video_id').equals(numericVideoId).first()
  const baseUpdatedAt = patch.updated_at || nowIso()
  const next = createBaseRecord({
    local_id: current?.local_id || `offline-learning-state-${numericVideoId}`,
    server_id: current?.server_id || patch?.server_id || String(numericVideoId),
    updated_at: baseUpdatedAt,
    sync_status: patch.sync_status || current?.sync_status || OFFLINE_SYNC_STATUS.SYNCED,
    lastAccessedAt: patch.lastAccessedAt || baseUpdatedAt,
    entity_type: OFFLINE_ENTITY_TYPE.LEARNING_STATE,
    video_id: numericVideoId,
    current_position_seconds: normalizeOptionalNumber(
      patch.current_position_seconds ?? current?.current_position_seconds
    ),
    progress_percent: clamp(normalizeNumber(patch.progress_percent ?? current?.progress_percent, 0), 0, 100),
    last_viewed_at: normalizeIsoTime(patch.last_viewed_at || current?.last_viewed_at || baseUpdatedAt, baseUpdatedAt),
    last_note_at: normalizeIsoTime(patch.last_note_at || current?.last_note_at || baseUpdatedAt, baseUpdatedAt),
    last_question_at: normalizeIsoTime(
      patch.last_question_at || current?.last_question_at || baseUpdatedAt,
      baseUpdatedAt
    ),
    status: normalizeString(patch.status ?? current?.status, 64)
  })
  await getTable('offline_learning_state').put(next)
  return next
}

export const getCachedLearningState = async (videoId) => {
  const numericVideoId = normalizeIntegerId(videoId)
  if (!numericVideoId) return null
  return getTable('offline_learning_state').where('video_id').equals(numericVideoId).first()
}

export const touchVideoAccess = async (videoId, accessTime = nowIso()) => {
  const numericVideoId = normalizeIntegerId(videoId)
  if (!numericVideoId) return
  const video = await getTable('offline_videos').where('video_id').equals(numericVideoId).first()
  if (video) {
    await getTable('offline_videos').update(video.local_id, { lastAccessedAt: normalizeIsoTime(accessTime, nowIso()) })
  }
  const learningState = await getTable('offline_learning_state').where('video_id').equals(numericVideoId).first()
  if (learningState) {
    await getTable('offline_learning_state').update(learningState.local_id, {
      lastAccessedAt: normalizeIsoTime(accessTime, nowIso()),
      last_viewed_at: normalizeIsoTime(accessTime, nowIso())
    })
  }
  await touchRowsByVideoId('offline_subtitles', numericVideoId, accessTime)
  await touchRowsByVideoId('offline_notes', numericVideoId, accessTime)
  await touchRowsByVideoId('offline_questions', numericVideoId, accessTime)
}
