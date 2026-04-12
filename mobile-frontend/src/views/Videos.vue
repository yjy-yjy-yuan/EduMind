<template>
  <div class="page">
    <header class="topbar">
      <h2>{{ scopeTitle }}</h2>
      <div class="top-actions">
        <button
          v-if="failedVideos.length > 1"
          class="link link--warn"
          @click="retryAllFailed"
          :disabled="loading || batchRetrying"
        >
          {{ batchRetrying ? '批量重试中…' : `批量重试失败(${failedVideos.length})` }}
        </button>
        <button class="link" @click="reload(true)" :disabled="loading || batchRetrying">
          {{ loading ? '加载中…' : '刷新' }}
        </button>
      </div>
    </header>

    <div class="scope-switch">
      <button
        v-for="item in scopeTabs"
        :key="item.value"
        class="scope-pill"
        :class="{ 'scope-pill--active': scope === item.value }"
        @click="setScope(item.value)"
      >
        {{ item.label }}
      </button>
    </div>

    <div v-if="hasActiveTasks" class="polling-tip">
      <span>{{ pollStatusText }}</span>
      <button v-if="pollPaused" class="link link--warn" @click="resumePolling" :disabled="loading || batchRetrying">
        恢复自动刷新
      </button>
    </div>

    <div v-if="offlineTaskCount > 0" class="queue-tip">
      还有 {{ offlineTaskCount }} 个离线任务在上传页等待自动补跑；这些任务拿到视频 ID 后会继续回到当前列表和详情页状态链路。
    </div>


    <div v-if="error" class="alert alert--bad">
      <span>{{ error }}</span>
      <button class="link" @click="reload(true)">重试</button>
    </div>

    <div v-else-if="loading && videos.length === 0" class="skeleton">
      <div v-for="i in 6" :key="i" class="sk-card"></div>
    </div>

    <div v-else-if="filteredVideos.length === 0" class="empty">
      {{ emptyText }}
      <button class="link" @click="go('/upload')">去上传</button>
    </div>

    <div v-else class="list">
      <div v-for="v in filteredVideos" :key="v.id" class="card">
        <button class="card-main" @click="openVideo(v)">
          <div class="row">
            <div class="title" :title="v.title || ''">{{ v.title || '未命名视频' }}</div>
            <i class="arrow">›</i>
          </div>
          <div class="meta">
            <span class="badge" :class="badgeClass(v.status)">{{ statusText(v.status) }}</span>
            <span v-if="v.processing_origin_label" class="muted">{{ v.processing_origin_label }}</span>
            <span v-if="isInProgress(v.status)" class="muted">{{ Number(v.process_progress) || 0 }}%</span>
          </div>
          <div v-if="processingModelText(v)" class="muted">{{ processingModelText(v) }}</div>
          <div v-if="isInProgress(v.status)" class="progress">
            <div class="bar" :style="{ width: `${Number(v.process_progress) || 0}%` }"></div>
          </div>
        </button>
        <div v-if="v.status === 'failed'" class="card-actions">
          <button class="mini mini--warn" @click="retryFailed(v)" :disabled="isRetrying(v.id) || batchRetrying">
            {{ isRetrying(v.id) ? '重试中…' : '一键重试处理' }}
          </button>
        </div>
      </div>
    </div>

    <div class="footer">
      <button class="load-more" @click="loadMore" :disabled="loading || !hasMore">
        {{ hasMore ? (loading ? '加载中…' : '加载更多') : '没有更多了' }}
      </button>
    </div>

    <div v-if="message" class="alert alert--ok">
      <span>{{ message }}</span>
      <button class="link" @click="message = ''">关闭</button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getVideoList, processVideo } from '@/api/video'
import { OFFLINE_QUEUE_EVENT_NAME, getPendingOfflineTasks } from '@/services/offlineQueue'
import { buildProcessPayload, getProcessingSettings, whisperModelLabel } from '@/services/processingSettings'
import { isActiveVideoStatus, normalizeVideoStatus, videoStatusText, videoStatusTone } from '@/services/videoStatus'

const route = useRoute()
const router = useRouter()
const go = (path) => router.push(path)
const openVideo = (video) => {
  go(`/videos/${video.id}`)
}

const loading = ref(false)
const error = ref('')
const message = ref('')
const page = ref(1)
const pageSize = 10
const hasMore = ref(true)
const videos = ref([])
const offlineTaskCount = ref(0)
const retryingIds = ref({})
const batchRetrying = ref(false)
const POLL_BASE_INTERVAL_MS = 3000
const POLL_MAX_INTERVAL_MS = 30000
const POLL_FAILURE_LIMIT = 5
const pollFailureCount = ref(0)
const pollDelayMs = ref(POLL_BASE_INTERVAL_MS)
let pollTimer = null
const scopeTabs = [
  { value: 'recent', label: '最近视频' },
  { value: 'completed', label: '已完成' },
  { value: 'active', label: '进行中' }
]
const validScopes = new Set(scopeTabs.map((item) => item.value))

