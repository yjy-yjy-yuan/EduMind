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
      <div class="meta-head">
        <div>
          <h2 class="title">{{ transcript.fileName || '本地视频' }}</h2>
          <div class="muted">
            {{ readableSize(transcript.fileSize) }} · {{ localeLabel }} · {{ engineLabel }}
          </div>
          <div class="muted">{{ updatedText }}</div>
        </div>
        <span class="status" :class="statusClass(transcript.status)">{{ statusText(transcript.status) }}</span>
      </div>

      <div v-if="showProgress" class="progress-block">
        <div class="muted">{{ transcript.progress }}% · {{ transcript.currentStep || '处理中' }}</div>
        <div class="progress">
          <div class="bar" :style="{ width: `${transcript.progress}%` }"></div>
        </div>
      </div>

      <div v-if="transcript.errorMessage" class="alert alert--bad">{{ transcript.errorMessage }}</div>

      <div class="block">
        <div class="block-head">
          <div class="block-title">转录文本</div>
          <button class="mini" @click="copyTranscript" :disabled="!transcript.transcriptText || copying">
            {{ copying ? '复制中…' : '复制文本' }}
          </button>
        </div>
        <pre v-if="transcript.transcriptText" class="transcript-text">{{ transcript.transcriptText }}</pre>
        <div v-else class="empty empty--compact">当前还没有可用文本。</div>
      </div>

      <div v-if="segmentCount > 0" class="muted">分段数量：{{ segmentCount }}</div>

      <button class="danger" @click="removeTranscript" :disabled="deleting">
        {{ deleting ? '删除中…' : '删除本地结果' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NATIVE_OFFLINE_TRANSCRIPTS_EVENT_NAME,
  deleteNativeOfflineTranscript,
  getNativeOfflineTranscript
} from '@/services/nativeOfflineTranscripts'
import { nativeLocaleLabel } from '@/services/processingSettings'
import { normalizeVideoStatus, videoStatusText, videoStatusTone } from '@/services/videoStatus'

const route = useRoute()
const router = useRouter()

const taskId = computed(() => String(route.params.taskId || '').trim())
const loading = ref(false)
const deleting = ref(false)
const copying = ref(false)
const error = ref('')
const transcript = ref(null)

const statusText = videoStatusText
const showProgress = computed(() => {
  const status = normalizeVideoStatus(transcript.value?.status)
  return ['preparing', 'extracting', 'transcribing'].includes(status)
})
const segmentCount = computed(() => (Array.isArray(transcript.value?.segments) ? transcript.value.segments.length : 0))
const localeLabel = computed(() => nativeLocaleLabel(transcript.value?.locale || ''))
const engineLabel = computed(() =>
  String(transcript.value?.engine || '').trim() === 'apple_speech_on_device' ? 'Apple 端侧识别' : 'iOS 原生识别'
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

const readableSize = (size) => {
  const n = Number(size || 0)
  if (!n) return '0 B'
  if (n >= 1024 * 1024 * 1024) return `${(n / (1024 * 1024 * 1024)).toFixed(2)} GB`
  if (n >= 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(2)} MB`
  if (n >= 1024) return `${(n / 1024).toFixed(2)} KB`
  return `${n} B`
}

const statusClass = (status) => {
  const tone = videoStatusTone(status)
  if (tone === 'ok') return 'status--ok'
  if (tone === 'bad') return 'status--bad'
  if (tone === 'warn') return 'status--warn'
  return 'status--info'
}

const reload = async () => {
  if (!taskId.value || loading.value) return
  loading.value = true
  error.value = ''

  try {
    transcript.value = await getNativeOfflineTranscript(taskId.value)
  } catch (e) {
    error.value = e?.message || '加载本地离线转录结果失败'
  } finally {
    loading.value = false
  }
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
    router.replace('/upload')
  } catch (e) {
    error.value = e?.message || '删除本地结果失败'
  } finally {
    deleting.value = false
  }
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
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}

.topbar-title {
  font-size: 15px;
  font-weight: 900;
}

.back,
.link {
  border: 0;
  background: transparent;
  color: var(--primary);
  font-weight: 900;
}

.card {
  background: var(--card);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  padding: 14px;
  display: grid;
  gap: 14px;
}

.meta-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.title {
  margin: 0 0 6px;
  font-size: 17px;
  font-weight: 900;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.muted {
  font-size: 12px;
  color: var(--muted);
  overflow-wrap: anywhere;
  word-break: break-word;
}

.status {
  border-radius: 999px;
  padding: 4px 9px;
  font-size: 12px;
  font-weight: 800;
}

.status--ok {
  background: rgba(34, 197, 94, 0.12);
  color: #15803d;
}

.status--bad {
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
}

.status--warn {
  background: rgba(245, 158, 11, 0.14);
  color: #92400e;
}

.status--info {
  background: rgba(99, 102, 241, 0.12);
  color: #3730a3;
}

.progress-block {
  display: grid;
  gap: 8px;
}

.progress {
  height: 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.bar {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #14b8a6);
}

.block {
  display: grid;
  gap: 10px;
}

.block-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.block-title {
  font-size: 13px;
  font-weight: 900;
}

.mini {
  border: 1px solid var(--border);
  border-radius: 999px;
  background: #fff;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 800;
}

.transcript-text {
  margin: 0;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: rgba(15, 23, 42, 0.04);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 55vh;
  overflow: auto;
}

.alert {
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 13px;
}

.alert--bad {
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
}

.empty {
  display: grid;
  gap: 8px;
  justify-items: start;
  padding: 18px 0;
  color: var(--muted);
}

.empty--compact {
  padding: 0;
}

.skeleton {
  display: grid;
  gap: 10px;
}

.sk-hero,
.sk-line {
  border-radius: 12px;
  background: linear-gradient(90deg, rgba(226, 232, 240, 0.7), rgba(241, 245, 249, 0.95), rgba(226, 232, 240, 0.7));
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite linear;
}

.sk-hero {
  height: 120px;
}

.sk-line {
  height: 16px;
}

.danger {
  border: 0;
  border-radius: 14px;
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
  padding: 12px;
  font-weight: 900;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
