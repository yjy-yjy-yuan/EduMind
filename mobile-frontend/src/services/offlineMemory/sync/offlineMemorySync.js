import { askQuestion } from '@/api/qa'
import { createNote, updateNote } from '@/api/note'
import { getBackendUnavailableMessage, hasReachableBackendConfig, isBackendUnavailableError } from '@/services/networkStatus'
import { cacheNoteRecord, markOfflineNoteFailed, buildNotePayloadForSync } from '@/services/offlineMemory/cache/noteCache'
import { buildQuestionPayloadForSync, cacheQuestionRecord, markOfflineQuestionFailed } from '@/services/offlineMemory/cache/questionCache'
import { OFFLINE_SYNC_ACTION } from '@/services/offlineMemory/sync/contracts'
import {
  OFFLINE_ENTITY_TYPE,
  OFFLINE_SYNC_STATUS,
  createBaseRecord,
  createLocalId,
  normalizeString,
  nowIso
} from '@/services/offlineMemory/storage/db'
import { getTable } from '@/services/offlineMemory/storage/repository'

const isNavigatorOffline = () => typeof navigator !== 'undefined' && navigator.onLine === false

export const shouldUseOfflineMemoryMode = (error = null) => {
  if (!hasReachableBackendConfig()) return true
  if (isNavigatorOffline()) return true
  return Boolean(error) && isBackendUnavailableError(error)
}

const normalizeQueuePayload = (payload = {}) => JSON.parse(JSON.stringify(payload))

export const enqueueSync = async ({
  entityType,
  entityLocalId,
  action,
  payload,
  serverId = null
}) => {
  const queueTable = getTable('offline_sync_queue')
  const existing = await queueTable.where('[entity_type+entity_local_id]').equals([entityType, entityLocalId]).first()
  const updatedAt = nowIso()
  const nextRecord = createBaseRecord({
    local_id: existing?.local_id || createLocalId('offline-sync'),
    server_id: serverId || existing?.server_id || null,
    updated_at: updatedAt,
    sync_status: OFFLINE_SYNC_STATUS.PENDING,
    lastAccessedAt: updatedAt,
    entity_type: entityType,
    entity_local_id: entityLocalId,
    action,
    created_at: existing?.created_at || updatedAt,
    run_after: updatedAt,
    retry_count: Number(existing?.retry_count || 0),
    payload: normalizeQueuePayload(payload),
    last_error: ''
  })
  await queueTable.put(nextRecord)
  return nextRecord
}

const markQueueItem = async (localId, patch = {}) => {
  if (!localId) return null
  const queueTable = getTable('offline_sync_queue')
  await queueTable.update(String(localId), {
    ...patch,
    updated_at: nowIso()
  })
  return queueTable.get(String(localId))
}

const syncNoteCreate = async (queueItem) => {
  const noteTable = getTable('offline_notes')
  const current = await noteTable.get(queueItem.entity_local_id)
  if (!current) {
    await markQueueItem(queueItem.local_id, {
      sync_status: OFFLINE_SYNC_STATUS.SYNCED
    })
    return
  }

  const response = await createNote(buildNotePayloadForSync(current))
  const remoteNote = response?.data?.data || response?.data?.note || response?.data
  const saved = await cacheNoteRecord(
    {
      ...current,
      ...remoteNote,
      local_id: current.local_id
    },
    { syncStatus: OFFLINE_SYNC_STATUS.SYNCED }
  )

  await markQueueItem(queueItem.local_id, {
    server_id: saved.server_id || saved.id || remoteNote?.id || null,
    sync_status: OFFLINE_SYNC_STATUS.SYNCED
  })
}

const syncNoteUpdate = async (queueItem) => {
  const noteTable = getTable('offline_notes')
  const current = await noteTable.get(queueItem.entity_local_id)
  if (!current) {
    await markQueueItem(queueItem.local_id, {
      sync_status: OFFLINE_SYNC_STATUS.SYNCED
    })
    return
  }

  if (!current.server_id) {
    await syncNoteCreate(queueItem)
    return
  }

  const response = await updateNote(current.server_id, buildNotePayloadForSync(current))
  const remoteNote = response?.data?.data || response?.data?.note || response?.data
  await cacheNoteRecord(
    {
      ...current,
      ...remoteNote,
      local_id: current.local_id
    },
    { syncStatus: OFFLINE_SYNC_STATUS.SYNCED }
  )
  await markQueueItem(queueItem.local_id, {
    server_id: String(current.server_id),
    sync_status: OFFLINE_SYNC_STATUS.SYNCED
  })
}