const scope = computed(() => {
  const raw = String(route.query.scope || 'recent').toLowerCase()
  return validScopes.has(raw) ? raw : 'recent'
})

const scopeTitle = computed(() => {
  if (scope.value === 'completed') return '已完成视频'
  if (scope.value === 'active') return '进行中视频'
  return '最近视频'
})

const normalizeList = (payload) => {
  const list = payload?.videos || payload?.items || payload?.data || payload || []
  return Array.isArray(list) ? list : []
}

const filteredVideos = computed(() => {
  if (scope.value === 'completed') return videos.value.filter((item) => normalizeVideoStatus(item?.status) === 'completed')
  if (scope.value === 'active') return videos.value.filter((item) => isActiveVideoStatus(item?.status))
  return videos.value
})

const emptyText = computed(() => {
  if (scope.value === 'completed') return '暂无已完成视频。'
  if (scope.value === 'active') return '暂无进行中的视频。'
  return '暂无视频。'
})

const failedVideos = computed(() => filteredVideos.value.filter((item) => normalizeVideoStatus(item?.status) === 'failed'))
const isInProgress = (status) => isActiveVideoStatus(status)
const hasActiveTasks = computed(() =>
  filteredVideos.value.some((item) => isInProgress(item?.status))
)
const pollPaused = computed(() => pollFailureCount.value >= POLL_FAILURE_LIMIT)
const pollStatusText = computed(() => {
  if (pollPaused.value) return '网络不稳定，自动刷新已暂停，请手动恢复或点击刷新'
  if (pollFailureCount.value > 0) return `网络波动，${Math.ceil(pollDelayMs.value / 1000)} 秒后重试`
  return '检测到处理中任务，列表每 3 秒自动刷新'
})

const reload = async (reset = false) => {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    if (reset) {
      page.value = 1
      hasMore.value = true
      videos.value = []
    }
    const res = await getVideoList(page.value, pageSize)
    const list = normalizeList(res.data)
    videos.value = page.value === 1 ? list : [...videos.value, ...list]
    hasMore.value = list.length >= pageSize
    resetPollBackoff()
  } catch (e) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const extractErrorMessage = (err, fallback) => {
  const detail = err?.response?.data?.detail
  if (Array.isArray(detail)) {
    const first = detail.find(Boolean)
    if (typeof first === 'string') return first
    if (first?.msg) return first.msg
  }
  if (typeof detail === 'string' && detail.trim()) return detail.trim()
  const messageText = err?.response?.data?.message || err?.response?.data?.msg
  if (typeof messageText === 'string' && messageText.trim()) return messageText.trim()
  return err?.message || fallback
}

const isRetrying = (videoId) => Boolean(retryingIds.value[String(videoId)])

const setLocalStatus = (videoId, nextStatus) => {
  const id = Number(videoId)
  videos.value = videos.value.map((item) => {
    if (Number(item.id) !== id) return item
    return { ...item, status: nextStatus, process_progress: 0 }
  })
}

const processingModelText = (video) => {
  const model = String(video?.effective_model || video?.requested_model || '').trim().toLowerCase()
  return model ? `模型：${whisperModelLabel(model)}` : ''
}

const retryFailed = async (video) => {
  const videoId = Number(video?.id)
  if (!videoId || isRetrying(videoId)) return
  retryingIds.value = { ...retryingIds.value, [String(videoId)]: true }
  error.value = ''
  message.value = ''
  try {
    await processVideo(videoId, buildProcessPayload(getProcessingSettings()))
    setLocalStatus(videoId, 'pending')
    message.value = `视频 ${videoId} 已重新提交处理`
    await reload(true)
  } catch (e) {
    error.value = extractErrorMessage(e, '重试失败')
  } finally {
    const next = { ...retryingIds.value }
    delete next[String(videoId)]
    retryingIds.value = next
  }
}

const retryAllFailed = async () => {
  if (batchRetrying.value) return
  const targets = failedVideos.value.map((v) => Number(v.id)).filter(Boolean)
  if (targets.length === 0) return

  batchRetrying.value = true
  error.value = ''
  message.value = ''

  try {
    const startMap = { ...retryingIds.value }
    for (const id of targets) startMap[String(id)] = true
    retryingIds.value = startMap

    const results = await Promise.allSettled(
      targets.map(async (id) => {
        await processVideo(id, buildProcessPayload(getProcessingSettings()))
        return id
      })
    )

    const successIds = []
    const failed = []
    for (const r of results) {
      if (r.status === 'fulfilled') successIds.push(r.value)
      else failed.push(r.reason)
    }

    for (const id of successIds) setLocalStatus(id, 'pending')

    if (successIds.length > 0 && failed.length === 0) {
      message.value = `批量重试成功，共 ${successIds.length} 个任务`
    } else if (successIds.length > 0 && failed.length > 0) {
      message.value = `批量重试部分成功：成功 ${successIds.length}，失败 ${failed.length}`
      error.value = extractErrorMessage(failed[0], '部分任务重试失败')
    } else {
      error.value = extractErrorMessage(failed[0], '批量重试失败')
    }

    await reload(true)
  } finally {
    const next = { ...retryingIds.value }
    for (const id of targets) delete next[String(id)]
    retryingIds.value = next
    batchRetrying.value = false
  }
}

