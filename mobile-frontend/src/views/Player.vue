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
          @timeupdate="handleTimeUpdate"
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

    <section class="assistant-card">
      <div class="assistant-head">
        <div class="assistant-head__copy">
          <div class="assistant-title">这一段记笔记</div>
          <div class="assistant-tip">系统已按当前时间点整理成学习卡片，标题会自动按“分类 · 时间点”生成。</div>
        </div>
        <button class="btn btn--primary" @click="saveTimestampNote" :disabled="noteBusy || !canSaveTimestampNote">
          {{ noteBusy ? '保存中…' : '记下这一段' }}
        </button>
      </div>
      <div class="note-summary">
        <span class="note-summary__chip">系统分类 · {{ inferredNoteCategory }}</span>
        <span class="note-summary__chip note-summary__chip--ghost">自动标题 · {{ autoTitlePreview }}</span>
        <span class="note-summary__time">当前播放位置：{{ currentTimeText || '00:00' }}</span>
      </div>
      <div class="timestamp-preview">
        <div class="timestamp-preview__title">字幕片段</div>
        <div class="timestamp-preview__text">{{ subtitlePreview || '当前时间点附近还没有可用字幕。' }}</div>
      </div>
      <label class="assistant-field assistant-field--compact">
        <span class="assistant-label">短标题（可选）</span>
        <input v-model.trim="noteTitle" class="assistant-input" type="text" placeholder="可留空，系统会自动生成" />
        <div class="assistant-hint">留空时使用自动标题；填写后会覆盖自动标题。</div>
      </label>
      <label class="assistant-field">
        <span class="assistant-label">这一段的笔记</span>
        <textarea
          v-model.trim="noteBody"
          class="assistant-input"
          rows="3"
          placeholder="把你真正想记住的内容写在这里，系统会自动附上当前时间点。"
        />
      </label>
      <label class="assistant-field">
        <span class="assistant-label">我还想继续思考</span>
        <div class="tag-picks">
          <button
            v-for="thought in thoughtOptions"
            :key="thought"
            class="tag-chip"
            :class="{ 'tag-chip--active': selectedThoughts.includes(thought) }"
            @click="toggleThought(thought)"
          >
            {{ thought }}
          </button>
        </div>
        <input
          v-model.trim="customThought"
          class="assistant-input"
          type="text"
          placeholder="其他想法（可选），例如：这里要回去再看一遍"
        />
      </label>
      <div class="tag-picks">
        <button
          v-for="tag in noteTagOptions"
          :key="tag"
          class="tag-chip"
          :class="{ 'tag-chip--active': selectedNoteTags.includes(tag) }"
          @click="toggleNoteTag(tag)"
        >
          {{ tag }}
        </button>
      </div>
      <div v-if="noteResult" class="assistant-result">
        <div class="assistant-result__title">已保存</div>
        <div class="assistant-result__text">{{ noteResult.summary }}</div>
        <button v-if="noteResult.noteId" class="btn" @click="router.push(`/notes/${noteResult.noteId}`)">打开笔记</button>
      </div>
    </section>

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
import { createNote } from '@/api/note'
import { getVideo } from '@/api/video'
import { getSubtitleContext } from '@/api/subtitle'

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id)
const initialStartSeconds = computed(() => {
  const raw = route.query.start
  const parsed = Number.parseFloat(String(raw ?? ""))
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null
})
const videoTitle = ref(`视频 ${id.value}`)
const pageError = ref('')
const playerState = ref('准备中')
const durationSeconds = ref(0)
const currentTimeSeconds = ref(0)
const videoRef = ref(null)
const videoMeta = ref(null)
const subtitleFragments = ref([])
const noteTitle = ref('')
const noteBody = ref('')
const customThought = ref('')
const selectedNoteTags = ref(['再思考'])
const selectedThoughts = ref(['需要回看'])
const noteBusy = ref(false)
const noteResult = ref(null)
const pendingSeekSeconds = ref(null)
const noteTagOptions = ['再思考', '很重要', '待复习', '需要查证', '想再看一遍']
const thoughtOptions = ['需要回看', '需要查证', '要补充例子', '容易忘', '和前面有关']

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
const subtitlePreview = computed(() => buildSubtitleExcerpt())
const inferredNoteCategory = computed(() => inferNoteCategory())
const autoTitlePreview = computed(() => `${inferredNoteCategory.value} · ${currentTimeText.value || '00:00'}`)
const currentTimeText = computed(() => {
  const total = Math.max(0, Math.round(Number(currentTimeSeconds.value || 0)))
  const hh = Math.floor(total / 3600)
  const mm = Math.floor((total % 3600) / 60)
  const ss = total % 60
  return hh > 0
    ? `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}`
    : `${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}`
})
const canSaveTimestampNote = computed(() => !noteBusy.value)
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
    await loadSubtitleContext()
  } catch (err) {
    if (!useMockPlayer.value) {
      pageError.value = extractErrorMessage(err, '视频信息加载失败，请检查后端地址和视频是否存在。')
      playerState.value = '视频信息加载失败'
    }
  }
}

