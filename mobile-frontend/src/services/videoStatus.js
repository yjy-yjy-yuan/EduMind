const ACTIVE_VIDEO_STATUSES = new Set(['pending', 'processing', 'downloading'])
const COMPLETED_VIDEO_STATUSES = new Set(['completed'])
const AUTO_START_VIDEO_STATUSES = new Set(['uploaded', 'failed'])

export const normalizeVideoStatus = (status) => {
  const normalized = String(status || '').trim().toLowerCase()
  if (normalized === 'processed') return 'completed'
  return normalized || 'unknown'
}

export const isActiveVideoStatus = (status) => ACTIVE_VIDEO_STATUSES.has(normalizeVideoStatus(status))

export const isCompletedVideoStatus = (status) => COMPLETED_VIDEO_STATUSES.has(normalizeVideoStatus(status))

export const canAutoStartVideoProcessing = (status) => AUTO_START_VIDEO_STATUSES.has(normalizeVideoStatus(status))

export const canRetryVideoProcessing = (status) => normalizeVideoStatus(status) === 'failed'

export const canPlayVideo = (status) => isCompletedVideoStatus(status)

export const videoStatusText = (status) => {
  const map = {
    uploaded: '已上传',
    pending: '排队中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
    downloading: '下载中',
    offline_queued: '离线排队中',
    uploading: '自动补跑中',
    unknown: '未知'
  }
  return map[normalizeVideoStatus(status)] || '未知'
}

export const videoStatusTone = (status) => {
  const normalized = normalizeVideoStatus(status)
  if (normalized === 'completed') return 'ok'
  if (normalized === 'failed') return 'bad'
  if (normalized === 'offline_queued' || normalized === 'uploading') return 'warn'
  if (ACTIVE_VIDEO_STATUSES.has(normalized)) return 'warn'
  return 'info'
}

export const createFixedIntervalPoller = ({ intervalMs = 2000, shouldPoll, onTick }) => {
  let timerId = null
  let active = false

  const clear = () => {
    if (timerId == null) return
    window.clearTimeout(timerId)
    timerId = null
  }

  const schedule = () => {
    if (!active || !shouldPoll()) return
    timerId = window.setTimeout(run, intervalMs)
  }

  const run = async () => {
    timerId = null
    if (!active || !shouldPoll()) return
    await onTick()
    schedule()
  }

  return {
    start() {
      active = true
      clear()
      schedule()
    },
    stop() {
      active = false
      clear()
    }
  }
}
