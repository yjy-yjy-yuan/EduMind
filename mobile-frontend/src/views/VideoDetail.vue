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
          <div class="hero-shell__badge">{{ UI_ONLY_MODE ? 'UI ONLY' : 'LIVE' }}</div>
          <div class="hero-shell__initial">{{ heroInitial }}</div>
          <div class="hero-shell__caption">
            {{ UI_ONLY_MODE ? '当前阶段仅构建界面，封面与播放器资源后续通过预留接口接入。' : '视频预览由后端接口提供。' }}
          </div>
        </div>
      </div>

      <h2 class="title">{{ video.title || '未命名视频' }}</h2>

      <div class="meta">
        <span class="badge" :class="badgeClass(statusValue)">{{ statusText(statusValue) }}</span>
        <span v-if="autoStarting" class="muted">正在自动启动处理…</span>
        <span v-if="isInProgress(statusValue)" class="muted">{{ progressValue }}% · {{ stepValue || '处理中' }}</span>
      </div>

      <div v-if="isInProgress(statusValue)" class="progress">
        <div class="bar" :style="{ width: `${progressValue}%` }"></div>
      </div>

      <div v-if="video.summary" class="block">
        <div class="block-title">摘要</div>
        <div class="block-body">{{ video.summary }}</div>
      </div>

      <div class="actions">
        <button class="btn" @click="startProcess" :disabled="processDisabled">开始处理</button>
        <button class="btn btn--primary" @click="play" :disabled="!canPlay">播放</button>
        <button class="btn" @click="qa">问答</button>
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
import { UI_ONLY_MODE } from '@/config'
import { deleteVideo, getVideo, getVideoStatus, processVideo } from '@/api/video'

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id)

const loading = ref(false)
const error = ref('')
const video = ref(null)
const statusInfo = ref({ status: '', progress: 0, current_step: '' })
const autoStarting = ref(false)
const retrying = ref(false)

let pollTimer = null

const statusValue = computed(() => statusInfo.value.status || video.value?.status || '')
const progressValue = computed(() => Number(statusInfo.value.progress ?? 0) || 0)
const stepValue = computed(() => statusInfo.value.current_step || '')
const heroInitial = computed(() => String(video.value?.title || 'V').trim().slice(0, 1).toUpperCase() || 'V')

const isInProgress = (status) => ['processing', 'pending', 'downloading'].includes(status)

