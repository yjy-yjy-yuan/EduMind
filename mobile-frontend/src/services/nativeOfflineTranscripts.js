export const NATIVE_OFFLINE_TRANSCRIPTS_EVENT_NAME = 'edumind:native-offline-transcripts-updated'

const disabledError = () => new Error('本地离线转录能力已从当前项目移除')

export const getNativeOfflineTranscript = async () => null
export const listNativeOfflineTranscripts = async () => []
export const getLatestNativeOfflineTranscript = async () => null

export const saveNativeOfflineTranscript = async () => {
  throw disabledError()
}

export const deleteNativeOfflineTranscript = async () => false
