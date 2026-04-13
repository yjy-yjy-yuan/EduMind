const emptyArray = async () => []
const emptyObject = async () => ({})
const nullValue = async () => null
const passthrough = async (value) => value || {}

export const OFFLINE_MEMORY_LIMITS = Object.freeze({})
export const OFFLINE_SYNC_STATUS = Object.freeze({
  PENDING: 'pending',
  SYNCED: 'synced',
  FAILED: 'failed'
})

export const shouldUseOfflineMemoryMode = () => false

export const clearCache = async () => ({ disabled: true })
export const cleanupExpiredCache = async () => ({ disabled: true })
export const deleteCacheByVideoId = async () => ({ disabled: true })
export const getCacheSize = async () => 0

export const cacheLearningState = emptyObject
export const cacheVideoList = emptyArray
export const cacheVideoMetadata = passthrough
export const cacheVideoSubtitles = emptyArray
export const getAllCachedSubtitles = emptyArray
export const getCachedLearningState = nullValue
export const getCachedSubtitlePage = nullValue
export const getCachedVideo = nullValue
export const getCachedVideoOptions = emptyArray
export const touchVideoAccess = async () => {}

export const buildNotePayloadForSync = (note = {}) => note
export const cacheNoteRecord = passthrough
export const cacheNotes = async (notes = []) => notes
export const getOfflineNoteByIdentifier = nullValue
export const getOfflineNoteTags = emptyArray
export const getOfflineNotes = emptyArray

export const buildQuestionPayloadForSync = (payload = {}) => payload
export const cacheQuestionRecord = passthrough
export const getOfflineQaMessages = emptyArray
export const getOfflineQuestions = emptyArray

export const answerOfflineFromContext = (_context, _question) => ({
  answer: '离线记忆能力已从当前项目移除。',
  references: []
})
export const buildVideoMemoryContext = async () => ({})
export const formatMemoryPrompt = () => ''

export const cacheOnlineNote = passthrough
export const flush = async () => ({ flushed: 0, failed: 0, disabled: true })
export const offlineMemorySync = {
  flush,
  saveNoteOffline: async () => {
    throw new Error('离线记忆能力已从当前项目移除')
  },
  saveOfflineQuestion: async () => {
    throw new Error('离线记忆能力已从当前项目移除')
  }
}
export const persistQuestionResult = async () => ({ disabled: true })
export const saveNoteOffline = async () => {
  throw new Error('离线记忆能力已从当前项目移除')
}
export const saveOfflineQuestion = async () => {
  throw new Error('离线记忆能力已从当前项目移除')
}
