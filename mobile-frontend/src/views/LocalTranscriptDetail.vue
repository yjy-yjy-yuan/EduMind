<template>
  <div class="page">
    <header class="topbar">
      <button class="back" @click="router.back()">‹</button>
      <div class="topbar-title">本地转录详情</div>
      <button class="link" @click="reload" :disabled="loading">{{ loading ? '…' : '刷新' }}</button>
    </header>

    <div v-if="error" class="alert alert--bad">
      <span>{{ error }}</span>
      <button class="link" @click="reload">重试</button>
    </div>

    <div v-else-if="loading && !transcript" class="skeleton">
      <div class="sk-hero"></div>
      <div class="sk-line"></div>
      <div class="sk-line"></div>
    </div>

    <div v-else-if="!transcript" class="empty">
      未找到该本地离线转录结果。
      <button class="link" @click="router.push('/upload')">返回上传页</button>
    </div>

    <div v-else class="card">
      <div class="hero">
        <div v-if="canPlayLocalVideo" class="player-shell">
          <video
            :key="playerReloadKey"
            ref="videoRef"
            class="video"
            :src="localVideoSrc"
            controls
            playsinline
            webkit-playsinline
            preload="metadata"
            x-webkit-airplay="allow"
            @loadstart="handleLoadStart"
            @loadedmetadata="handleLoadedMetadata"
            @canplay="handleCanPlay"
            @playing="handlePlaying"
            @waiting="handleWaiting"
            @error="handleVideoError"
          />
        </div>
        <div v-else class="hero-shell" :class="heroClass">
          <div class="hero-shell__badge">LOCAL</div>
          <div class="hero-shell__initial">{{ heroInitial }}</div>
          <div class="hero-shell__caption">
            本地离线结果已保存在当前设备。若需要视频预览，请在 iOS 原生容器中打开该页面。
          </div>
        </div>
      </div>

      <h2 class="title">{{ transcript.fileName || '本地视频' }}</h2>

      <div class="meta">
        <span class="badge" :class="badgeClass(transcript.status)">{{ statusText(transcript.status) }}</span>
        <span class="muted">{{ readableSize(transcript.fileSize) }}</span>
        <span class="muted">{{ localeLabel }}</span>
        <span class="muted">{{ engineLabel }}</span>
        <span v-if="showProgress" class="muted">{{ transcript.progress }}% · {{ transcript.currentStep || '处理中' }}</span>
        <span v-else-if="playerStateText" class="muted">{{ playerStateText }}</span>
        <span v-if="durationText" class="muted">{{ durationText }}</span>
      </div>

      <div class="setting-hint">{{ updatedText }}</div>
      <div v-if="segmentCount > 0" class="setting-hint">分段数量：{{ segmentCount }}</div>
      <div v-if="syncHintText" class="setting-hint">{{ syncHintText }}</div>

      <div v-if="showProgress" class="progress">
        <div class="bar" :style="{ width: `${transcript.progress}%` }"></div>
      </div>

      <div v-if="playerError" class="inline-tip inline-tip--bad">{{ playerError }}</div>
      <div v-else class="inline-tip">{{ tipText }}</div>

      <div v-if="transcript.errorMessage" class="alert alert--bad">{{ transcript.errorMessage }}</div>

      <div class="block">
        <div class="block-head">
          <div class="block-title">智能摘要</div>
          <div class="block-actions">
            <button class="mini" @click="createSummary" :disabled="!canGenerateSummary || summaryGenerating">
              {{ summaryGenerating ? '生成中…' : (transcript.summary ? '重生成摘要' : '生成摘要') }}
            </button>
          </div>
        </div>
        <div class="setting-hint">
          当前摘要设置：{{ summaryStyleText }}
          <span v-if="!summaryBackendConfigured"> · 当前未配置可用后端</span>
        </div>
        <div v-if="transcript.summary" class="block-body block-body--prewrap">{{ transcript.summary }}</div>
        <div v-else-if="transcript.summaryStatus === 'generating'" class="block-placeholder">正在提取课程摘要…</div>
        <div v-else class="block-placeholder">转录完成后可在此生成课程摘要。</div>
        <div v-if="transcript.summaryErrorMessage" class="inline-tip inline-tip--bad">{{ transcript.summaryErrorMessage }}</div>
      </div>

      <div class="actions">
        <button class="btn btn--primary" @click="reloadVideo" :disabled="!canPlayLocalVideo">重新加载视频</button>
        <button class="btn" @click="copyTranscript" :disabled="!transcript.transcriptText || copying">
          {{ copying ? '复制中…' : '复制文本' }}
        </button>
        <button class="btn" @click="router.push('/local-transcripts')">返回列表</button>
      </div>

      <div class="block">
        <div class="block-head">
          <div class="block-title">转录文本</div>
        </div>
        <pre v-if="transcript.transcriptText" class="block-body block-body--prewrap transcript-text">{{ transcript.transcriptText }}</pre>
        <div v-else class="block-placeholder">当前还没有可用文本。</div>
      </div>

      <button class="danger" @click="removeTranscript" :disabled="deleting">
        {{ deleting ? '删除中…' : '删除本地结果' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { generateTranscriptSummary, hasLiveVideoBackend, syncOfflineTranscriptToVideo } from '@/api/video'
import {
  NATIVE_OFFLINE_TRANSCRIPTS_EVENT_NAME,
  deleteNativeOfflineTranscript,
  getNativeOfflineTranscript,
  saveNativeOfflineTranscript
} from '@/services/nativeOfflineTranscripts'
import { buildNativeOfflineVideoUrl, hasNativeBridge } from '@/services/nativeBridge'
import { getProcessingSettings, nativeLocaleLabel, summaryStyleLabel } from '@/services/processingSettings'
import { normalizeVideoStatus, videoStatusText, videoStatusTone } from '@/services/videoStatus'

const route = useRoute()
const router = useRouter()

const taskId = computed(() => String(route.params.taskId || '').trim())
const loading = ref(false)
const deleting = ref(false)
const copying = ref(false)
const summaryGenerating = ref(false)
const error = ref('')
const playerError = ref('')
const transcript = ref(null)
const videoRef = ref(null)
const playerReloadKey = ref(0)
const playerState = ref('准备加载本地视频')
const durationSeconds = ref(0)
const processingSettings = ref(getProcessingSettings())

const statusText = videoStatusText
const showProgress = computed(() => {
  const status = normalizeVideoStatus(transcript.value?.status)
  return ['preparing', 'extracting', 'transcribing'].includes(status)
})
const segmentCount = computed(() => (Array.isArray(transcript.value?.segments) ? transcript.value.segments.length : 0))
const localeLabel = computed(() => nativeLocaleLabel(transcript.value?.locale || ''))
const summaryBackendConfigured = computed(() => hasLiveVideoBackend())
const canGenerateSummary = computed(() => {
  const status = normalizeVideoStatus(transcript.value?.status)
  return summaryBackendConfigured.value && status === 'completed' && Boolean(String(transcript.value?.transcriptText || '').trim())
})
const summaryStyleText = computed(() => `${summaryStyleLabel(transcript.value?.summaryStyle || processingSettings.value.summaryStyle)}风格`)
const engineLabel = computed(() =>
  String(transcript.value?.engine || '').trim() === 'whisper_cpp_on_device'
    ? 'Whisper 本机离线转录'
    : (String(transcript.value?.engine || '').trim() === 'apple_speech_on_device'
        ? 'Apple 端侧识别'
        : (String(transcript.value?.engine || '').trim() === 'backend_whisper' ? 'Whisper 后端转录' : 'iOS 原生识别'))
)
const updatedText = computed(() => {
  const value = transcript.value?.updatedAt || transcript.value?.createdAt
  if (!value) return ''
  try {
    return `更新时间：${new Date(value).toLocaleString()}`
  } catch {
    return ''
  }
})
const syncHintText = computed(() => {
  const status = String(transcript.value?.syncStatus || '').trim().toLowerCase()
  if (status === 'completed' && Number(transcript.value?.syncedVideoId || 0) > 0) {
    return `已写入视频库：videoId=${transcript.value.syncedVideoId} · 来源标记=iOS 离线处理`
  }
  if (status === 'syncing') return '正在将本地离线结果写入视频库…'
  if (status === 'failed' && transcript.value?.syncErrorMessage) return `写入视频库失败：${transcript.value.syncErrorMessage}`
  return ''
})
const heroInitial = computed(() => String(transcript.value?.fileName || 'L').trim().slice(0, 1).toUpperCase() || 'L')
const heroClass = computed(() => {
  const tone = videoStatusTone(transcript.value?.status)
  if (tone === 'ok') return 'hero-shell--ok'
  if (tone === 'bad') return 'hero-shell--bad'
  if (tone === 'warn') return 'hero-shell--warn'
  return 'hero-shell--idle'
})
const canPlayLocalVideo = computed(() => hasNativeBridge() && Boolean(taskId.value))
const localVideoSrc = computed(() => (canPlayLocalVideo.value ? buildNativeOfflineVideoUrl(taskId.value) : ''))
const playerStateText = computed(() => (canPlayLocalVideo.value ? playerState.value : ''))
const durationText = computed(() => {
  const seconds = Number(durationSeconds.value || 0)
  if (!Number.isFinite(seconds) || seconds <= 0) return ''
  const total = Math.round(seconds)
  const hh = Math.floor(total / 3600)
  const mm = Math.floor((total % 3600) / 60)
  const ss = total % 60
  return hh > 0
    ? `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}`
    : `${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}`
})
const tipText = computed(() => {
  if (!canPlayLocalVideo.value) {
    return '当前页面已对齐在线详情页布局；本地视频播放仅在 iOS 原生容器中可用。'
  }
  if (playerError.value) {
    return '若本地视频仍无法播放，请确认该离线任务对应的原始视频文件仍保存在 App 本地缓存中。'
  }
  if (showProgress.value) {
    return '本地离线转录仍在进行中，当前播放器播放的是设备上的原始视频文件。'
  }
  return '当前页面播放的是 iOS 本地缓存的原始视频，不依赖后端流接口。'
})

const readableSize = (size) => {
  const n = Number(size || 0)
  if (!n) return '0 B'
  if (n >= 1024 * 1024 * 1024) return `${(n / (1024 * 1024 * 1024)).toFixed(2)} GB`
  if (n >= 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(2)} MB`
  if (n >= 1024) return `${(n / 1024).toFixed(2)} KB`
  return `${n} B`
}

const badgeClass = (status) => videoStatusTone(status)

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

const logOfflineDetail = (stage, payload = {}) => {
  try {
    console.info(`[OfflineDetail] ${stage} ${JSON.stringify(payload)}`)
  } catch {
    console.info(`[OfflineDetail] ${stage}`)
  }
}

const syncToVideoLibrary = async ({ silent = false } = {}) => {
  if (!transcript.value?.taskId || !String(transcript.value?.transcriptText || '').trim()) return
  if (!summaryBackendConfigured.value) return
  logOfflineDetail('sync-start', {
    taskId: transcript.value.taskId,
    apiBaseAvailable: summaryBackendConfigured.value,
    hasSummary: Boolean(String(transcript.value.summary || '').trim())
  })

  transcript.value = await saveNativeOfflineTranscript({
    taskId: transcript.value.taskId,
    syncStatus: 'syncing',
    syncErrorMessage: ''
  })

  try {
    const res = await syncOfflineTranscriptToVideo({
      task_id: transcript.value.taskId,
      file_name: transcript.value.fileName,
      file_ext: transcript.value.fileExt,
      file_size: transcript.value.fileSize,
      locale: transcript.value.locale,
      engine: transcript.value.engine,
      transcript_text: transcript.value.transcriptText,
      summary: transcript.value.summary || '',
      summary_style: transcript.value.summaryStyle || processingSettings.value.summaryStyle || 'study',
      tags: Array.isArray(transcript.value.tags) ? transcript.value.tags : [],
      auto_generate_tags: typeof transcript.value.autoGenerateTags === 'boolean'
        ? transcript.value.autoGenerateTags
        : Boolean(processingSettings.value.autoGenerateTags),
      segments: Array.isArray(transcript.value.segments) ? transcript.value.segments : []
    })
    const data = res?.data || {}
    logOfflineDetail('sync-success', {
      taskId: transcript.value.taskId,
      videoId: Number(data?.video?.id || data?.id || 0) || 0,
      tagCount: Array.isArray(data?.video?.tags) ? data.video.tags.length : 0
    })
    transcript.value = await saveNativeOfflineTranscript({
      taskId: transcript.value.taskId,
      fileName: data?.video?.title || transcript.value.fileName,
      tags: Array.isArray(data?.video?.tags) ? data.video.tags : transcript.value.tags,
      syncedVideoId: Number(data?.video?.id || data?.id || 0) || 0,
      syncStatus: 'completed',
      syncErrorMessage: '',
      syncUpdatedAt: new Date().toISOString()
    })
  } catch (e) {
    const messageText = extractErrorMessage(e, '写入视频库失败')
    logOfflineDetail('sync-failed', {
      taskId: transcript.value.taskId,
      error: messageText
    })
    transcript.value = await saveNativeOfflineTranscript({
      taskId: transcript.value.taskId,
      syncStatus: 'failed',
      syncErrorMessage: messageText,
      syncUpdatedAt: new Date().toISOString()
    })
    if (!silent) error.value = messageText
  }
}

const reload = async () => {
  if (!taskId.value || loading.value) return
  loading.value = true
  error.value = ''

  try {
    processingSettings.value = getProcessingSettings()
    transcript.value = await getNativeOfflineTranscript(taskId.value)
    if (
      transcript.value
      && transcript.value.summaryStatus === 'idle'
      && !transcript.value.summary
      && transcript.value.autoGenerateSummary
      && normalizeVideoStatus(transcript.value.status) === 'completed'
      && String(transcript.value.transcriptText || '').trim()
      && summaryBackendConfigured.value
    ) {
      void createSummary({ silent: true })
      return
    }
    if (
      transcript.value
      && transcript.value.summary
      && transcript.value.syncStatus === 'idle'
      && !Number(transcript.value.syncedVideoId || 0)
      && summaryBackendConfigured.value
    ) {
      void syncToVideoLibrary({ silent: true })
    }
  } catch (e) {
    error.value = e?.message || '加载本地离线转录结果失败'
  } finally {
    loading.value = false
  }
}

const createSummary = async ({ silent = false } = {}) => {
  if (!transcript.value || summaryGenerating.value) return
  const text = String(transcript.value.transcriptText || '').trim()
  if (!text) return
  if (!summaryBackendConfigured.value) {
    const messageText = '当前未配置可用后端，无法提取摘要'
    transcript.value = await saveNativeOfflineTranscript({
      taskId: transcript.value.taskId,
      summaryStatus: 'failed',
      summaryErrorMessage: messageText
    })
    if (!silent) error.value = messageText
    return
  }

  summaryGenerating.value = true
  error.value = ''
  processingSettings.value = getProcessingSettings()
  const style = processingSettings.value.summaryStyle || transcript.value.summaryStyle || 'study'

  try {
    transcript.value = await saveNativeOfflineTranscript({
      taskId: transcript.value.taskId,
      summaryStatus: 'generating',
      summaryStyle: style,
      summaryErrorMessage: ''
    })
    const res = await generateTranscriptSummary({
      title: transcript.value.fileName || '本地视频',
      transcript_text: text,
      style
    })
    const data = res?.data || {}
    transcript.value = await saveNativeOfflineTranscript({
      taskId: transcript.value.taskId,
      summary: data.summary || '',
      summaryStyle: data.style || style,
      summaryStatus: 'completed',
      summaryErrorMessage: '',
      summaryUpdatedAt: new Date().toISOString()
    })
    await syncToVideoLibrary({ silent })
  } catch (e) {
    const messageText = extractErrorMessage(e, '摘要提取失败')
    transcript.value = await saveNativeOfflineTranscript({
      taskId: transcript.value.taskId,
      summaryStatus: 'failed',
      summaryStyle: style,
      summaryErrorMessage: messageText
    })
    if (!silent) error.value = messageText
  } finally {
    summaryGenerating.value = false
  }
}

const reloadVideo = async () => {
  if (!canPlayLocalVideo.value) return
  playerError.value = ''
  durationSeconds.value = 0
  playerState.value = '准备重新加载本地视频'
  playerReloadKey.value += 1
  await nextTick()
  const element = videoRef.value
  if (!element) return
  element.pause()
  element.load()
}

const copyTranscript = async () => {
  const text = String(transcript.value?.transcriptText || '')
  if (!text || copying.value) return
  copying.value = true
  error.value = ''

  try {
    if (!navigator?.clipboard?.writeText) {
      throw new Error('当前环境不支持剪贴板复制')
    }
    await navigator.clipboard.writeText(text)
  } catch (e) {
    error.value = e?.message || '复制失败'
  } finally {
    copying.value = false
  }
}

const removeTranscript = async () => {
  if (!taskId.value || deleting.value) return
  deleting.value = true
  error.value = ''

  try {
    await deleteNativeOfflineTranscript(taskId.value)
    router.replace('/local-transcripts')
  } catch (e) {
    error.value = e?.message || '删除本地结果失败'
  } finally {
    deleting.value = false
  }
}

const handleLoadStart = () => {
  playerError.value = ''
  playerState.value = '正在请求本地视频'
}

const handleLoadedMetadata = (event) => {
  durationSeconds.value = Number(event?.target?.duration || 0)
  playerState.value = '本地视频元数据已加载'
}

const handleCanPlay = () => {
  playerState.value = '可以开始播放'
}

const handlePlaying = () => {
  playerState.value = '播放中'
}

const handleWaiting = () => {
  playerState.value = '缓冲中'
}

const handleVideoError = () => {
  playerState.value = '播放失败'
  playerError.value = '本地视频加载失败。请确认该离线任务的原始视频文件仍存在，并且当前页面运行在 iOS 原生容器中。'
}

const handleStoreUpdate = (event) => {
  const changedTaskId = String(event?.detail?.taskId || '').trim()
  if (!changedTaskId || changedTaskId !== taskId.value) return
  reload()
}

onMounted(async () => {
  await reload()
  window.addEventListener(NATIVE_OFFLINE_TRANSCRIPTS_EVENT_NAME, handleStoreUpdate)
})

onUnmounted(() => {
  window.removeEventListener(NATIVE_OFFLINE_TRANSCRIPTS_EVENT_NAME, handleStoreUpdate)
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

.player-shell {
  background: #000;
}

.video {
  display: block;
  width: 100%;
  min-height: 180px;
  max-height: 56vh;
  background: #000;
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

.setting-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--muted);
}

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

.inline-tip--bad {
  color: var(--lilac-text);
}

.actions {
  margin-top: 14px;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 10px;
}

.btn {
  border: 0;
  border-radius: 14px;
  padding: 12px 10px;
  font-weight: 900;
  background: var(--ok-bg);
  color: var(--ok-text);
}

.btn--primary {
  background: linear-gradient(135deg, #5f477e, #8f73ba);
  color: #fff;
}

.btn:disabled {
  opacity: 0.6;
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

.block-title {
  font-weight: 900;
  font-size: 13px;
}

.block-actions {
  display: flex;
  align-items: center;
  gap: 8px;
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

.mini {
  border: 0;
  border-radius: 999px;
  padding: 8px 12px;
  font-weight: 800;
  color: var(--primary);
  background: rgba(37, 99, 235, 0.08);
}

.mini:disabled {
  opacity: 0.6;
}

.transcript-text {
  max-height: 55vh;
  overflow: auto;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: rgba(15, 23, 42, 0.04);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.danger {
  margin-top: 14px;
  border: 0;
  border-radius: 14px;
  background: var(--lilac-bg);
  color: var(--lilac-text);
  padding: 12px;
  font-weight: 900;
  width: 100%;
}

@media (max-width: 420px) {
  .actions {
    grid-template-columns: 1fr;
  }
}
</style>
