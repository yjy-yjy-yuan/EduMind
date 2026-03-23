import { buildProcessPayload } from '@/services/processingSettings'

export const OFFLINE_QUEUE_DB_NAME = 'edumind_offline_queue'
export const OFFLINE_QUEUE_STORE_NAME = 'offline_tasks'
const OFFLINE_QUEUE_DB_VERSION = 1
const RETRY_BASE_DELAY_MS = 60 * 1000
const RETRY_MAX_DELAY_MS = 5 * 60 * 1000

export const OFFLINE_TASK_TYPES = Object.freeze({
  LOCAL_UPLOAD: 'local_upload',
  URL_IMPORT: 'url_import'
})

export const OFFLINE_TASK_STATUSES = Object.freeze({
  OFFLINE_QUEUED: 'offline_queued',
  UPLOADING: 'uploading',
  FAILED: 'failed',
  COMPLETED: 'completed'
})

let dbPromise = null

const requestToPromise = (request) =>
  new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error || new Error('IndexedDB request failed'))
  })

const normalizeIsoTime = (value, fallback) => {
  if (!value) return fallback
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? fallback : date.toISOString()
}

const nowIso = () => new Date().toISOString()

const normalizeVideoId = (value) => {
  if (value == null || value === '') return null
  const numeric = Number(value)
  return Number.isFinite(numeric) && numeric > 0 ? numeric : null
}

const randomId = () => Math.random().toString(36).slice(2, 10)

const buildTaskId = () => {
  const cryptoApi = typeof globalThis !== 'undefined' ? globalThis.crypto : undefined
  if (cryptoApi?.randomUUID) return cryptoApi.randomUUID()
  return `offline-${Date.now()}-${randomId()}${randomId()}`
}

const fileExt = (filename) => {
  const name = String(filename || '').trim()
  const index = name.lastIndexOf('.')
  if (index < 0) return ''
  return name.slice(index + 1).toLowerCase()
}

const normalizeStatus = (value) => {
  const status = String(value || '').trim().toLowerCase()
  if (Object.values(OFFLINE_TASK_STATUSES).includes(status)) return status
  return OFFLINE_TASK_STATUSES.OFFLINE_QUEUED
}

const normalizeType = (value) => {
  const type = String(value || '').trim().toLowerCase()
  if (Object.values(OFFLINE_TASK_TYPES).includes(type)) return type
  return OFFLINE_TASK_TYPES.LOCAL_UPLOAD
}

const normalizeRetryCount = (value) => {
  const numeric = Number(value)
  return Number.isInteger(numeric) && numeric >= 0 ? numeric : 0
}

const normalizeProcessing = (value) => buildProcessPayload(value || {})

const normalizeTask = (input = {}) => {
  const taskId = String(input.taskId || buildTaskId())
  const createdAt = normalizeIsoTime(input.createdAt, nowIso())
  const updatedAt = normalizeIsoTime(input.updatedAt, createdAt)
  return {
    taskId,
    type: normalizeType(input.type),
    status: normalizeStatus(input.status),
    createdAt,
    updatedAt,
    retryCount: normalizeRetryCount(input.retryCount),
    lastError: input.lastError ? String(input.lastError) : '',
    tempKey: String(input.tempKey || `offline-${taskId}`),
    videoId: normalizeVideoId(input.videoId),
    processing: normalizeProcessing(input.processing),
    fileName: input.fileName ? String(input.fileName) : '',
    fileSize: Number(input.fileSize || 0) || 0,
    fileExt: input.fileExt ? String(input.fileExt).toLowerCase() : fileExt(input.fileName),
    blob: input.blob instanceof Blob ? input.blob : null,
    videoUrl: input.videoUrl ? String(input.videoUrl).trim() : ''
  }
}

const ensureIndexedDb = () => {
  if (typeof window === 'undefined' || !window.indexedDB) {
    throw new Error('当前环境不支持 IndexedDB，离线队列不可用')
  }
}

const openDatabase = async () => {
  ensureIndexedDb()
  if (dbPromise) return dbPromise

  dbPromise = new Promise((resolve, reject) => {
    const request = window.indexedDB.open(OFFLINE_QUEUE_DB_NAME, OFFLINE_QUEUE_DB_VERSION)

    request.onupgradeneeded = () => {
      const db = request.result
      if (db.objectStoreNames.contains(OFFLINE_QUEUE_STORE_NAME)) return
      const store = db.createObjectStore(OFFLINE_QUEUE_STORE_NAME, { keyPath: 'taskId' })
      store.createIndex('status', 'status', { unique: false })
      store.createIndex('updatedAt', 'updatedAt', { unique: false })
      store.createIndex('createdAt', 'createdAt', { unique: false })
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
      reject(request.error || new Error('打开 IndexedDB 失败'))
    }
  })

  return dbPromise
}

const withStore = async (mode, runner) => {
  const db = await openDatabase()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(OFFLINE_QUEUE_STORE_NAME, mode)
    const store = tx.objectStore(OFFLINE_QUEUE_STORE_NAME)
    let settled = false

    const finish = (resolver) => (value) => {
      if (settled) return
      settled = true
      resolver(value)
    }

    tx.oncomplete = () => finish(resolve)()
    tx.onerror = () => finish(reject)(tx.error || new Error('IndexedDB transaction failed'))
    tx.onabort = () => finish(reject)(tx.error || new Error('IndexedDB transaction aborted'))

    Promise.resolve()
      .then(() => runner(store))
      .then((value) => {
        if (value !== undefined) finish(resolve)(value)
      })
      .catch((error) => {
        try {
          tx.abort()
        } catch {
          // ignore abort failures
        }
        finish(reject)(error)
      })
  })
}

