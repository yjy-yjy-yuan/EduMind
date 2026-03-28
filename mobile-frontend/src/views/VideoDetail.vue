<template>
  <div class="page">
    <header class="topbar">
      <button class="back" @click="router.back()">‹</button>
      <div class="topbar-title">视频详情</div>
      <button class="link" @click="reload" :disabled="loading">{{ loading ? '…' : '刷新' }}</button>
    </header>

    <div v-if="error" class="alert alert--bad">
      <span>{{ error }}</span>
      <button class="link" @click="reload">重试</button>
    </div>

    <div v-else-if="loading && !video" class="skeleton">
      <div class="sk-hero"></div>
      <div class="sk-line"></div>
      <div class="sk-line"></div>
    </div>

    <div v-else-if="!video" class="empty">未找到该视频。</div>

    <div v-else class="card">
      <div class="hero">
        <div class="hero-shell" :class="heroClass">
          <div class="hero-shell__badge">{{ usingMockGateway ? 'UI ONLY' : 'LIVE' }}</div>
          <div class="hero-shell__initial">{{ heroInitial }}</div>
          <div class="hero-shell__caption">
            {{ usingMockGateway ? '当前阶段仅构建界面，封面与播放器资源后续通过预留接口接入。' : '视频预览与播放资源由后端接口提供。' }}
          </div>
        </div>
      </div>

      <h2 class="title">{{ video.title || '未命名视频' }}</h2>

      <div class="meta">
        <span class="badge" :class="badgeClass(statusValue)">{{ statusText(statusValue) }}</span>
        <span v-if="autoStarting" class="muted">正在自动启动处理…</span>
        <span v-if="isInProgress(statusValue)" class="muted">{{ progressValue }}% · {{ stepValue || '处理中' }}</span>
      </div>

      <div v-if="offlineTaskCount > 0" class="inline-tip inline-tip--queue">
        上传页还有 {{ offlineTaskCount }} 个离线任务等待自动补跑；本页只展示已经拿到视频 ID 的在线处理状态。
      </div>

      <div v-if="activeModelText" class="setting-hint">本次任务模型：{{ activeModelText }}</div>

      <div v-if="isInProgress(statusValue)" class="progress">
        <div class="bar" :style="{ width: `${progressValue}%` }"></div>
      </div>

      <div v-if="canOpenPlayerWhileProcessing" class="inline-tip">
        后台处理中仍可进入播放器，当前播放原始视频文件。
      </div>

      <div class="block">
        <WhisperModelPicker
          title="Whisper 模型"
          :model="processingSettings.model"
          :options="whisperModelOptions"
          :disabled="processDisabled"
          @select="selectProcessingModel"
        />
      </div>

      <div v-if="canShowAnalysisBlock" class="block">
        <div class="block-head">
          <div class="block-title">智能摘要</div>
          <div class="block-actions">
            <button class="mini" @click="createSummary" :disabled="!canGenerateSummary || summaryGenerating || tagGenerating || summaryImporting">
              {{ summaryGenerating ? '生成中…' : (video.summary ? '重生成摘要' : '生成摘要') }}
            </button>
            <button class="mini" @click="createTags" :disabled="!canGenerateTags || summaryGenerating || tagGenerating || summaryImporting">
              {{ tagGenerating ? '提取中…' : (tagList.length > 0 ? '重提标签' : '提取标签') }}
            </button>
            <button class="mini mini--primary" @click="importSummaryToNote" :disabled="!canImportSummary">
              {{ summaryImporting ? '导入中…' : '导入到笔记' }}
            </button>
          </div>
        </div>
        <div class="setting-hint">当前摘要设置：{{ summaryStyleText }}</div>
        <div v-if="video.summary" class="block-body block-body--prewrap">{{ video.summary }}</div>
        <div v-else class="block-placeholder">处理完成后可在此生成课程摘要。</div>
        <div v-if="tagList.length > 0" class="tag-list">
          <span v-for="tag in tagList" :key="tag" class="tag-pill">{{ tag }}</span>
        </div>
      </div>

      <div class="block">
        <div class="block-head">
          <div>
            <div class="block-title">本视频笔记</div>
            <div class="setting-hint">把视频里的关键结论沉淀到笔记页，形成稳定回看入口。</div>
          </div>
          <div class="block-actions">
            <button class="mini" @click="openVideoNotes">查看全部</button>
            <button class="mini" @click="takeNote">继续记笔记</button>
          </div>
        </div>

        <div v-if="notesLoading" class="setting-hint">正在加载本视频笔记…</div>
        <div v-else-if="videoNotes.length === 0" class="block-placeholder">当前视频还没有笔记，建议从关键知识点开始记录。</div>
        <div v-else class="note-preview-list">
          <button
            v-for="note in videoNotes"
            :key="note.id"
            class="note-preview-card"
            @click="openNote(note.id)"
          >
            <div class="note-preview-card__title">{{ note.title || '未命名笔记' }}</div>
            <div class="note-preview-card__excerpt">{{ buildNoteExcerpt(note.content) }}</div>
            <div class="note-preview-card__meta">
              <span v-if="Array.isArray(note.timestamps) && note.timestamps.length > 0">
                {{ formatNoteTimestampSummary(note.timestamps) }}
              </span>
              <span>{{ formatMetaTime(note.updated_at || note.created_at) }}</span>
            </div>
          </button>
        </div>
      </div>

      <div class="actions">
        <button class="btn" @click="startProcess" :disabled="processDisabled">开始处理</button>
        <button class="btn btn--primary" @click="play" :disabled="!canOpenPlayerWhileProcessing">{{ playLabel }}</button>
        <button class="btn" @click="qa">问答</button>
        <button class="btn" @click="takeNote">记笔记</button>
      </div>

      <button v-if="canRetry" class="retry" @click="retryProcess" :disabled="retrying || autoStarting">
        {{ retrying ? '重试中…' : '失败后一键重试' }}
      </button>

      <button class="danger" @click="remove" :disabled="deleteDisabled">删除视频</button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { shouldUseMockApi } from '@/config'
