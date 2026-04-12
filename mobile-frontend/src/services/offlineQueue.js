export const OFFLINE_QUEUE_DB_NAME = 'edumind_offline_queue'
export const OFFLINE_QUEUE_STORE_NAME = 'offline_tasks'
export const OFFLINE_QUEUE_EVENT_NAME = 'edumind:offline-queue-updated'

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

const disabledError = () => new Error('离线队列能力已从当前项目移除')
const noopTaskList = async () => []
const noopTask = async () => null
const passthroughTask = async (task = {}) => task

export const isOfflineQueueSupported = () => false
export const createOfflineTaskId = () => ''
export const createOfflineTaskTempKey = () => ''
export const getOfflineRetryDelayMs = () => 0
export const isOfflineTaskReadyForFlush = () => false
export const getOfflineTask = noopTask
export const getOfflineTasks = noopTaskList
export const getFlushableOfflineTasks = noopTaskList
export const getPendingOfflineTasks = noopTaskList
export const putOfflineTask = passthroughTask
export const createLocalUploadTask = passthroughTask
export const createUrlImportTask = passthroughTask
export const deleteOfflineTask = async () => false
export const removeOfflineTask = async () => false
export const updateOfflineTask = passthroughTask
export const markOfflineTaskFailed = passthroughTask
export const markOfflineTaskUploading = passthroughTask
export const markOfflineTaskCompleted = passthroughTask
export const resolveOfflineTaskVideoId = () => null
export const enqueueOfflineUploadFromError = async () => {
  throw disabledError()
}
export const flushOfflineQueue = async () => ({ flushed: 0, failed: 0, disabled: true })
