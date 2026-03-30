<template>
  <div class="page">
    <header class="topbar">
      <button class="back" @click="router.back()">‹</button>
      <div class="topbar-title">{{ isNew ? '新建笔记' : '编辑笔记' }}</div>
      <button class="link" @click="save" :disabled="saving || loading">{{ saving ? '…' : '保存' }}</button>
    </header>

    <div v-if="error" class="alert alert--bad">{{ error }}</div>

    <div v-if="loading" class="skeleton">
      <div class="sk-card"></div>
      <div class="sk-card sk-card--small"></div>
    </div>

    <template v-else>
      <section class="card">
        <div class="section-title">基础信息</div>

        <label class="field">
          <span class="label">标题</span>
          <input v-model.trim="form.title" class="input" placeholder="请输入标题" />
        </label>

        <label class="field">
          <span class="label">关联视频</span>
          <select v-model="form.videoId" class="input">
            <option value="">不关联视频</option>
            <option v-for="item in videoOptions" :key="item.id" :value="String(item.id)">{{ item.title || `视频 ${item.id}` }}</option>
          </select>
        </label>

        <label class="field">
          <span class="label">标签</span>
          <input v-model.trim="form.tagsText" class="input" placeholder="使用逗号分隔，例如：导数, 重点, 易错题" />
        </label>

        <label class="field">
          <span class="label">内容</span>
          <textarea
            ref="contentTextarea"
            v-model="form.content"
            class="textarea textarea--auto"
            placeholder="记录关键结论、易错点或需要回看的地方"
            rows="6"
            @input="resizeContentTextarea"
          ></textarea>
        </label>
      </section>

      <section class="card card--compact">
        <div class="section-head">
          <div class="section-title">重点时间点</div>
          <div class="section-tip">{{ timestamps.length }} 个</div>
        </div>

        <div v-if="timestamps.length === 0" class="empty-inline">当前还没有重点时间点。</div>

        <div v-else class="timestamp-list">
          <div v-for="item in timestamps" :key="item.localKey" class="timestamp-row">
            <div class="timestamp-grid">
              <div class="time-inline">
                <span class="label">秒数</span>
                <input
                  v-model="item.timeSeconds"
                  class="input input--sm"
                  type="number"
                  min="0"
                  step="0.1"
                  placeholder="例如 92.5"
                  @blur="autofillTimestampSubtitle(item)"
                />
              </div>

              <div class="time-inline time-inline--wide">
                <span class="label">字幕/提示</span>
                <input v-model.trim="item.subtitleText" class="input input--sm" placeholder="可填写对应字幕或回看提示" />
              </div>
            </div>

            <div class="timestamp-actions">
              <div class="time-preview">{{ formatSeconds(item.timeSeconds) }}</div>
            </div>
          </div>
        </div>
      </section>

      <button v-if="!isNew" class="danger" @click="remove" :disabled="saving">删除笔记</button>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { addNoteTimestamp, createNote, deleteNote, getNote, updateNote } from '@/api/note'
import { getSubtitleContext } from '@/api/subtitle'
import { getVideo, getVideoList } from '@/api/video'
import {
  buildVideoMemoryContext,
  cacheOnlineNote,
  cacheVideoList,
  cacheVideoMetadata,
  cacheVideoSubtitles,
  getCachedVideoOptions,
  getOfflineNoteByIdentifier,
  saveNoteOffline,
  shouldUseOfflineMemoryMode
} from '@/services/offlineMemory'

const route = useRoute()
const router = useRouter()
const isNew = computed(() => route.name === 'NoteNew')
const id = computed(() => route.params.id)

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const contentTextarea = ref(null)
const videoOptions = ref([])
const timestamps = ref([])
const originalTimestamps = ref([])
const videoContextLoading = ref(false)
const videoContextError = ref('')
const videoSummary = ref('')
const videoSubtitles = ref([])
const summarySegments = ref([])
const activeSummaryTheme = ref('all')
const currentNoteLocalId = ref('')
const currentNoteServerId = ref('')