const loadSubtitleContext = async () => {
  try {
    const res = await getSubtitleContext(Number(id.value), { preferMerged: true })
    const list = res?.data?.subtitles || res?.data || res?.subtitles || res || []
    subtitleFragments.value = Array.isArray(list) ? list : []
  } catch {
    subtitleFragments.value = []
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
  if (initialStartSeconds.value !== null && pendingSeekSeconds.value === null) {
    pendingSeekSeconds.value = initialStartSeconds.value
  }
  applyPendingSeek(event?.target)
  playerState.value = '视频元数据已加载'
}

const handleCanPlay = () => {
  applyPendingSeek(videoRef.value)
  playerState.value = '可以开始播放'
}

const handlePlaying = () => {
  playerState.value = '播放中'
}

const handleTimeUpdate = (event) => {
  currentTimeSeconds.value = Number(event?.target?.currentTime || 0)
}

const handleWaiting = () => {
  playerState.value = '缓冲中'
}

const handleVideoError = () => {
  playerState.value = '播放失败'
  pageError.value = '视频流加载失败。请确认后端服务在线、手机与 Mac 在同一网络，并且该视频文件仍存在。'
}

const applyPendingSeek = (element) => {
  if (!element || pendingSeekSeconds.value === null) return
  const duration = Number(element.duration || durationSeconds.value || 0)
  const target = Math.max(0, Number(pendingSeekSeconds.value || 0))
  if (!Number.isFinite(target)) {
    pendingSeekSeconds.value = null
    return
  }
  if (duration > 0) {
    element.currentTime = Math.min(target, Math.max(duration - 0.25, 0))
    currentTimeSeconds.value = Number(element.currentTime || target)
    pendingSeekSeconds.value = null
  }
}

const formatSeconds = (seconds) => {
  const total = Math.max(0, Math.round(Number(seconds || 0)))
  const mm = Math.floor((total % 3600) / 60)
  const ss = total % 60
  return `${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}`
}

const buildSubtitleExcerpt = () => {
  const list = Array.isArray(subtitleFragments.value) ? subtitleFragments.value : []
  if (list.length === 0) return ''
  const target = Number(currentTimeSeconds.value || 0)
  const ordered = [...list].sort((a, b) => Number(a?.start_time || 0) - Number(b?.start_time || 0))
  let bestIndex = 0
  let bestDistance = Number.POSITIVE_INFINITY
  ordered.forEach((item, index) => {
    const start = Number(item?.start_time || 0)
    const end = Number(item?.end_time || start)
    const midpoint = (start + end) / 2
    const distance = Math.abs(midpoint - target)
    if (distance < bestDistance) {
      bestDistance = distance
      bestIndex = index
    }
  })
  const scope = ordered.slice(Math.max(0, bestIndex - 1), Math.min(ordered.length, bestIndex + 2))
  return scope
    .map((item) => {
      const start = Number(item?.start_time || 0)
      const end = Number(item?.end_time || start)
      const text = String(item?.text || '').trim()
      return text ? `[${formatSeconds(start)}-${formatSeconds(end)}] ${text}` : ''
    })
    .filter(Boolean)
    .join('\n')
}

const deriveAutoTitle = () => {
  const manualTitle = String(noteTitle.value || '').trim()
  if (manualTitle) return manualTitle
  const category = inferNoteCategory()
  return `${category} · ${currentTimeText.value || '00:00'}`
}

const inferNoteCategory = () => {
  const text = `${buildSubtitleExcerpt()} ${noteBody.value} ${customThought.value}`.toLowerCase()
  if (/例题|例如|举例|算|计算|解题|题目/.test(text)) return '例题'
  if (/思考|为什么|如何|怎么|原因|讨论|探究/.test(text)) return '思考题'
  if (/易错|注意|别忘|常见错误|容易/.test(text)) return '易错点'
  if (/结论|总结|归纳|因此|所以/.test(text)) return '结论'
  return '知识点'
}

const toggleNoteTag = (tag) => {
  const current = new Set(selectedNoteTags.value)
  if (current.has(tag)) current.delete(tag)
  else current.add(tag)
  selectedNoteTags.value = [...current]
}

const toggleThought = (thought) => {
  const current = new Set(selectedThoughts.value)
  if (current.has(thought)) current.delete(thought)
  else current.add(thought)
  selectedThoughts.value = [...current]
}

const saveTimestampNote = async () => {
  if (!canSaveTimestampNote.value) return
  noteBusy.value = true
  try {
    const subtitleExcerpt = buildSubtitleExcerpt()
    const thoughtText = [...selectedThoughts.value, customThought.value.trim()].filter(Boolean).join('；')
    const contentParts = []
    if (subtitleExcerpt) contentParts.push(`字幕片段：\n${subtitleExcerpt}`)
    if (noteBody.value.trim()) contentParts.push(`笔记：\n${noteBody.value.trim()}`)
    if (thoughtText) contentParts.push(`待思考：\n${thoughtText}`)
    const noteContent = contentParts.join('\n\n').trim() || subtitleExcerpt || noteBody.value.trim() || thoughtText || `${videoTitle.value} 的时间点记录`
    const noteTitleValue = deriveAutoTitle()
    const response = await createNote({
      title: noteTitleValue,
      content: noteContent,
      note_type: 'text',
      video_id: Number(id.value),
      tags: selectedNoteTags.value.join(','),
      timestamps: [
        {
          time_seconds: Number(currentTimeSeconds.value || 0),
          subtitle_text: subtitleExcerpt || ''
        }
      ]
    })
    const created = response?.data?.data || response?.data?.note || response?.data || null
    const noteId = created?.id || created?.note_id || created?.data?.id || null
    if (noteId) {
      noteResult.value = {
        noteId,
        summary: `已保存 ${currentTimeText.value} 的时间点笔记：${noteTitleValue}`
      }
      noteBody.value = ''
      customThought.value = ''
      noteTitle.value = ''
      selectedNoteTags.value = ['再思考']
      selectedThoughts.value = ['需要回看']
    } else {
      noteResult.value = {
        noteId: null,
        summary: '已保存笔记'
      }
    }
  } catch (err) {
    pageError.value = extractErrorMessage(err, '时间戳笔记保存失败')
  } finally {
    noteBusy.value = false
  }
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
  background: var(--lilac-bg);
  color: var(--lilac-text);
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
  background: rgba(139, 121, 157, 0.12);
  color: var(--primary-deep);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.04em;
}

.badge--status {
  background: var(--ok-bg);
  color: var(--ok-text);
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
    linear-gradient(180deg, #261f2d, #000);
}

.mock-player {
  padding: 16px;
  background: linear-gradient(180deg, #261f2d, #3a3042);
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
    radial-gradient(circle at top right, rgba(183, 157, 213, 0.28), transparent 34%),
    linear-gradient(145deg, rgba(139, 121, 157, 0.94), rgba(73, 60, 82, 0.98));
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
  background: linear-gradient(90deg, #d8bd83, #fbbf24);
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
  background: rgba(242, 235, 248, 0.92);
  box-shadow: 0 10px 20px rgba(101, 87, 117, 0.08);
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
  background: rgba(139, 121, 157, 0.08);
  color: var(--primary-deep);
}

.assistant-card {
  margin-top: 12px;
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: linear-gradient(180deg, rgba(242, 235, 248, 0.98), rgba(242, 235, 248, 0.96));
  display: grid;
  gap: 10px;
}

.assistant-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.assistant-head__copy {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.assistant-title {
  font-size: 13px;
  font-weight: 900;
}

.assistant-tip,
.note-summary__time {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.5;
}

.note-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.note-summary__chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(139, 121, 157, 0.12);
  color: var(--primary-deep);
  font-size: 12px;
  font-weight: 900;
}

.note-summary__chip--ghost {
  background: rgba(255, 255, 255, 0.72);
}

.assistant-field {
  display: grid;
  gap: 6px;
}

.assistant-field--compact {
  gap: 5px;
}

.assistant-label {
  font-size: 12px;
  font-weight: 900;
  color: var(--primary-deep);
}

.assistant-hint {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.5;
}

.assistant-input {
  width: 100%;
  border: 1px solid rgba(32, 42, 55, 0.14);
  border-radius: 14px;
  padding: 10px 12px;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.9);
}

.tag-picks {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-chip {
  border: 1px solid rgba(32, 42, 55, 0.12);
  background: rgba(255, 255, 255, 0.8);
  color: var(--primary-deep);
  border-radius: 999px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 900;
}

.tag-chip--active {
  background: linear-gradient(135deg, #8b799d, #6f5d7d);
  color: #fff;
  border-color: transparent;
}

.timestamp-preview {
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(32, 42, 55, 0.08);
}

.timestamp-preview__title {
  font-size: 12px;
  font-weight: 900;
}

.timestamp-preview__text {
  white-space: pre-wrap;
  font-size: 12px;
  line-height: 1.6;
  color: #334155;
}

.assistant-result {
  display: grid;
  gap: 8px;
  padding: 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.72);
}

.assistant-result__title {
  font-size: 13px;
  font-weight: 900;
}

.assistant-result__text {
  font-size: 12px;
  line-height: 1.6;
  color: #334155;
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
  background: linear-gradient(135deg, #8b799d, #6f5d7d);
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
