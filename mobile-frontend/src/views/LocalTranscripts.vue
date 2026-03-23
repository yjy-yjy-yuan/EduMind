<template>
  <div class="page">
    <header class="topbar">
      <h2>本地转录</h2>
      <button class="link" @click="reload" :disabled="loading">{{ loading ? '加载中…' : '刷新' }}</button>
    </header>

    <div class="filters">
      <button
        v-for="item in FILTERS"
        :key="item.value"
        class="filter"
        :class="{ 'filter--active': statusFilter === item.value }"
        @click="statusFilter = item.value"
      >
        {{ item.label }}
      </button>
    </div>

    <div v-if="error" class="alert alert--bad">
      <span>{{ error }}</span>
      <button class="link" @click="reload">重试</button>
    </div>

    <div v-else-if="loading && transcripts.length === 0" class="skeleton">
      <div v-for="i in 4" :key="i" class="sk-card"></div>
    </div>

    <div v-else-if="filteredTranscripts.length === 0" class="empty">
      {{ emptyText }}
      <button class="link" @click="router.push('/upload')">去上传页</button>
    </div>

    <div v-else class="list">
      <div v-for="item in filteredTranscripts" :key="item.taskId" class="card">
        <button class="card-main" @click="openDetail(item.taskId)">
          <div class="row">
            <div class="title">{{ item.fileName || '本地视频' }}</div>
            <i class="arrow">›</i>
          </div>
          <div class="meta">
            <span class="badge" :class="badgeClass(item.status)">{{ statusText(item.status) }}</span>
            <span class="muted">{{ readableSize(item.fileSize) }}</span>
          </div>
          <div class="muted">{{ localeLabel(item.locale) }} · {{ engineLabel(item.engine) }}</div>
          <div class="muted">{{ formatTimeText(item.updatedAt || item.createdAt) }}</div>
          <div v-if="showProgress(item.status)" class="progress">
            <div class="bar" :style="{ width: `${Math.max(0, Math.min(100, Number(item.progress || 0)))}%` }"></div>
          </div>
        </button>
        <div class="card-actions">
          <button class="mini" @click="openDetail(item.taskId)">查看详情</button>
          <button class="mini mini--warn" @click="removeItem(item.taskId)" :disabled="deletingIds[item.taskId]">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NATIVE_OFFLINE_TRANSCRIPTS_EVENT_NAME,
  deleteNativeOfflineTranscript,
  listNativeOfflineTranscripts
} from '@/services/nativeOfflineTranscripts'
import { nativeLocaleLabel } from '@/services/processingSettings'
import { normalizeVideoStatus, videoStatusText, videoStatusTone } from '@/services/videoStatus'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const transcripts = ref([])
const statusFilter = ref('all')
const deletingIds = ref({})

const FILTERS = [
  { value: 'all', label: '全部' },
  { value: 'completed', label: '已完成' },
  { value: 'active', label: '进行中' },
  { value: 'failed', label: '失败' }
]

const statusText = videoStatusText

const filteredTranscripts = computed(() => {
  if (statusFilter.value === 'all') return transcripts.value
  if (statusFilter.value === 'active') {
    return transcripts.value.filter((item) =>
      ['preparing', 'extracting', 'transcribing'].includes(normalizeVideoStatus(item.status))
    )
  }
  return transcripts.value.filter((item) => normalizeVideoStatus(item.status) === statusFilter.value)
})

const emptyText = computed(() => {
  if (statusFilter.value === 'completed') return '暂无已完成的本地离线转录结果。'
  if (statusFilter.value === 'active') return '暂无进行中的本地离线转录任务。'
  if (statusFilter.value === 'failed') return '暂无失败的本地离线转录任务。'
  return '暂无本地离线转录结果。'
})

const badgeClass = (status) => {
  const tone = videoStatusTone(status)
  if (tone === 'ok') return 'ok'
  if (tone === 'bad') return 'bad'
  if (tone === 'warn') return 'warn'
  return 'info'
}

const showProgress = (status) => ['preparing', 'extracting', 'transcribing'].includes(normalizeVideoStatus(status))