const form = reactive({
  title: '',
  content: '',
  tagsText: '',
  videoId: ''
})

const selectedVideoId = computed(() => Number(form.videoId || 0))

const selectedVideoLabel = computed(() => {
  const currentVideoId = String(form.videoId || '')
  if (!currentVideoId) return normalizeText(route.query.videoTitle)
  return (
    videoOptions.value.find((item) => String(item.id) === currentVideoId)?.title ||
    normalizeText(route.query.videoTitle)
  )
})

const normalizeText = (value) => String(value || '').trim()
const resizeTextarea = (element) => {
  if (!element) return
  element.style.height = 'auto'
  element.style.height = `${Math.max(element.scrollHeight, 140)}px`
}
const resizeContentTextarea = () => {
  resizeTextarea(contentTextarea.value)
}
const compactText = (value, maxLength = 56) => {
  const text = normalizeText(value).replace(/\s+/g, ' ')
  if (!text) return ''
  return text.length > maxLength ? `${text.slice(0, maxLength)}…` : text
}

const normalizeNote = (payload) => payload?.note || payload?.data || payload || null
const normalizeVideo = (payload) => payload?.video || payload?.data || payload || null
const normalizeVideoList = (payload) => {
  const list = payload?.videos || payload?.items || payload?.data || payload || []
  return Array.isArray(list) ? list : []
}
const normalizeSubtitleList = (payload) => {
  const list = payload?.subtitles || payload?.data?.subtitles || payload?.data || payload || []
  return Array.isArray(list) ? list : []
}
const normalizeSubtitleSegments = (payload) => {
  const list = payload?.data || payload || []
  return Array.isArray(list) ? list : []
}

const sortByUpdated = (list) =>
  [...list].sort((a, b) => {
    const aTime = new Date(a?.updated_at || a?.created_at || 0).getTime()
    const bTime = new Date(b?.updated_at || b?.created_at || 0).getTime()
    return bTime - aTime
  })

const buildLocalKey = (prefix = 'draft') => `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`

const normalizeTags = (value) => {
  const source = Array.isArray(value) ? value : String(value || '').split(',')
  const seen = new Set()
  return source
    .map((item) => normalizeText(item))
    .filter((item) => {
      if (!item || seen.has(item)) return false
      seen.add(item)
      return true
    })
}

const tagsToInput = (value) => normalizeTags(value).join(', ')

const toEditableTimestamp = (item = {}) => ({
  localKey: item?.id ? `saved-${item.id}` : buildLocalKey(),
  id: item?.id ?? null,
  timeSeconds:
    item?.time_seconds == null || Number.isNaN(Number(item?.time_seconds)) ? '' : String(Number(item.time_seconds)),
  subtitleText: normalizeText(item?.subtitle_text)
})

const toTimestampPayload = (item) => ({
  time_seconds: Math.max(0, Number(item?.timeSeconds || 0)),
  subtitle_text: normalizeText(item?.subtitleText) || null
})

const sortTimestamps = (list) =>
  [...list].sort((a, b) => Number(a?.timeSeconds || 0) - Number(b?.timeSeconds || 0))

const sortByStartTime = (list) =>
  [...list].sort((a, b) => Number(a?.start_time || 0) - Number(b?.start_time || 0))

const ensureVideoOption = (videoId, title = '') => {
  const normalizedVideoId = Number(videoId || 0)
  if (!normalizedVideoId) return
  const exists = videoOptions.value.some((item) => Number(item.id) === normalizedVideoId)
  if (exists) return
  videoOptions.value.unshift({
    id: normalizedVideoId,
    title: normalizeText(title) || `视频 ${normalizedVideoId}`
  })
}

const resetVideoContext = () => {
  videoContextError.value = ''
  videoSummary.value = ''
  videoSubtitles.value = []
  summarySegments.value = []
  activeSummaryTheme.value = 'all'
}

