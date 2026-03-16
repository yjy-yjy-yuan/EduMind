<template>
  <div class="page">
    <header class="topbar">
      <button class="back" @click="router.back()">‹</button>
      <div class="topbar-title">{{ videoTitle }}</div>
      <div />
    </header>

    <div v-if="pageError" class="alert alert--bad">
      <span>{{ pageError }}</span>
      <button class="link" @click="loadVideoMeta">重试</button>
    </div>

    <div class="status-row">
      <span class="badge">{{ useMockPlayer ? 'UI ONLY' : 'LIVE' }}</span>
      <span v-if="videoStatusText" class="badge badge--status">{{ videoStatusText }}</span>
      <span class="muted">{{ playerStateText }}</span>
      <span v-if="durationText" class="muted">{{ durationText }}</span>
    </div>

    <div class="wrap">
      <div v-if="useMockPlayer" class="mock-player">
        <div class="mock-player__stage">
          <div class="mock-player__chip">UI ONLY</div>
          <div class="mock-player__play">▶</div>
          <div class="mock-player__title">{{ videoTitle }}</div>
          <div class="mock-player__desc">未配置后端地址，当前只展示播放器界面。到“我的”页面填写 FastAPI 地址后即可切换到真实播放。</div>
        </div>
        <div class="mock-player__controls">
          <span>00:00</span>
          <div class="mock-player__progress"><div class="mock-player__bar"></div></div>
          <span>12:48</span>
        </div>
      </div>
      <div v-else class="player-shell">
        <video
          ref="videoRef"
          class="video"
          :src="streamUrl"
          :poster="posterUrl"
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
        >
          <track v-if="subtitleUrl" kind="subtitles" srclang="zh" label="中文" :src="subtitleUrl" default />
        </video>
      </div>
    </div>

    <div class="tip">
      {{ tipText }}
    </div>

    <div v-if="!useMockPlayer" class="actions">
      <button class="btn btn--primary" @click="reloadPlayer">重新加载</button>
      <button class="btn" @click="router.replace(`/videos/${id}`)">返回详情</button>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { shouldUseMockApi, withBase } from '@/config'
import { getVideo } from '@/api/video'

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id)
const videoTitle = ref(`视频 ${id.value}`)
const pageError = ref('')
const playerState = ref('准备中')
const durationSeconds = ref(0)
const videoRef = ref(null)
const videoMeta = ref(null)

const useMockPlayer = computed(() => shouldUseMockApi())
const streamUrl = computed(() => withBase(`/api/videos/${id.value}/stream`))
const subtitleUrl = computed(() => (useMockPlayer.value ? '' : withBase(`/api/videos/${id.value}/subtitle?format=vtt`)))
const posterUrl = computed(() => (useMockPlayer.value ? '' : withBase(`/api/videos/${id.value}/preview`)))
const videoStatus = computed(() => String(videoMeta.value?.status || '').trim().toLowerCase())
const videoStatusText = computed(() => {
  const map = {
    uploaded: '已上传',
    pending: '排队中',
    processing: '处理中',
    completed: '已完成',
    failed: '处理失败',
    downloading: '下载中'
  }
  return map[videoStatus.value] || ''
})
const playerStateText = computed(() => playerState.value)
const durationText = computed(() => {
  const seconds = Number(durationSeconds.value || videoMeta.value?.duration || 0)
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
  if (useMockPlayer.value) {
    return '当前未连接后端。到“我的”页面填写 FastAPI 地址，或使用 iOS 原生注入的固定地址后，播放器会立即切到真实视频流。'
  }
  if (pageError.value) {
    return '播放器已切到真实接口。若仍失败，优先检查后端地址、同一 Wi‑Fi、MySQL 是否可连、以及该视频是否已处理完成。'
  }
  if (['pending', 'processing'].includes(videoStatus.value)) {
    return '当前播放原始视频文件，后台仍在处理字幕与分析结果；处理完成后无需重新上传。'
  }
  return '真机播放依赖 FastAPI 视频流接口和 iOS WebView 媒体配置，当前页面已启用原生 controls、inline 播放和字幕轨。'
})

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