const syncQuestionAsk = async (queueItem) => {
  const questionTable = getTable('offline_questions')
  const current = await questionTable.get(queueItem.entity_local_id)
  if (!current) {
    await markQueueItem(queueItem.local_id, {
      sync_status: OFFLINE_SYNC_STATUS.SYNCED
    })
    return
  }

  const response = await askQuestion(buildQuestionPayloadForSync(current))
  const remoteQuestion = response?.data || response
  const saved = await cacheQuestionRecord(
    {
      ...current,
      ...remoteQuestion,
      id: remoteQuestion?.id || current.server_id,
      question: remoteQuestion?.content || current.question,
      answer: remoteQuestion?.answer || current.answer,
      references: Array.isArray(remoteQuestion?.references) ? remoteQuestion.references : current.references,
      source: 'online'
    },
    { syncStatus: OFFLINE_SYNC_STATUS.SYNCED }
  )

  await markQueueItem(queueItem.local_id, {
    server_id: saved.server_id || remoteQuestion?.id || null,
    sync_status: OFFLINE_SYNC_STATUS.SYNCED
  })
}

const syncOneQueueItem = async (queueItem) => {
  if (!queueItem?.entity_local_id) return
  if (queueItem.action === OFFLINE_SYNC_ACTION.CREATE_NOTE) {
    await syncNoteCreate(queueItem)
    return
  }
  if (queueItem.action === OFFLINE_SYNC_ACTION.UPDATE_NOTE) {
    await syncNoteUpdate(queueItem)
    return
  }
  if (queueItem.action === OFFLINE_SYNC_ACTION.ASK_QUESTION) {
    await syncQuestionAsk(queueItem)
  }
}

let flushPromise = null

export const flush = async () => {
  if (flushPromise) return flushPromise
  flushPromise = (async () => {
    if (shouldUseOfflineMemoryMode()) {
      return { skipped: true, reason: 'offline' }
    }

    const queueTable = getTable('offline_sync_queue')
    const queueItems = (await queueTable.toArray())
      .filter((item) => item.sync_status === OFFLINE_SYNC_STATUS.PENDING || item.sync_status === OFFLINE_SYNC_STATUS.FAILED)
      .sort((left, right) => new Date(left.created_at || left.updated_at || 0) - new Date(right.created_at || right.updated_at || 0))

    for (const item of queueItems) {
      try {
        await syncOneQueueItem(item)
      } catch (error) {
        const message = normalizeString(getBackendUnavailableMessage(error, error?.message || '同步失败'), 500)
        await markQueueItem(item.local_id, {
          sync_status: OFFLINE_SYNC_STATUS.FAILED,
          retry_count: Number(item.retry_count || 0) + 1,
          last_error: message,
          run_after: nowIso()
        })

        if (item.entity_type === OFFLINE_ENTITY_TYPE.NOTE) {
          await markOfflineNoteFailed(item.entity_local_id, message)
        }
        if (item.entity_type === OFFLINE_ENTITY_TYPE.QUESTION) {
          await markOfflineQuestionFailed(item.entity_local_id, message)
        }

        if (isBackendUnavailableError(error)) {
          break
        }
      }
    }

    return { skipped: false }
  })()

  try {
    return await flushPromise
  } finally {
    flushPromise = null
  }
}

export const saveNoteOffline = async (payload, { existingLocalId = null, existingServerId = null } = {}) => {
  const saved = await cacheNoteRecord(
    {
      ...payload,
      local_id: existingLocalId,
      server_id: existingServerId
    },
    { syncStatus: OFFLINE_SYNC_STATUS.PENDING }
  )

  await enqueueSync({
    entityType: OFFLINE_ENTITY_TYPE.NOTE,
    entityLocalId: saved.local_id,
    action: saved.server_id ? OFFLINE_SYNC_ACTION.UPDATE_NOTE : OFFLINE_SYNC_ACTION.CREATE_NOTE,
    payload: buildNotePayloadForSync(saved),
    serverId: saved.server_id
  })

  return saved
}

export const cacheOnlineNote = async (notePayload) =>
  cacheNoteRecord(notePayload, {
    syncStatus: OFFLINE_SYNC_STATUS.SYNCED
  })

export const persistQuestionResult = async ({
  question,
  answer,
  references = [],
  video_id = null,
  user_id = null,
  mode = 'video',
  provider = 'qwen',
  model = '',
  deep_thinking = false,
  history = [],
  source = 'online',
  syncStatus = OFFLINE_SYNC_STATUS.SYNCED,
  local_id = null,
  server_id = null
}) =>
  cacheQuestionRecord(
    {
      local_id,
      server_id,
      question,
      answer,
      references,
      video_id,
      user_id,
      mode,
      provider,
      model,
      deep_thinking,
      history,
      source
    },
    { syncStatus }
  )

export const saveOfflineQuestion = async (payload) => {
  const saved = await persistQuestionResult({
    ...payload,
    source: 'offline',
    syncStatus: OFFLINE_SYNC_STATUS.PENDING
  })

  await enqueueSync({
    entityType: OFFLINE_ENTITY_TYPE.QUESTION,
    entityLocalId: saved.local_id,
    action: OFFLINE_SYNC_ACTION.ASK_QUESTION,
    payload: buildQuestionPayloadForSync(saved)
  })

  return saved
}

export const offlineMemorySync = {
  enqueue: enqueueSync,
  flush
}