const pollRefresh = async () => {
  if (loading.value || batchRetrying.value) return true
  const perPage = Math.max(page.value * pageSize, pageSize)
  try {
    const res = await getVideoList(1, perPage)
    const list = normalizeList(res.data)
    videos.value = list
    hasMore.value = list.length >= perPage
    if (!hasMore.value) page.value = Math.max(1, Math.ceil(list.length / pageSize) || 1)
    return true
  } catch {
    return false
  }
}

const stopPolling = () => {
  if (!pollTimer) return
  clearTimeout(pollTimer)
  pollTimer = null
}

const resetPollBackoff = () => {
  pollFailureCount.value = 0
  pollDelayMs.value = POLL_BASE_INTERVAL_MS
}

const increasePollBackoff = () => {
  pollFailureCount.value += 1
  pollDelayMs.value = Math.min(POLL_MAX_INTERVAL_MS, pollDelayMs.value * 2)
}

const scheduleNextPoll = (delay) => {
  stopPolling()
  if (!hasActiveTasks.value || pollPaused.value) return
  pollTimer = setTimeout(async () => {
    if (!hasActiveTasks.value || pollPaused.value) return
    const ok = await pollRefresh()
    if (ok) {
      resetPollBackoff()
    } else {
      increasePollBackoff()
    }
    scheduleNextPoll(ok ? POLL_BASE_INTERVAL_MS : pollDelayMs.value)
  }, delay)
}

const startPollingIfNeeded = () => {
  stopPolling()
  if (!hasActiveTasks.value) return
  if (pollPaused.value) return
  scheduleNextPoll(POLL_BASE_INTERVAL_MS)
}

const reloadOfflineTaskCount = async () => {
  try {
    const tasks = await getPendingOfflineTasks()
    offlineTaskCount.value = tasks.length
  } catch {
    offlineTaskCount.value = 0
  }
}

const resumePolling = () => {
  if (!hasActiveTasks.value) return
  resetPollBackoff()
  scheduleNextPoll(0)
}

const loadMore = async () => {
  if (!hasMore.value || loading.value) return
  page.value += 1
  await reload(false)
}

const statusText = videoStatusText

const badgeClass = (status) => {
  const tone = videoStatusTone(status)
  if (tone === 'ok') return 'ok'
  if (tone === 'bad') return 'bad'
  if (tone === 'warn') return 'warn'
  return 'info'
}

const setScope = (nextScope) => {
  if (!validScopes.has(nextScope)) return
  router.push({ path: '/videos', query: { scope: nextScope } })
}

watch(hasActiveTasks, () => {
  if (!hasActiveTasks.value) resetPollBackoff()
  startPollingIfNeeded()
})

watch(
  () => route.query.scope,
  () => {
    if (!validScopes.has(String(route.query.scope || 'recent').toLowerCase())) {
      router.replace({ path: '/videos', query: { scope: 'recent' } })
    }
  },
  { immediate: true }
)

onMounted(async () => {
  window.addEventListener(OFFLINE_QUEUE_EVENT_NAME, reloadOfflineTaskCount)
  await reloadOfflineTaskCount()
  await reload(true)
  startPollingIfNeeded()
})

onUnmounted(() => {
  stopPolling()
  window.removeEventListener(OFFLINE_QUEUE_EVENT_NAME, reloadOfflineTaskCount)
})
</script>