import { createNote, getNotes, updateNote } from '@/api/note'
import { deleteVideo, generateVideoSummary, generateVideoTags, getVideo, getVideoProcessingOptions, getVideoStatus, processVideo } from '@/api/video'
import WhisperModelPicker from '@/components/WhisperModelPicker.vue'
import { OFFLINE_QUEUE_EVENT_NAME, getPendingOfflineTasks } from '@/services/offlineQueue'
import {
  buildProcessPayload,
  getProcessingSettings,
  getWhisperModelOptions,
  saveProcessingSettings,
  saveWhisperModelCatalog,
  summaryStyleLabel,
  whisperModelLabel
} from '@/services/processingSettings'
import {
  canAutoStartVideoProcessing,
  canRetryVideoProcessing,
  createFixedIntervalPoller,
  isActiveVideoStatus,
  isCompletedVideoStatus,
  normalizeVideoStatus,
  videoStatusText,
  videoStatusTone
} from '@/services/videoStatus'

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id)

const loading = ref(false)
const error = ref('')
const video = ref(null)
const offlineTaskCount = ref(0)
const statusInfo = ref({ status: '', progress: 0, current_step: '' })
const autoStarting = ref(false)
const retrying = ref(false)
const summaryGenerating = ref(false)
const tagGenerating = ref(false)
const summaryImporting = ref(false)
const notesLoading = ref(false)
const videoNotes = ref([])
const processingSettings = ref(getProcessingSettings())
const whisperModelOptions = ref(getWhisperModelOptions())

let statusPoller = null
const usingMockGateway = computed(() => shouldUseMockApi())