const bootstrapFromRouteQuery = () => {
  if (!isNew.value) return

  const queryVideoId = Number(route.query.videoId || 0)
  const queryVideoTitle = normalizeText(route.query.videoTitle)
  const queryTime = route.query.time
  const querySubtitle = normalizeText(route.query.subtitle)

  if (queryVideoId > 0) {
    form.videoId = String(queryVideoId)
    ensureVideoOption(queryVideoId, queryVideoTitle)
  }

  if (!form.title && queryVideoTitle) {
    form.title = queryVideoTitle
  }
  const validTime = queryTime !== undefined && queryTime !== null && String(queryTime).trim() !== ''
  if (!validTime && !querySubtitle) return

  timestamps.value = sortTimestamps([
    ...timestamps.value,
    toEditableTimestamp({
      time_seconds: validTime ? Number(queryTime) : 0,
      subtitle_text: querySubtitle
    })
  ])
}

const loadAuxiliaryData = async () => {
  const [videoResult] = await Promise.allSettled([getVideoList(1, 100)])
  if (videoResult.status === 'fulfilled') {
    const list = sortByUpdated(normalizeVideoList(videoResult.value?.data))
    videoOptions.value = list
    await cacheVideoList(list)
  } else {
    videoOptions.value = await getCachedVideoOptions()
  }
}

const loadSelectedVideoContext = async (videoId) => {
  if (!videoId) {
    resetVideoContext()
    return
  }

  videoContextLoading.value = true
  videoContextError.value = ''
  activeSummaryTheme.value = 'all'

  const [videoResult, subtitleResult, segmentResult] = await Promise.allSettled([
    getVideo(videoId),
    getSubtitleContext(videoId, { preferMerged: false }),
    getSubtitleContext(videoId, { preferMerged: true })
  ])

  try {
    const videoDetail = videoResult.status === 'fulfilled' ? normalizeVideo(videoResult.value?.data) : null
    const currentSummary = normalizeText(videoDetail?.summary)
    const rawSubtitles =
      subtitleResult.status === 'fulfilled' ? sortByStartTime(normalizeSubtitleList(subtitleResult.value?.data)) : []
    const mergedSegments =
      segmentResult.status === 'fulfilled' ? sortByStartTime(normalizeSubtitleSegments(segmentResult.value?.data)) : []
    const segmentSource = mergedSegments.length > 0 ? mergedSegments : rawSubtitles

    if (videoDetail) {
      await cacheVideoMetadata(videoDetail)
    }
    if (segmentSource.length > 0) {
      await cacheVideoSubtitles(videoId, segmentSource)
    }
    videoSummary.value = currentSummary
    videoSubtitles.value = rawSubtitles
    summarySegments.value = []
    if (!summarySegments.value.length && !videoSubtitles.value.length) {
      videoContextError.value = '当前视频还没有可用字幕。'
    }
  } catch (e) {
    if (shouldUseOfflineMemoryMode(e)) {
      const context = await buildVideoMemoryContext(videoId)
      videoSummary.value = normalizeText(context?.summary)
      videoSubtitles.value = sortByStartTime(context?.subtitles || [])
      summarySegments.value = []
      videoContextError.value = videoSummary.value || videoSubtitles.value.length > 0
        ? '当前展示的是本地离线摘要与字幕缓存'
        : '当前视频还没有可用的离线摘要或字幕缓存。'
    } else {
      videoContextError.value = e?.message || '视频摘要与字幕上下文加载失败'
    }
  } finally {
    videoContextLoading.value = false
  }
}