<style scoped>
.page {
  max-width: 520px;
  margin: 0 auto;
  padding: 16px 16px 0;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 10px;
  gap: 8px;
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.topbar h2 {
  margin: 0;
  font-size: 16px;
}

.polling-tip {
  margin: -2px 0 10px;
  font-size: 12px;
  color: #6b7280;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.queue-tip {
  margin: -2px 0 10px;
  padding: 10px 12px;
  border-radius: 12px;
  background: var(--surface-lilac);
  border: 1px solid var(--primary-soft-strong);
  color: var(--primary-deep);
  font-size: 12px;
  line-height: 1.5;
}

.queue-tip--local {
  background: rgba(16, 185, 129, 0.08);
  border-color: rgba(16, 185, 129, 0.18);
  color: #065f46;
}

.scope-switch {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin: 10px 0 10px;
}

.scope-pill {
  border: 1px solid var(--border);
  background: rgba(248, 242, 250, 0.98);
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 800;
  color: var(--text);
}

.scope-pill--active {
  border-color: var(--primary-soft-strong);
  background: var(--surface-lilac);
  color: var(--primary-deep);
}

.link {
  border: 0;
  background: transparent;
  color: var(--primary);
  font-weight: 900;
}

.link--warn {
  color: var(--lilac-text);
}

.alert {
  padding: 10px 12px;
  border-radius: 12px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-weight: 700;
  align-items: flex-start;
  flex-wrap: wrap;
}

.alert--bad {
  background: var(--lilac-bg);
  color: var(--lilac-text);
}

.alert--ok {
  margin-top: 10px;
  background: var(--ok-bg);
  color: var(--ok-text);
}

.skeleton {
  display: grid;
  gap: 10px;
}

.sk-card {
  height: 92px;
  border-radius: var(--radius);
  background: linear-gradient(90deg, #ebe3f4, #e2d8f0, #ebe3f4);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
}

@keyframes shimmer {
  0% { background-position: 0% 0; }
  100% { background-position: 200% 0; }
}

.empty {
  color: var(--muted);
  font-size: 13px;
}

.list {
  display: grid;
  gap: 10px;
}

.card {
  border-radius: var(--radius);
  background: var(--card);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  overflow: hidden;
}

.card-main {
  border: 0;
  width: 100%;
  text-align: left;
  padding: 14px;
  display: grid;
  gap: 10px;
  background: transparent;
}

.card-actions {
  padding: 0 14px 12px;
  display: flex;
  justify-content: flex-end;
}

.row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.title {
  font-size: 14px;
  font-weight: 900;
  min-width: 0;
  flex: 1;
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.arrow {
  color: #9ca3af;
  font-style: normal;
  font-size: 22px;
  flex-shrink: 0;
}

.meta {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.muted {
  color: var(--muted);
  font-size: 12px;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  white-space: normal;
  text-align: center;
}

.badge.ok { background: var(--ok-bg); color: var(--ok-text); }
.badge.warn { background: var(--lilac-bg); color: var(--lilac-text); }
.badge.bad { background: var(--lilac-bg); color: var(--lilac-text); }
.badge.info { background: rgba(139, 121, 157, 0.14); color: #665775; }

.progress {
  height: 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.bar {
  height: 100%;
  background: linear-gradient(90deg, #665775, #8b799d);
}

.mini {
  border: 1px solid var(--border);
  background: rgba(248, 242, 250, 0.98);
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 800;
  color: var(--text);
  text-align: center;
}

.mini--warn {
  border-color: var(--lilac-border);
  background: var(--lilac-bg);
  color: var(--lilac-text);
}

.mini:disabled {
  opacity: 0.6;
}

.footer {
  padding: 16px 0 12px;
  display: flex;
  justify-content: center;
}

.load-more {
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(248, 242, 250, 0.98);
  border-radius: 999px;
  padding: 10px 14px;
  font-weight: 900;
  color: var(--text);
}

@media (max-width: 420px) {
  .top-actions,
  .polling-tip,
  .card-actions {
    width: 100%;
  }

  .top-actions {
    justify-content: flex-start;
  }

  .card-actions {
    justify-content: flex-start;
  }
}
</style>
<style scoped>
.page {
  padding-top: calc(14px + env(safe-area-inset-top));
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 5;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(248, 242, 250, 0.94);
  border: 1px solid rgba(32, 42, 55, 0.08);
  box-shadow: 0 10px 22px rgba(101, 87, 117, 0.09);
}

.topbar h2 {
  font-size: 18px;
}

.polling-tip {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px dashed var(--primary-soft-strong);
  background: var(--surface-lilac);
}

.list {
  margin-top: 10px;
  gap: 12px;
}

.card {
  border-radius: 20px;
  border: 1px solid rgba(32, 42, 55, 0.09);
  background: linear-gradient(180deg, rgba(248, 242, 250, 0.98), rgba(242, 235, 248, 0.96));
  box-shadow: 0 12px 24px rgba(101, 87, 117, 0.08);
}

.card-main {
  padding: 16px;
  gap: 11px;
}

.title {
  font-size: 15px;
}

.badge.ok {
  background: var(--ok-bg);
  color: var(--ok-text);
}

.badge.warn {
  background: var(--lilac-bg);
  color: var(--lilac-text);
}

.badge.bad {
  background: var(--lilac-bg);
  color: var(--lilac-text);
}

.badge.info {
  background: var(--info-bg);
  color: var(--info-text);
}

.bar {
  background: linear-gradient(90deg, #665775, #8b799d);
}

.load-more {
  border-color: var(--primary-soft-strong);
  color: var(--primary-deep);
}
</style>