const statusValue = computed(() => statusInfo.value.status || video.value?.status || '')
const progressValue = computed(() => Number(statusInfo.value.progress ?? 0) || 0)
const stepValue = computed(() => statusInfo.value.current_step || '')
const activeModelValue = computed(
  () => statusInfo.value.effective_model || statusInfo.value.requested_model || video.value?.effective_model || video.value?.requested_model || ''
)
const activeModelText = computed(() => {
  const value = String(activeModelValue.value || '').trim().toLowerCase()
  return value ? whisperModelLabel(value) : ''
})
const heroInitial = computed(() => String(video.value?.title || 'V').trim().slice(0, 1).toUpperCase() || 'V')

const isInProgress = isActiveVideoStatus
const statusText = videoStatusText

const canRetry = computed(() => canRetryVideoProcessing(statusValue.value))
const canOpenPlayerWhileProcessing = computed(() => {
  const normalizedStatus = normalizeVideoStatus(statusValue.value)
  return Boolean(video.value?.filepath) && normalizedStatus !== 'downloading'
})
const playLabel = computed(() => (isInProgress(statusValue.value) ? '播放原视频' : '播放'))
const tagList = computed(() => (Array.isArray(video.value?.tags) ? video.value.tags : []))
const canShowAnalysisBlock = computed(
  () => Boolean(video.value) && (normalizeVideoStatus(statusValue.value) === 'completed' || Boolean(video.value?.summary) || tagList.value.length > 0)
)
const canGenerateSummary = computed(() => normalizeVideoStatus(statusValue.value) === 'completed')
const canGenerateTags = computed(() => normalizeVideoStatus(statusValue.value) === 'completed' && Boolean(video.value?.summary))
const canImportSummary = computed(
  () => Boolean(normalizeText(video.value?.summary)) && !summaryGenerating.value && !tagGenerating.value && !summaryImporting.value
)
const summaryStyleText = computed(() => `${summaryStyleLabel(processingSettings.value.summaryStyle)}风格`)
const processDisabled = computed(
  () => autoStarting.value || retrying.value || ['processing', 'downloading'].includes(normalizeVideoStatus(statusValue.value))
)
const deleteDisabled = computed(
  () => autoStarting.value || retrying.value || ['processing', 'downloading'].includes(normalizeVideoStatus(statusValue.value))
)

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

const normalizeText = (value) => String(value || '').trim()

const badgeClass = (status) => {
  return videoStatusTone(status)
}

const refreshWhisperModelOptions = async () => {
  try {
    const res = await getVideoProcessingOptions()
    const catalog = saveWhisperModelCatalog(res?.data || {})
    whisperModelOptions.value = catalog.options
    processingSettings.value = saveProcessingSettings(processingSettings.value)
  } catch {
    whisperModelOptions.value = getWhisperModelOptions()
    processingSettings.value = saveProcessingSettings(processingSettings.value)
  }
}

const heroClass = computed(() => {
  const tone = videoStatusTone(statusValue.value)
  if (tone === 'ok') return 'hero-shell--ok'
  if (tone === 'bad') return 'hero-shell--bad'
  if (tone === 'warn') return 'hero-shell--warn'
  return 'hero-shell--idle'
})

const fetchStatus = async () => {
  const previousStatus = normalizeVideoStatus(statusValue.value)
  const res = await getVideoStatus(id.value)
  const p = res.data || {}
  statusInfo.value = {
    status: p.status || p.data?.status || '',
    progress: p.progress ?? p.data?.progress ?? 0,
    current_step: p.current_step || p.data?.current_step || '',
    requested_model: p.requested_model || p.data?.requested_model || '',
    effective_model: p.effective_model || p.data?.effective_model || '',
    requested_language: p.requested_language || p.data?.requested_language || ''
  }
  const nextStatus = normalizeVideoStatus(statusInfo.value.status)
  if (previousStatus && isActiveVideoStatus(previousStatus) && !isActiveVideoStatus(nextStatus)) {
    const detailRes = await getVideo(id.value)
    video.value = normalizeVideo(detailRes.data)
  }
}

const clearAutoStartQuery = async () => {
  if (!route.query?.autostart) return
  const query = { ...route.query }
  delete query.autostart
  await router.replace({ path: route.path, query })
}

const shouldAutoStart = () => String(route.query?.autostart || '') === '1'