const applyLoadedNote = (note) => {
  if (!note) return
  currentNoteLocalId.value = String(note.local_id || '')
  currentNoteServerId.value = String(note.server_id || note.id || '')
  form.title = note.title || ''
  form.content = note.content || ''
  form.tagsText = tagsToInput(note.tags)
  form.videoId = note.video_id ? String(note.video_id) : ''
  ensureVideoOption(note.video_id, note.video_title)

  const loadedTimestamps = sortTimestamps((note.timestamps || []).map((item) => toEditableTimestamp(item)))
  timestamps.value = loadedTimestamps
  originalTimestamps.value = loadedTimestamps.map((item) => ({
    id: item.id,
    timeSeconds: item.timeSeconds,
    subtitleText: item.subtitleText
  }))
}

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    await loadAuxiliaryData()

    if (isNew.value) {
      bootstrapFromRouteQuery()
      return
    }

    const res = await getNote(id.value)
    const note = normalizeNote(res.data)
    if (!note) throw new Error('笔记不存在')
    const cached = await cacheOnlineNote(note)
    applyLoadedNote(cached)
  } catch (e) {
    if (shouldUseOfflineMemoryMode(e)) {
      const offlineNote = await getOfflineNoteByIdentifier(id.value)
      if (!offlineNote) {
        error.value = e?.message || '加载失败'
      } else {
        applyLoadedNote(offlineNote)
        error.value = '当前后端不可达，正在编辑本地离线笔记'
      }
    } else {
      error.value = e?.message || '加载失败'
    }
  } finally {
    loading.value = false
    await nextTick()
    resizeContentTextarea()
  }
}

const parsePositiveSeconds = (value) => {
  const numericValue = Number(normalizeText(value))
  if (!Number.isFinite(numericValue) || numericValue < 0) return null
  return numericValue
}

const findClosestTimedItem = (list, seconds, maxGapSeconds = 18) => {
  if (!Array.isArray(list) || list.length === 0) return null

  let bestMatch = null
  let bestDistance = Number.POSITIVE_INFINITY

  list.forEach((item) => {
    const startTime = Number(item?.start_time || 0)
    const endTime = Number(item?.end_time ?? item?.start_time ?? 0)
    const distance = seconds < startTime ? startTime - seconds : seconds > endTime ? seconds - endTime : 0
    if (distance < bestDistance) {
      bestDistance = distance
      bestMatch = item
    }
  })

  return bestDistance <= maxGapSeconds ? bestMatch : null
}

const findMatchingSubtitle = (seconds) => findClosestTimedItem(videoSubtitles.value, seconds, 18)

const suggestSubtitleText = (seconds) => {
  const subtitle = findMatchingSubtitle(seconds)
  if (subtitle?.text) return compactText(subtitle.text)
  return ''
}

const hasTimestampAt = (seconds) =>
  timestamps.value.some((item) => Math.abs(Number(item?.timeSeconds || 0) - Number(seconds || 0)) < 0.001)

const addTimestampEntry = (seconds, subtitleText) => {
  if (hasTimestampAt(seconds)) return false

  timestamps.value = sortTimestamps([
    ...timestamps.value,
    toEditableTimestamp({
      time_seconds: seconds,
      subtitle_text: subtitleText
    })
  ])
  return true
}

const autofillTimestampSubtitle = (item) => {
  if (!item || normalizeText(item.subtitleText)) return
  const seconds = parsePositiveSeconds(item.timeSeconds)
  if (seconds == null) return
  item.subtitleText = suggestSubtitleText(seconds)
}

const formatSeconds = (value) => {
  const seconds = Number(value || 0)
  if (!Number.isFinite(seconds) || seconds < 0) return '--:--'
  const minutes = Math.floor(seconds / 60)
  const remain = Math.floor(seconds % 60)
  return `${String(minutes).padStart(2, '0')}:${String(remain).padStart(2, '0')}`
}

const timestampsEqual = (current, original) =>
  Math.abs(Number(current?.timeSeconds || 0) - Number(original?.timeSeconds || 0)) < 0.001 &&
  normalizeText(current?.subtitleText) === normalizeText(original?.subtitleText)