const canPlay = computed(() => ['completed', 'processed'].includes(statusValue.value))
const canRetry = computed(() => statusValue.value === 'failed')
const processDisabled = computed(
  () => autoStarting.value || retrying.value || ['processing', 'downloading'].includes(statusValue.value)
)
const deleteDisabled = computed(
  () => autoStarting.value || retrying.value || ['processing', 'downloading'].includes(statusValue.value)
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

const statusText = (status) => {
  const map = {
    uploaded: '已上传',
    pending: '排队中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
    downloading: '下载中',
    processed: '已完成'
  }
  return map[status] || (status || '未知')
}

const badgeClass = (status) => {
  if (status === 'completed' || status === 'processed') return 'ok'
  if (status === 'failed') return 'bad'
  if (isInProgress(status)) return 'warn'
  return 'info'
}

const heroClass = computed(() => {
  if (statusValue.value === 'completed' || statusValue.value === 'processed') return 'hero-shell--ok'
  if (statusValue.value === 'failed') return 'hero-shell--bad'
  if (isInProgress(statusValue.value)) return 'hero-shell--warn'
  return 'hero-shell--idle'
})

const fetchStatus = async () => {
  const res = await getVideoStatus(id.value)
  const p = res.data || {}
  statusInfo.value = {
    status: p.status || p.data?.status || '',
    progress: p.progress ?? p.data?.progress ?? 0,
    current_step: p.current_step || p.data?.current_step || ''
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
  if (!shouldAutoStart()) return

  if (isInProgress(statusValue.value) || ['completed', 'processed'].includes(statusValue.value)) {
    await clearAutoStartQuery()
    return
  }

  if (!['uploaded', 'failed'].includes(statusValue.value)) {
    await clearAutoStartQuery()
    return
  }

  autoStarting.value = true
  error.value = ''
  try {
    await processVideo(id.value)
    await fetchStatus()
    startPollingIfNeeded()
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || '自动开始处理失败'
  } finally {
    autoStarting.value = false
    await clearAutoStartQuery()
  }
}

const startPollingIfNeeded = () => {
  clearInterval(pollTimer)
  pollTimer = null
  if (!isInProgress(statusValue.value)) return
  pollTimer = setInterval(async () => {
    try {
      await fetchStatus()
      if (!isInProgress(statusValue.value)) {
        clearInterval(pollTimer)
        pollTimer = null
      }
    } catch {
      // ignore
    }
  }, 2000)
}

const normalizeVideo = (payload) => payload?.video || payload?.data || payload || null

const reload = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await getVideo(id.value)
    video.value = normalizeVideo(res.data)
    await fetchStatus()
    startPollingIfNeeded()
    await tryAutoStartProcessing()
  } catch (e) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const startProcess = async () => {
  try {
    await processVideo(id.value)
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
    await processVideo(id.value)
    await reload()
  } catch (e) {
    error.value = extractErrorMessage(e, '重试失败')
  } finally {
    retrying.value = false
  }
}

const play = () => {
  if (!canPlay.value) return
  router.push(`/player/${id.value}`)
}

const qa = () => router.push({ path: '/qa', query: { videoId: String(id.value) } })

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

onMounted(reload)
onUnmounted(() => clearInterval(pollTimer))
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
}

.alert--bad {
  background: rgba(239, 68, 68, 0.10);
  color: #b91c1c;
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
  background: linear-gradient(145deg, #1f7a8c, #0f5f70);
}

.hero-shell--warn {
  background: linear-gradient(145deg, #d97706, #b45309);
}

.hero-shell--ok {
  background: linear-gradient(145deg, #159a72, #0f766e);
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
  max-width: 260px;
  font-size: 12px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.94);
}

.title {
  margin: 12px 0 0;
  font-size: 16px;
  font-weight: 900;
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
}

.badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  white-space: nowrap;
}

.badge.ok { background: rgba(34, 197, 94, 0.12); color: #15803d; }
.badge.warn { background: rgba(245, 158, 11, 0.14); color: #92400e; }
.badge.bad { background: rgba(239, 68, 68, 0.12); color: #b91c1c; }
.badge.info { background: rgba(99, 102, 241, 0.12); color: #3730a3; }

.progress {
  margin-top: 10px;
  height: 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.bar {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
}

.block {
  margin-top: 14px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  padding-top: 14px;
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
}

.actions {
  margin-top: 14px;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 10px;
}

.btn {
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: #fff;
  border-radius: 14px;
  padding: 10px 10px;
  font-weight: 900;
  font-size: 12px;
}

.btn--primary {
  border: 0;
  color: #fff;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.btn:disabled,
.danger:disabled {
  opacity: 0.5;
}

.retry {
  margin-top: 12px;
  width: 100%;
  border: 1px solid rgba(245, 158, 11, 0.35);
  background: rgba(245, 158, 11, 0.10);
  color: #92400e;
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
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
  border-radius: 14px;
  padding: 12px;
  font-weight: 900;
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
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 20px rgba(24, 45, 73, 0.08);
}

.card {
  margin-top: 12px;
  border-radius: 24px;
  border: 1px solid rgba(32, 42, 55, 0.09);
  background: linear-gradient(180deg, #ffffff, #f9fbfd);
  box-shadow: 0 16px 30px rgba(24, 45, 73, 0.1);
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
  background: linear-gradient(135deg, #1f7a8c, #3d8da0);
}
</style>