const tryAutoStartProcessing = async () => {
  if (!shouldAutoStart() || autoStarting.value || retrying.value) return

  const currentStatus = normalizeVideoStatus(statusValue.value)
  if (isCompletedVideoStatus(currentStatus)) {
    await clearAutoStartQuery()
    return
  }

  if (isActiveVideoStatus(currentStatus)) {
    return
  }

  if (!canAutoStartVideoProcessing(currentStatus)) {
    await clearAutoStartQuery()
    return
  }

  autoStarting.value = true
  error.value = ''
  let attempted = false
  try {
    attempted = true
    processingSettings.value = getProcessingSettings()
    await processVideo(id.value, buildProcessPayload(processingSettings.value))
    await fetchStatus()
    startPollingIfNeeded()
  } catch (e) {
    error.value = extractErrorMessage(e, '自动开始处理失败')
  } finally {
    autoStarting.value = false
    if (attempted) await clearAutoStartQuery()
  }
}

const ensureStatusPoller = () => {
  if (statusPoller) return statusPoller

  statusPoller = createFixedIntervalPoller({
    intervalMs: 2000,
    shouldPoll: () => isActiveVideoStatus(statusValue.value) || shouldAutoStart(),
    onTick: async () => {
      try {
        await fetchStatus()
        await tryAutoStartProcessing()
        if (!isActiveVideoStatus(statusValue.value) && !shouldAutoStart()) {
          statusPoller.stop()
        }
      } catch {
        // ignore transient polling failures
      }
    }
  })

  return statusPoller
}

const startPollingIfNeeded = () => {
  const poller = ensureStatusPoller()
  if (!isActiveVideoStatus(statusValue.value) && !shouldAutoStart()) {
    poller.stop()
    return
  }
  poller.start()
}

const reloadOfflineTaskCount = async () => {
  try {
    const tasks = await getPendingOfflineTasks()
    offlineTaskCount.value = tasks.length
  } catch {
    offlineTaskCount.value = 0
  }
}

const normalizeVideo = (payload) => {
  const current = payload?.video || payload?.data || payload || null
  if (!current) return null
  return {
    ...current,
    tags: Array.isArray(current.tags) ? current.tags : [],
    requested_model: String(current.requested_model || '').trim().toLowerCase(),
    effective_model: String(current.effective_model || current.requested_model || '').trim().toLowerCase()
  }
}

const normalizeNoteList = (payload) => {
  const list = payload?.notes || payload?.items || payload?.data || payload || []
  return Array.isArray(list) ? list : []
}

const normalizeNote = (payload) => payload?.note || payload?.data || payload || null
const loadVideoNotes = async () => {
  notesLoading.value = true
  try {
    const response = await getNotes({ video_id: Number(id.value) })
    const list = normalizeNoteList(response?.data)
    videoNotes.value = list.slice(0, 3)
  } catch {
    videoNotes.value = []
  } finally {
    notesLoading.value = false
  }
}