const syncTimestamps = async (noteId) => {
  const currentById = new Map(timestamps.value.filter((item) => item.id).map((item) => [Number(item.id), item]))

  for (const original of originalTimestamps.value) {
    const current = currentById.get(Number(original.id))
    if (!current) continue

    if (!timestampsEqual(current, original)) {
      await addNoteTimestamp(noteId, toTimestampPayload(current))
    }
  }

  for (const item of timestamps.value.filter((entry) => !entry.id)) {
    await addNoteTimestamp(noteId, toTimestampPayload(item))
  }
}

const buildPayload = () => ({
  title: form.title,
  content: buildNoteContent(),
  video_id: form.videoId ? Number(form.videoId) : null,
  tags: normalizeTags(form.tagsText).join(',')
})

const buildMemoryLines = () => {
  const lines = []
  if (selectedVideoLabel.value) lines.push(`关联视频：${selectedVideoLabel.value}`)

  const normalizedTimestamps = sortTimestamps(timestamps.value)
    .map((item) => {
      const timeLabel = formatSeconds(item.timeSeconds)
      const subtitle = normalizeText(item.subtitleText)
      return subtitle ? `- ${timeLabel} ${subtitle}` : `- ${timeLabel}`
    })
    .filter(Boolean)

  if (normalizedTimestamps.length > 0) {
    lines.push('重点时间点：')
    lines.push(...normalizedTimestamps)
  }

  return lines
}

const buildNoteContent = () => {
  const manualContent = normalizeText(form.content)
  if (manualContent) return manualContent

  const memoryLines = buildMemoryLines()
  if (memoryLines.length === 0) return ''

  return `${memoryLines.join('\n')}\n\n待补充要点：\n- `
}
const save = async () => {
  if (saving.value) return
  saving.value = true
  error.value = ''
  try {
    if (!form.title) {
      error.value = '请填写标题'
      return
    }

    const payload = buildPayload()
    const offlineSave = async (noteAction) => {
      const saved = await saveNoteOffline(
        {
          ...payload,
          timestamps: timestamps.value.map((item) => toTimestampPayload(item)),
          video_title: selectedVideoLabel.value
        },
        {
          existingLocalId: currentNoteLocalId.value || null,
          existingServerId: currentNoteServerId.value || null
        }
      )
      currentNoteLocalId.value = saved.local_id
      currentNoteServerId.value = saved.server_id || ''
      const query = {
        noteId: saved.server_id || saved.local_id,
        noteAction
      }
      if (payload.video_id) query.videoId = String(payload.video_id)
      await router.replace({ path: '/notes', query })
    }

    if (!payload.content) {
      error.value = '请填写内容，或至少关联视频/添加重点时间点后再保存'
      return
    }

    if (isNew.value) {
      if (shouldUseOfflineMemoryMode()) {
        await offlineSave('created')
        return
      }
      try {
        const response = await createNote({
          ...payload,
          timestamps: timestamps.value.map((item) => toTimestampPayload(item))
        })
        const created = normalizeNote(response?.data)
        const cached = await cacheOnlineNote({
          ...created,
          timestamps: created?.timestamps || timestamps.value.map((item) => toTimestampPayload(item)),
          video_title: selectedVideoLabel.value
        })
        currentNoteLocalId.value = cached.local_id
        currentNoteServerId.value = cached.server_id || created?.id || ''
        const query = {}
        if (cached.server_id || cached.local_id) query.noteId = cached.server_id || cached.local_id
        query.noteAction = 'created'
        if (payload.video_id) query.videoId = String(payload.video_id)
        await router.replace({ path: '/notes', query })
      } catch (e) {
        if (shouldUseOfflineMemoryMode(e)) {
          await offlineSave('created')
          return
        }
        throw e
      }
      return
    }

    if (shouldUseOfflineMemoryMode()) {
      await offlineSave('updated')
      return
    }

    try {
      if (!currentNoteServerId.value) {
        const response = await createNote({
          ...payload,
          timestamps: timestamps.value.map((item) => toTimestampPayload(item))
        })
        const created = normalizeNote(response?.data)
        const cached = await cacheOnlineNote({
          ...created,
          timestamps: created?.timestamps || timestamps.value.map((item) => toTimestampPayload(item)),
          video_title: selectedVideoLabel.value
        })
        currentNoteLocalId.value = cached.local_id
        currentNoteServerId.value = cached.server_id || created?.id || ''
      } else {
        const response = await updateNote(currentNoteServerId.value, payload)
        await syncTimestamps(currentNoteServerId.value)
        const updated = normalizeNote(response?.data)
        const cached = await cacheOnlineNote({
          ...updated,
          timestamps: timestamps.value.map((item) => toTimestampPayload(item)),
          video_title: selectedVideoLabel.value
        })
        currentNoteLocalId.value = cached.local_id
        currentNoteServerId.value = cached.server_id || updated?.id || currentNoteServerId.value
      }

      const query = {
        noteId: currentNoteServerId.value || currentNoteLocalId.value || String(id.value),
        noteAction: 'updated'
      }
      if (payload.video_id) query.videoId = String(payload.video_id)
      await router.replace({ path: '/notes', query })
    } catch (e) {
      if (shouldUseOfflineMemoryMode(e)) {
        await offlineSave('updated')
        return
      }
      throw e
    }
  } catch (e) {
    error.value = e?.message || '保存失败'
  } finally {
    saving.value = false
  }
}

