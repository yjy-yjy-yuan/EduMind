const DB_NAME = 'edumind_native_offline_transcripts'
const STORE_NAME = 'transcripts'
const DB_VERSION = 1

export const NATIVE_OFFLINE_TRANSCRIPTS_EVENT_NAME = 'edumind:native-offline-transcripts-updated'

let dbPromise = null

const requestToPromise = (request) =>
  new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error || new Error('IndexedDB request failed'))
  })

const emitTranscriptStoreEvent = (detail = {}) => {
  if (typeof window === 'undefined' || typeof window.dispatchEvent !== 'function') return
  window.dispatchEvent(new CustomEvent(NATIVE_OFFLINE_TRANSCRIPTS_EVENT_NAME, { detail }))
}

const normalizeStatus = (status) => {
  const value = String(status || '').trim().toLowerCase()
  return value || 'unknown'
}

const normalizeSegments = (segments) => {
  if (!Array.isArray(segments)) return []
  return segments
    .filter(Boolean)
    .map((segment) => ({
      text: String(segment.text || segment.substring || '').trim(),
      start: Number(segment.start ?? segment.timestamp ?? 0) || 0,
      duration: Number(segment.duration ?? 0) || 0,
      confidence: Number(segment.confidence ?? 0) || 0
    }))
}

const normalizeTags = (tags) => {
  if (!Array.isArray(tags)) return []
  const seen = new Set()
  return tags
    .map((tag) => String(tag || '').trim())
    .filter((tag) => {
      if (!tag) return false
      const key = tag.toLowerCase()
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
}

const normalizeTranscript = (input = {}) => {
  const now = new Date().toISOString()
  return {
    taskId: String(input.taskId || ''),
    fileName: String(input.fileName || '本地视频'),
    fileSize: Number(input.fileSize || 0) || 0,
    fileExt: String(input.fileExt || '').trim().toLowerCase(),
    status: normalizeStatus(input.status),
    progress: Math.max(0, Math.min(100, Math.round(Number(input.progress || 0) || 0))),
    currentStep: String(input.currentStep || input.message || ''),
    transcriptText: String(input.transcriptText || ''),
    errorMessage: String(input.errorMessage || ''),
    summary: String(input.summary || ''),
    summaryStyle: String(input.summaryStyle || 'study'),
    summaryStatus: String(input.summaryStatus || 'idle').trim().toLowerCase() || 'idle',
    summaryErrorMessage: String(input.summaryErrorMessage || ''),
    summaryUpdatedAt: String(input.summaryUpdatedAt || ''),
    autoGenerateSummary: Boolean(input.autoGenerateSummary),
    autoGenerateTags: typeof input.autoGenerateTags === 'boolean' ? input.autoGenerateTags : true,
    tags: normalizeTags(input.tags),
    syncedVideoId: Number(input.syncedVideoId || 0) || 0,
    syncStatus: String(input.syncStatus || 'idle').trim().toLowerCase() || 'idle',
    syncErrorMessage: String(input.syncErrorMessage || ''),
    syncUpdatedAt: String(input.syncUpdatedAt || ''),
    locale: String(input.locale || ''),
    engine: String(input.engine || 'apple_speech_on_device'),
    segments: normalizeSegments(input.segments),
    createdAt: String(input.createdAt || now),
    updatedAt: String(input.updatedAt || now)
  }
}

const sortByUpdatedAtDesc = (items = []) =>
  [...items].sort((a, b) => {
    const left = new Date(a.updatedAt || a.createdAt || 0).getTime()
    const right = new Date(b.updatedAt || b.createdAt || 0).getTime()
    return right - left
  })

const openDatabase = async () => {
  if (typeof window === 'undefined' || !window.indexedDB) {
    throw new Error('当前环境不支持 IndexedDB，本地离线转录结果无法持久化')
  }

  if (dbPromise) return dbPromise

  dbPromise = new Promise((resolve, reject) => {
    const request = window.indexedDB.open(DB_NAME, DB_VERSION)

    request.onupgradeneeded = () => {
      const db = request.result
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'taskId' })
        store.createIndex('updatedAt', 'updatedAt', { unique: false })
        store.createIndex('status', 'status', { unique: false })
      }
    }

    request.onsuccess = () => {
      const db = request.result
      db.onversionchange = () => {
        db.close()
        dbPromise = null
      }
      resolve(db)
    }

    request.onerror = () => {
      dbPromise = null
      reject(request.error || new Error('打开本地离线转录数据库失败'))
    }
  })

  return dbPromise
}

const runTransaction = async (mode, handler) => {
  const db = await openDatabase()

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(STORE_NAME, mode)
    const store = transaction.objectStore(STORE_NAME)
    let result
    let settled = false

    const finish = (fn, value) => {
      if (settled) return
      settled = true
      fn(value)
    }

    transaction.oncomplete = () => finish(resolve, result)
    transaction.onerror = () => finish(reject, transaction.error || new Error('IndexedDB transaction failed'))
    transaction.onabort = () => finish(reject, transaction.error || new Error('IndexedDB transaction aborted'))

    Promise.resolve()
      .then(() => handler(store))
      .then((value) => {
        result = value
      })
      .catch((error) => {
        try {
          transaction.abort()
        } catch {
          // ignore
        }
        finish(reject, error)
      })
  })
}

export const getNativeOfflineTranscript = async (taskId) => {
  if (!taskId) return null
  return runTransaction('readonly', async (store) => {
    const record = await requestToPromise(store.get(String(taskId)))
    return record ? normalizeTranscript(record) : null
  })
}

export const listNativeOfflineTranscripts = async () =>
  runTransaction('readonly', async (store) => {
    const list = await requestToPromise(store.getAll())
    return sortByUpdatedAtDesc(list.map((item) => normalizeTranscript(item)))
  })

export const saveNativeOfflineTranscript = async (patch = {}) => {
  const taskId = String(patch.taskId || '').trim()
  if (!taskId) {
    throw new Error('本地离线转录结果缺少 taskId，无法保存')
  }

  const existing = await getNativeOfflineTranscript(taskId)
  const now = new Date().toISOString()
  const record = normalizeTranscript({
    ...existing,
    ...patch,
    taskId,
    createdAt: existing?.createdAt || patch.createdAt || now,
    updatedAt: now
  })

  const saved = await runTransaction('readwrite', async (store) => {
    await requestToPromise(store.put(record))
    return record
  })

  emitTranscriptStoreEvent({
    reason: 'save',
    taskId: saved.taskId,
    status: saved.status
  })

  return saved
}

export const deleteNativeOfflineTranscript = async (taskId) => {
  const id = String(taskId || '').trim()
  if (!id) return

  await runTransaction('readwrite', async (store) => {
    await requestToPromise(store.delete(id))
    return true
  })

  emitTranscriptStoreEvent({
    reason: 'delete',
    taskId: id
  })
}

export const getLatestNativeOfflineTranscript = async () => {
  const items = await listNativeOfflineTranscripts()
  return items[0] || null
}