const sortByCreatedAt = (tasks = []) =>
  [...tasks].sort((left, right) => {
    const leftTime = new Date(left.createdAt).getTime()
    const rightTime = new Date(right.createdAt).getTime()
    return leftTime - rightTime
  })

export const isOfflineQueueSupported = () => typeof window !== 'undefined' && typeof window.indexedDB !== 'undefined'

export const createOfflineTaskId = () => buildTaskId()

export const createOfflineTaskTempKey = (taskId = buildTaskId()) => `offline-${taskId}`

export const getOfflineRetryDelayMs = (task = {}) => {
  const retryCount = normalizeRetryCount(task.retryCount)
  if (retryCount <= 0) return 0
  return Math.min(RETRY_MAX_DELAY_MS, RETRY_BASE_DELAY_MS * (2 ** (retryCount - 1)))
}

export const isOfflineTaskReadyForFlush = (task = {}, now = Date.now()) => {
  const status = normalizeStatus(task.status)
  if (![OFFLINE_TASK_STATUSES.OFFLINE_QUEUED, OFFLINE_TASK_STATUSES.FAILED].includes(status)) return false

  const updatedAt = new Date(task.updatedAt || task.createdAt || 0).getTime()
  if (!Number.isFinite(updatedAt) || updatedAt <= 0) return true

  return now - updatedAt >= getOfflineRetryDelayMs(task)
}

export const getOfflineTask = async (taskId) => {
  if (!taskId) return null
  return withStore('readonly', async (store) => {
    const task = await requestToPromise(store.get(String(taskId)))
    return task ? normalizeTask(task) : null
  })
}

export const getOfflineTasks = async () =>
  withStore('readonly', async (store) => {
    const tasks = await requestToPromise(store.getAll())
    return sortByCreatedAt(tasks.map((task) => normalizeTask(task)))
  })

export const getFlushableOfflineTasks = async (now = Date.now()) => {
  const tasks = await getOfflineTasks()
  return tasks.filter((task) => isOfflineTaskReadyForFlush(task, now))
}

export const putOfflineTask = async (taskInput = {}) => {
  const timestamp = nowIso()
  const task = normalizeTask({
    ...taskInput,
    createdAt: taskInput.createdAt || timestamp,
    updatedAt: taskInput.updatedAt || timestamp
  })
  return withStore('readwrite', async (store) => {
    await requestToPromise(store.put(task))
    return task
  })
}

export const createLocalUploadTask = async ({ file, processing, tempKey } = {}) => {
  if (!(file instanceof Blob)) throw new Error('离线本地任务缺少可持久化的文件 Blob')

  const taskId = buildTaskId()
  return putOfflineTask({
    taskId,
    type: OFFLINE_TASK_TYPES.LOCAL_UPLOAD,
    status: OFFLINE_TASK_STATUSES.OFFLINE_QUEUED,
    tempKey: tempKey || createOfflineTaskTempKey(taskId),
    processing,
    fileName: file.name || '',
    fileSize: Number(file.size || 0),
    fileExt: fileExt(file.name),
    blob: file
  })
}

export const createUrlImportTask = async ({ videoUrl, processing, tempKey } = {}) => {
  const trimmedUrl = String(videoUrl || '').trim()
  if (!trimmedUrl) throw new Error('离线链接任务缺少视频地址')

  const taskId = buildTaskId()
  return putOfflineTask({
    taskId,
    type: OFFLINE_TASK_TYPES.URL_IMPORT,
    status: OFFLINE_TASK_STATUSES.OFFLINE_QUEUED,
    tempKey: tempKey || createOfflineTaskTempKey(taskId),
    processing,
    videoUrl: trimmedUrl
  })
}

export const updateOfflineTask = async (taskId, updates = {}) => {
  const current = await getOfflineTask(taskId)
  if (!current) return null

  return putOfflineTask({
    ...current,
    ...updates,
    taskId: current.taskId,
    createdAt: current.createdAt,
    updatedAt: normalizeIsoTime(updates.updatedAt, nowIso())
  })
}

export const markOfflineTaskUploading = async (taskId) =>
  updateOfflineTask(taskId, {
    status: OFFLINE_TASK_STATUSES.UPLOADING,
    lastError: ''
  })

export const markOfflineTaskFailed = async (taskId, errorMessage) => {
  const current = await getOfflineTask(taskId)
  if (!current) return null

  return putOfflineTask({
    ...current,
    status: OFFLINE_TASK_STATUSES.FAILED,
    retryCount: current.retryCount + 1,
    lastError: errorMessage ? String(errorMessage) : ''
  })
}

export const markOfflineTaskCompleted = async (taskId, { videoId } = {}) =>
  updateOfflineTask(taskId, {
    status: OFFLINE_TASK_STATUSES.COMPLETED,
    videoId: normalizeVideoId(videoId),
    lastError: ''
  })

export const deleteOfflineTask = async (taskId) => {
  if (!taskId) return
  return withStore('readwrite', async (store) => {
    await requestToPromise(store.delete(String(taskId)))
  })
}