const remove = async () => {
  const ok = window.confirm('确认删除该笔记？')
  if (!ok) return
  saving.value = true
  error.value = ''
  try {
    await deleteNote(id.value)
    router.replace('/notes')
  } catch (e) {
    error.value = e?.message || '删除失败'
  } finally {
    saving.value = false
  }
}

watch(
  selectedVideoId,
  async (videoId) => {
    await loadSelectedVideoContext(videoId)
  },
  { immediate: true }
)

watch(selectedVideoLabel, (label) => {
  if (!isNew.value || form.title) return
  const normalizedLabel = normalizeText(label)
  if (normalizedLabel) form.title = normalizedLabel
})

watch(
  () => form.content,
  () => {
    resizeContentTextarea()
  }
)

onMounted(load)
</script>

<style scoped>
.page {
  max-width: 520px;
  margin: 0 auto;
  padding: calc(14px + env(safe-area-inset-top)) 16px 0;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 5;
  display: grid;
  grid-template-columns: 40px 1fr 56px;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 16px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: rgba(242, 235, 248, 0.92);
  box-shadow: 0 10px 20px rgba(101, 87, 117, 0.08);
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
  font-weight: 800;
  margin-bottom: 12px;
}

.alert--bad {
  background: var(--lilac-bg);
  color: var(--lilac-text);
}

.skeleton {
  display: grid;
  gap: 12px;
}