const loadVideoMeta = async () => {
  pageError.value = ''
  try {
    const res = await getVideo(id.value)
    const payload = res?.data || {}
    const title = payload?.video?.title || payload?.data?.title || payload?.title
    if (title) videoTitle.value = String(title)
    videoMeta.value = payload?.video || payload?.data || payload || null
    playerState.value = useMockPlayer.value ? '等待接入真实后端' : '等待播放器加载'
  } catch (err) {
    if (!useMockPlayer.value) {
      pageError.value = extractErrorMessage(err, '视频信息加载失败，请检查后端地址和视频是否存在。')
      playerState.value = '视频信息加载失败'
    }
  }
}

const reloadPlayer = async () => {
  await loadVideoMeta()
  await nextTick()
  const element = videoRef.value
  if (!element) return
  element.pause()
  element.load()
}

const handleLoadStart = () => {
  playerState.value = '正在请求视频流'
}

const handleLoadedMetadata = (event) => {
  durationSeconds.value = Number(event?.target?.duration || 0)
  playerState.value = '视频元数据已加载'
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
  pageError.value = '视频流加载失败。请确认后端服务在线、手机与 Mac 在同一网络，并且该视频文件仍存在。'
}

onMounted(loadVideoMeta)
</script>

<style scoped>
.page {
  max-width: 720px;
  margin: 0 auto;
  padding: 16px 16px 24px;
}

.topbar {
  display: grid;
  grid-template-columns: 40px 1fr 40px;
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

.alert {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.alert--bad {
  background: rgba(239, 68, 68, 0.1);
  color: #b91c1c;
}

.status-row {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 10px;
  align-items: center;
}

.badge {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(31, 122, 140, 0.12);
  color: var(--primary-deep);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.04em;
}

.badge--status {
  background: rgba(15, 118, 110, 0.12);
  color: #0f766e;
}

.muted {
  color: var(--muted);
  font-size: 12px;
}

.wrap {
  margin-top: 12px;
  border-radius: var(--radius);
  overflow: hidden;
  background: #000;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
}

.player-shell {
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.08), transparent 35%),
    linear-gradient(180deg, #08121a, #000);
}

.mock-player {
  padding: 16px;
  background: linear-gradient(180deg, #08121a, #0f2430);
  color: #fff;
}

.mock-player__stage {
  min-height: 220px;
  border-radius: 18px;
  padding: 16px;
  display: grid;
  align-content: center;
  justify-items: center;
  text-align: center;
  gap: 10px;
  background:
    radial-gradient(circle at top right, rgba(61, 141, 160, 0.34), transparent 34%),
    linear-gradient(145deg, rgba(31, 122, 140, 0.94), rgba(11, 56, 67, 0.98));
}

.mock-player__chip {
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.08em;
}

.mock-player__play {
  width: 72px;
  height: 72px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.12);
  font-size: 28px;
  text-indent: 4px;
}

.mock-player__title {
  font-size: 18px;
  font-weight: 900;
}

.mock-player__desc {
  max-width: 260px;
  color: rgba(255, 255, 255, 0.86);
  font-size: 12px;
  line-height: 1.6;
}

.mock-player__controls {
  margin-top: 14px;
  display: grid;
  grid-template-columns: 44px 1fr 44px;
  align-items: center;
  gap: 10px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.72);
}

.mock-player__progress {
  height: 6px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.16);
}

.mock-player__bar {
  width: 34%;
  height: 100%;
  background: linear-gradient(90deg, #67e8f9, #fbbf24);
}

.video {
  width: 100%;
  height: auto;
  display: block;
  aspect-ratio: 16 / 9;
  background: #000;
}

.tip {
  margin-top: 12px;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}

.topbar {
  padding: 10px 12px;
  border-radius: 16px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 20px rgba(24, 45, 73, 0.08);
}

.wrap {
  margin-top: 12px;
  border-radius: 20px;
  border: 1px solid rgba(32, 42, 55, 0.14);
}

.tip {
  margin-top: 14px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(31, 122, 140, 0.08);
  color: var(--primary-deep);
}

.actions {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.btn {
  min-height: 42px;
  border: 0;
  border-radius: 14px;
  padding: 0 14px;
  font-weight: 900;
  background: rgba(32, 42, 55, 0.08);
  color: var(--text);
}

.btn--primary {
  background: linear-gradient(135deg, #1f7a8c, #164e63);
  color: #fff;
}

.link {
  border: 0;
  background: transparent;
  color: inherit;
  font-weight: 900;
}

@media (max-width: 480px) {
  .actions {
    grid-template-columns: 1fr;
  }
}
</style>