const reload = async () => {
  loading.value = true
  error.value = ''
  try {
    await refreshWhisperModelOptions()
    processingSettings.value = getProcessingSettings()
    const res = await getVideo(id.value)
    video.value = normalizeVideo(res.data)
    if (video.value?.processing_origin === 'ios_offline' && video.value?.task_id) {
      await router.replace(`/local-transcripts/${video.value.task_id}`)
      return
    }
    await loadVideoNotes()
    await fetchStatus()
    startPollingIfNeeded()
    await tryAutoStartProcessing()
  } catch (e) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const selectProcessingModel = (model) => {
  if (processDisabled.value) return
  processingSettings.value = saveProcessingSettings({
    ...processingSettings.value,
    model
  })
}

const startProcess = async () => {
  try {
    processingSettings.value = getProcessingSettings()
    await processVideo(id.value, buildProcessPayload(processingSettings.value))
    await reload()
  } catch (e) {
    error.value = extractErrorMessage(e, '提交失败')
  }
}

const retryProcess = async () => {
  if (!canRetry.value || retrying.value || autoStarting.value) return
  retrying.value = true
  error.value = ''
  try {
    processingSettings.value = getProcessingSettings()
    await processVideo(id.value, buildProcessPayload(processingSettings.value))
    await reload()
  } catch (e) {
    error.value = extractErrorMessage(e, '重试失败')
  } finally {
    retrying.value = false
  }
}

const play = () => {
  if (!canOpenPlayerWhileProcessing.value) return
  router.push(`/player/${id.value}`)
}

const createSummary = async () => {
  if (!canGenerateSummary.value || summaryGenerating.value || tagGenerating.value) return
  summaryGenerating.value = true
  error.value = ''
  try {
    processingSettings.value = getProcessingSettings()
    await generateVideoSummary(id.value, { style: processingSettings.value.summaryStyle })
    await reload()
  } catch (e) {
    error.value = extractErrorMessage(e, '生成摘要失败')
  } finally {
    summaryGenerating.value = false
  }
}

const createTags = async () => {
  if (!canGenerateTags.value || summaryGenerating.value || tagGenerating.value) return
  tagGenerating.value = true
  error.value = ''
  try {
    await generateVideoTags(id.value, { max_tags: 6 })
    await reload()
  } catch (e) {
    error.value = extractErrorMessage(e, '提取标签失败')
  } finally {
    tagGenerating.value = false
  }
}

const buildSummaryNotePayload = () => ({
  title: normalizeText(video.value?.title) || '未命名视频',
  content: normalizeText(video.value?.summary),
  note_type: 'summary',
  video_id: Number(id.value),
  tags: tagList.value.join(',')
})

const findSummaryNote = async () => {
  const response = await getNotes({ video_id: Number(id.value), per_page: 100 })
  const currentTitle = normalizeText(video.value?.title) || '未命名视频'
  const summaryNotes = normalizeNoteList(response?.data).filter(
    (item) => String(item?.note_type || 'text') === 'summary' && Number(item?.video_id || 0) === Number(id.value)
  )
  return summaryNotes.find((item) => normalizeText(item?.title) === currentTitle) || summaryNotes[0] || null
}

const importSummaryToNote = async () => {
  if (!canImportSummary.value) return
  if (usingMockGateway.value) {
    error.value = '当前未连接真实后端，摘要导入不会写入数据库；请先配置 API Base 并关闭 UI-only。'
    return
  }

  summaryImporting.value = true
  error.value = ''

  try {
    const payload = buildSummaryNotePayload()
    const existing = await findSummaryNote()
    let noteId = ''
    let noteAction = 'created'

    if (existing?.id) {
      const response = await updateNote(existing.id, payload)
      const updated = normalizeNote(response?.data)
      noteId = String(updated?.id || existing.id)
      noteAction = 'updated'
    } else {
      const response = await createNote(payload)
      const created = normalizeNote(response?.data)
      noteId = String(created?.id || '')
    }

    const query = {
      noteAction,
      videoId: String(id.value)
    }
    if (noteId) query.noteId = noteId

    await router.push({ path: '/notes', query })
  } catch (e) {
    error.value = extractErrorMessage(e, '导入摘要失败')
  } finally {
    summaryImporting.value = false
  }
}

const qa = () => router.push({ path: '/qa', query: { videoId: String(id.value) } })

const openVideoNotes = () => router.push({ path: '/notes', query: { videoId: String(id.value) } })

const openNote = (noteId) => router.push(`/notes/${noteId}`)
const takeNote = () => {
  router.push({
    path: '/notes/new',
    query: {
      videoId: String(id.value),
      videoTitle: String(video.value?.title || '')
    }
  })
}

const buildNoteExcerpt = (content) => {
  const text = String(content || '').replace(/\s+/g, ' ').trim()
  if (!text) return '暂无笔记正文。'
  return text.length > 66 ? `${text.slice(0, 66)}…` : text
}

const formatNoteTimestampSummary = (timestamps) => {
  const sorted = [...timestamps].sort((a, b) => Number(a?.time_seconds || 0) - Number(b?.time_seconds || 0))
  const first = Number(sorted[0]?.time_seconds || 0)
  const minutes = Math.floor(first / 60)
  const seconds = Math.floor(first % 60)
  const head = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  return sorted.length > 1 ? `${head} 等 ${sorted.length} 个时间点` : `${head} 重点时间点`
}

const formatMetaTime = (value) => {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleDateString()
}
const remove = async () => {
  const ok = window.confirm('确认删除该视频？')
  if (!ok) return
  try {
    await deleteVideo(id.value)
    router.replace('/videos')
  } catch (e) {
    error.value = e?.message || '删除失败'
  }
}

onMounted(async () => {
  window.addEventListener(OFFLINE_QUEUE_EVENT_NAME, reloadOfflineTaskCount)
  await reloadOfflineTaskCount()
  await reload()
})

onUnmounted(() => {
  statusPoller?.stop()
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
  display: grid;
  grid-template-columns: 40px 1fr 56px;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.topbar-title {
  text-align: center;
  font-weight: 900;
  min-width: 0;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.back {
  border: 0;
  background: var(--card);
  border-radius: 12px;
  height: 36px;
  width: 40px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  font-size: 22px;
  line-height: 1;
}

.link {
  border: 0;
  background: transparent;
  color: var(--primary);
  font-weight: 900;
  justify-self: end;
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

.skeleton {
  display: grid;
  gap: 12px;
}

.sk-hero {
  height: 180px;
  border-radius: var(--radius);
  background: linear-gradient(90deg, #f3f4f6, #e5e7eb, #f3f4f6);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
}

.sk-line {
  height: 16px;
  border-radius: 999px;
  background: linear-gradient(90deg, #f3f4f6, #e5e7eb, #f3f4f6);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
}

@keyframes shimmer {
  0% { background-position: 0% 0; }
  100% { background-position: 200% 0; }
}

.empty {
  color: var(--muted);
}

.card {
  background: var(--card);
  border-radius: var(--radius);
  padding: 14px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
}

.hero {
  border-radius: 14px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.05);
  min-height: 180px;
}

.hero-shell {
  position: relative;
  min-height: 180px;
  padding: 18px;
  display: grid;
  align-content: space-between;
  gap: 14px;
  color: #fff;
  overflow: hidden;
}

.hero-shell::before,
.hero-shell::after {
  content: '';
  position: absolute;
  border-radius: 999px;
  opacity: 0.26;
}

.hero-shell::before {
  width: 156px;
  height: 156px;
  top: -44px;
  right: -30px;
  background: rgba(255, 255, 255, 0.2);
}

.hero-shell::after {
  width: 112px;
  height: 112px;
  left: -24px;
  bottom: -26px;
  background: rgba(255, 255, 255, 0.14);
}

.hero-shell--idle {
  background: linear-gradient(145deg, #8b799d, #665775);
}

.hero-shell--warn {
  background: linear-gradient(145deg, #8f73ba, #5f477e);
}

.hero-shell--ok {
  background: linear-gradient(145deg, #b79dd5, #6b5b84);
}

.hero-shell--bad {
  background: linear-gradient(145deg, #c2410c, #991b1b);
}

.hero-shell__badge,
.hero-shell__initial,
.hero-shell__caption {
  position: relative;
  z-index: 1;
}

.hero-shell__badge {
  justify-self: start;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.08em;
}

.hero-shell__initial {
  font-size: 66px;
  font-weight: 900;
  line-height: 1;
}

.hero-shell__caption {
  max-width: min(100%, 260px);
  font-size: 12px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.94);
  overflow-wrap: anywhere;
  word-break: break-word;
}

.title {
  margin: 12px 0 0;
  font-size: 16px;
  font-weight: 900;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.meta {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
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
  margin-top: 10px;
  height: 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.bar {
  height: 100%;
  background: linear-gradient(90deg, #a792bc, #7f698f);
}

.inline-tip {
  margin-top: 8px;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}

.inline-tip--queue {
  margin-bottom: 2px;
}

.block {
  margin-top: 14px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  padding-top: 14px;
  display: grid;
  gap: 10px;
}

.block-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.block-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.block-title {
  font-weight: 900;
  font-size: 13px;
}

.block-body {
  margin-top: 8px;
  color: #374151;
  font-size: 13px;
  line-height: 1.6;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.block-body--prewrap {
  white-space: pre-wrap;
}

.block-placeholder {
  border-radius: 14px;
  padding: 12px;
  background: var(--ok-bg);
  color: var(--ok-text);
  font-size: 13px;
  font-weight: 700;
  line-height: 1.6;
}

.setting-hint {
  font-size: 12px;
  color: var(--muted);
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.note-preview-list {
  display: grid;
  gap: 10px;
}

.note-preview-card {
  border: 1px solid rgba(32, 42, 55, 0.08);
  border-radius: 16px;
  background: #fff;
  padding: 12px;
  text-align: left;
  display: grid;
  gap: 8px;
}

.note-preview-card__title {
  font-size: 13px;
  font-weight: 900;
  color: #0f172a;
}

.note-preview-card__excerpt {
  font-size: 12px;
  line-height: 1.6;
  color: #475569;
  overflow-wrap: anywhere;
}

.note-preview-card__meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 11px;
  color: #64748b;
  font-weight: 700;
}

.tag-pill {
  border-radius: 999px;
  padding: 6px 10px;
  background: var(--ok-bg);
  color: var(--ok-text);
  font-weight: 800;
  font-size: 12px;
}

.mini {
  border: 0;
  border-radius: 12px;
  padding: 8px 10px;
  background: var(--ok-bg);
  color: var(--ok-text);
  font-weight: 800;
  font-size: 12px;
}

.mini:disabled {
  opacity: 0.6;
}

.mini--primary {
  background: linear-gradient(135deg, #5f477e, #8f73ba);
  color: #fff;
}

.actions {
  margin-top: 14px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.btn {
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: #fff;
  border-radius: 14px;
  padding: 10px 10px;
  font-weight: 900;
  font-size: 12px;
  min-width: 0;
  text-align: center;
}

.btn--primary {
  border: 0;
  color: #fff;
  background: linear-gradient(135deg, #a792bc, #7f698f);
}

.btn:disabled,
.danger:disabled {
  opacity: 0.5;
}

.retry {
  margin-top: 12px;
  width: 100%;
  border: 1px solid var(--lilac-border);
  background: var(--lilac-bg);
  color: var(--lilac-text);
  border-radius: 14px;
  padding: 12px;
  font-weight: 900;
}

.retry:disabled {
  opacity: 0.6;
}

.danger {
  margin-top: 12px;
  width: 100%;
  border: 0;
  background: var(--lilac-bg);
  color: var(--lilac-text);
  border-radius: 14px;
  padding: 12px;
  font-weight: 900;
}

@media (max-width: 420px) {
  .topbar {
    grid-template-columns: 40px minmax(0, 1fr) minmax(52px, auto);
  }

  .actions {
    grid-template-columns: 1fr;
  }

  .hero-shell__caption {
    max-width: 100%;
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
  padding: 10px 12px;
  border-radius: 16px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: rgba(242, 235, 248, 0.92);
  box-shadow: 0 10px 20px rgba(101, 87, 117, 0.08);
}

.card {
  margin-top: 12px;
  border-radius: 24px;
  border: 1px solid rgba(32, 42, 55, 0.09);
  background: linear-gradient(180deg, #ffffff, #f0e8f7);
  box-shadow: 0 16px 30px rgba(101, 87, 117, 0.1);
  padding: 16px;
}

.hero,
.hero-shell {
  height: 200px;
}

.title {
  font-size: 19px;
  line-height: 1.35;
}

.block {
  border-top-color: rgba(32, 42, 55, 0.08);
}

.btn {
  border-radius: 16px;
  padding: 11px 10px;
}

.btn--primary {
  background: linear-gradient(135deg, #8b799d, #a48eb5);
}
</style>