const readableSize = (size) => {
  const n = Number(size || 0)
  if (!n) return '0 B'
  if (n >= 1024 * 1024 * 1024) return `${(n / (1024 * 1024 * 1024)).toFixed(2)} GB`
  if (n >= 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(2)} MB`
  if (n >= 1024) return `${(n / 1024).toFixed(2)} KB`
  return `${n} B`
}

const localeLabel = (locale) => nativeLocaleLabel(locale)

const engineLabel = (engine) => {
  if (String(engine || '').trim() === 'apple_speech_on_device') return 'Apple 端侧识别'
  return 'iOS 原生识别'
}

const formatTimeText = (isoText) => {
  if (!isoText) return ''
  try {
    return new Date(isoText).toLocaleString()
  } catch {
    return ''
  }
}

const reload = async () => {
  loading.value = true
  error.value = ''
  try {
    transcripts.value = await listNativeOfflineTranscripts()
  } catch (e) {
    error.value = e?.message || '加载本地离线转录结果失败'
  } finally {
    loading.value = false
  }
}

const openDetail = (taskId) => {
  const id = String(taskId || '').trim()
  if (!id) return
  router.push(`/local-transcripts/${id}`)
}

const removeItem = async (taskId) => {
  const id = String(taskId || '').trim()
  if (!id) return
  deletingIds.value = { ...deletingIds.value, [id]: true }
  error.value = ''
  try {
    await deleteNativeOfflineTranscript(id)
    await reload()
  } catch (e) {
    error.value = e?.message || '删除本地离线转录结果失败'
  } finally {
    const next = { ...deletingIds.value }
    delete next[id]
    deletingIds.value = next
  }
}

const handleStoreUpdate = async () => {
  await reload()
}

onMounted(async () => {
  window.addEventListener(NATIVE_OFFLINE_TRANSCRIPTS_EVENT_NAME, handleStoreUpdate)
  await reload()
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
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 10px;
  gap: 8px;
}

.topbar h2 {
  margin: 0;
  font-size: 16px;
}

.link {
  border: 0;
  background: transparent;
  color: var(--primary);
  font-weight: 900;
}

.filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.filter {
  border: 1px solid var(--border);
  background: #fff;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 800;
  color: var(--text);
}

.filter--active {
  border-color: rgba(16, 185, 129, 0.28);
  background: rgba(16, 185, 129, 0.1);
  color: #065f46;
}

.alert {
  padding: 10px 12px;
  border-radius: 12px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  font-weight: 700;
  margin-bottom: 10px;
}

.alert--bad {
  background: rgba(239, 68, 68, 0.1);
  color: #b91c1c;
}

.skeleton {
  display: grid;
  gap: 10px;
}

.sk-card {
  height: 92px;
  border-radius: var(--radius);
  background: linear-gradient(90deg, #f3f4f6, #e5e7eb, #f3f4f6);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
}

.empty {
  display: grid;
  gap: 8px;
  justify-items: start;
  color: var(--muted);
  padding: 16px 0;
}

.list {
  display: grid;
  gap: 10px;
}

.card {
  background: var(--card);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.card-main {
  width: 100%;
  border: 0;
  background: transparent;
  padding: 14px;
  text-align: left;
  display: grid;
  gap: 8px;
}

.card-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 0 14px 14px;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.title {
  font-size: 14px;
  font-weight: 900;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.arrow {
  font-style: normal;
  color: var(--muted);
}

.meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.badge {
  border-radius: 999px;
  padding: 4px 9px;
  font-size: 12px;
  font-weight: 800;
}

.badge.ok {
  background: rgba(34, 197, 94, 0.12);
  color: #15803d;
}

.badge.bad {
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
}

.badge.warn {
  background: rgba(245, 158, 11, 0.14);
  color: #92400e;
}

.badge.info {
  background: rgba(99, 102, 241, 0.12);
  color: #3730a3;
}

.muted {
  font-size: 12px;
  color: var(--muted);
  overflow-wrap: anywhere;
  word-break: break-word;
}

.progress {
  height: 6px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.bar {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #14b8a6);
}

.mini {
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 800;
  border: 1px solid var(--border);
  background: #fff;
}

.mini--warn {
  color: #b91c1c;
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