.sk-card {
  height: 220px;
  border-radius: 24px;
  background: linear-gradient(90deg, #f3f4f6, #e5e7eb, #f3f4f6);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
}

.sk-card--small {
  height: 150px;
}

@keyframes shimmer {
  0% { background-position: 0% 0; }
  100% { background-position: 200% 0; }
}

.context-card,
.card {
  margin-top: 12px;
  border-radius: 24px;
  padding: 16px;
  background: linear-gradient(180deg, #ffffff, #f0e8f7);
  border: 1px solid rgba(32, 42, 55, 0.09);
  box-shadow: 0 16px 30px rgba(101, 87, 117, 0.1);
}

.card--compact {
  padding-bottom: 12px;
}

.context-card {
  background: linear-gradient(180deg, rgba(139, 121, 157, 0.12), rgba(183, 157, 213, 0.12));
}

.context-line,
.section-tip,
.empty-inline {
  font-size: 13px;
  line-height: 1.6;
  color: #475569;
}

.inline-note {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.6;
  font-weight: 700;
}

.inline-note--bad {
  background: var(--lilac-bg);
  color: var(--lilac-text);
}

.context-line + .context-line {
  margin-top: 6px;
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 900;
  color: #0f172a;
}

.field {
  display: grid;
  gap: 6px;
}

.field--wide {
  flex: 1;
}

.label {
  font-size: 12px;
  color: var(--muted);
  font-weight: 900;
  margin-top: 8px;
}

.input,
.textarea {
  width: 100%;
  border: 1px solid rgba(32, 42, 55, 0.14);
  border-radius: 14px;
  padding: 10px 12px;
  outline: none;
  font-size: 14px;
  background: #fff;
}

.textarea--auto {
  min-height: 140px;
  resize: none;
  overflow: hidden;
}

.input--sm {
  padding-top: 9px;
  padding-bottom: 9px;
}

.textarea {
  min-height: 220px;
  resize: vertical;
  line-height: 1.6;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.summary-panel {
  margin-top: 12px;
  border-radius: 18px;
  padding: 14px;
  background: var(--ok-bg);
  display: grid;
  gap: 8px;
}

.summary-panel__title {
  font-size: 12px;
  font-weight: 900;
  color: var(--ok-text);
}

.summary-panel__body {
  font-size: 13px;
  line-height: 1.7;
  color: #0f172a;
  white-space: pre-wrap;
}

.segment-list {
  display: grid;
  gap: 12px;
  margin-top: 14px;
}

.segment-card {
  border: 1px solid rgba(32, 42, 55, 0.08);
  border-radius: 18px;
  padding: 14px;
  background: #fff;
  text-align: left;
  display: grid;
  gap: 8px;
}

.segment-card__head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.segment-card__theme {
  font-size: 12px;
  font-weight: 900;
  color: var(--primary-deep);
}

.segment-card__time {
  font-size: 11px;
  font-weight: 800;
  color: #7a667f;
}

.segment-card__title {
  font-size: 12px;
  font-weight: 800;
  color: #0f172a;
}

.segment-card__text {
  font-size: 13px;
  line-height: 1.7;
  color: #334155;
}

.segment-card__action {
  font-size: 12px;
  font-weight: 900;
  color: var(--primary);
}

.tag-chip {
  border: 1px solid rgba(139, 121, 157, 0.2);
  background: var(--ok-bg);
  color: var(--ok-text);
  border-radius: 999px;
  padding: 8px 10px;
  font-weight: 800;
  font-size: 12px;
}

.tag-chip--active {
  background: var(--primary-deep);
  color: #fff;
  border-color: transparent;
}

.timestamp-list {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.timestamp-row {
  display: grid;
  gap: 8px;
  padding: 10px 0;
  border-top: 1px solid rgba(32, 42, 55, 0.06);
}

.timestamp-row:first-child {
  border-top: 0;
  padding-top: 0;
}

.timestamp-grid,
.adder-grid {
  display: grid;
  gap: 12px;
}

.timestamp-actions {
  margin-top: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.time-preview {
  font-size: 12px;
  color: #7a667f;
  font-weight: 800;
}

.adder {
  margin-top: 16px;
  border-top: 1px solid rgba(32, 42, 55, 0.08);
  padding-top: 14px;
}

.adder--compact {
  margin-top: 12px;
  padding-top: 12px;
}

.field--inline {
  gap: 4px;
}

.mini {
  margin-top: 12px;
  border: 0;
  border-radius: 12px;
  padding: 10px 12px;
  background: var(--ok-bg);
  color: var(--ok-text);
  font-weight: 800;
  font-size: 12px;
}

.mini--inline {
  margin-top: 10px;
}

.danger {
  margin-top: 12px;
  width: 100%;
  border: 0;
  background: var(--lilac-bg);
  color: var(--lilac-text);
  border-radius: 16px;
  padding: 12px;
  font-weight: 900;
}

.danger:disabled {
  opacity: 0.6;
}

@media (max-width: 420px) {
  .topbar {
    grid-template-columns: 40px minmax(0, 1fr) minmax(52px, auto);
  }

  .section-head,
  .timestamp-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
