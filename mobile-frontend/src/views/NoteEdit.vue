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
      <section v-if="selectedVideoLabel || hasPrefilledTimestamp" class="context-card">
        <div class="section-title">当前上下文</div>
        <div v-if="selectedVideoLabel" class="context-line">关联视频：{{ selectedVideoLabel }}</div>
        <div v-if="hasPrefilledTimestamp" class="context-line">已带入 {{ timestamps.length }} 个重点时间点，可直接保存或继续编辑。</div>
      </section>

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

        <div v-if="popularTags.length > 0" class="tag-row">
          <button
            v-for="item in popularTags.slice(0, 8)"
            :key="item.name"
            class="tag-chip"
            :class="{ 'tag-chip--active': tagSelected(item.name) }"
            @click="toggleSuggestedTag(item.name)"
          >
            {{ item.name }}
          </button>
        </div>

        <label class="field">
          <span class="label">内容</span>
          <textarea v-model="form.content" class="textarea" placeholder="记录关键结论、易错点或需要回看的地方"></textarea>
        </label>
      </section>

      <section class="card">
        <div class="section-head">
          <div>
            <div class="section-title">重点时间点</div>
            <div class="section-tip">可挂接多个时间点，便于后续从视频内容回看笔记。</div>
          </div>
          <div class="section-tip">{{ timestamps.length }} 个</div>
        </div>

        <div v-if="timestamps.length === 0" class="empty-inline">当前还没有重点时间点。</div>

        <div v-else class="timestamp-list">
          <div v-for="item in timestamps" :key="item.localKey" class="timestamp-card">
            <div class="timestamp-grid">
              <label class="field">
                <span class="label">秒数</span>
                <input v-model="item.timeSeconds" class="input" type="number" min="0" step="0.1" placeholder="例如 92.5" />
              </label>

              <label class="field field--wide">
                <span class="label">字幕/提示</span>
                <input v-model.trim="item.subtitleText" class="input" placeholder="可填写对应字幕或回看提示" />
              </label>
            </div>

            <div class="timestamp-actions">
              <div class="time-preview">{{ formatSeconds(item.timeSeconds) }}</div>
              <button class="danger-link" @click="removeTimestamp(item.localKey)">删除</button>
            </div>
          </div>
        </div>

        <div class="adder">
          <div class="adder-grid">
            <label class="field">
              <span class="label">新增秒数</span>
              <input v-model="draftTimestamp.timeSeconds" class="input" type="number" min="0" step="0.1" placeholder="例如 120" />
            </label>

            <label class="field field--wide">
              <span class="label">新增字幕/提示</span>
              <input v-model.trim="draftTimestamp.subtitleText" class="input" placeholder="例如：这里解释了导数几何意义" />
            </label>
          </div>

          <button class="mini" @click="addDraftTimestamp">添加时间点</button>
        </div>
      </section>

      <button v-if="!isNew" class="danger" @click="remove" :disabled="saving">删除笔记</button>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { addNoteTimestamp, createNote, deleteNote, deleteNoteTimestamp, getNote, getNoteTags, updateNote } from '@/api/note'
import { getVideoList } from '@/api/video'

const route = useRoute()
const router = useRouter()
const isNew = computed(() => route.name === 'NoteNew')
const id = computed(() => route.params.id)

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const videoOptions = ref([])
const popularTags = ref([])
const timestamps = ref([])
const originalTimestamps = ref([])

const form = reactive({
  title: '',
  content: '',
  tagsText: '',
  videoId: ''
})

const draftTimestamp = reactive({
  timeSeconds: '',
  subtitleText: ''
})

const hasPrefilledTimestamp = computed(
  () =>
    isNew.value &&
    (Boolean(route.query.time) || Boolean(route.query.subtitle)) &&
    timestamps.value.length > 0
)

const selectedVideoLabel = computed(() => {
  const currentVideoId = String(form.videoId || '')
  if (!currentVideoId) return normalizeText(route.query.videoTitle)
  return (
    videoOptions.value.find((item) => String(item.id) === currentVideoId)?.title ||
    normalizeText(route.query.videoTitle)
  )
})

const normalizeText = (value) => String(value || '').trim()

const normalizeNote = (payload) => payload?.note || payload?.data || payload || null
const normalizeVideoList = (payload) => {
  const list = payload?.videos || payload?.items || payload?.data || payload || []
  return Array.isArray(list) ? list : []
}
const normalizeTagBuckets = (payload) => {
  const list = payload?.data || payload?.tags || payload || []
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
  const [videoResult, tagResult] = await Promise.allSettled([getVideoList(1, 100), getNoteTags()])
  videoOptions.value = videoResult.status === 'fulfilled' ? sortByUpdated(normalizeVideoList(videoResult.value?.data)) : []
  popularTags.value = tagResult.status === 'fulfilled' ? normalizeTagBuckets(tagResult.value?.data) : []
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
  } catch (e) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const tagSelected = (name) => normalizeTags(form.tagsText).includes(name)

const toggleSuggestedTag = (name) => {
  const tags = normalizeTags(form.tagsText)
  const next = tags.includes(name) ? tags.filter((item) => item !== name) : [...tags, name]
  form.tagsText = next.join(', ')
}

const addDraftTimestamp = () => {
  const rawTime = normalizeText(draftTimestamp.timeSeconds)
  const subtitle = normalizeText(draftTimestamp.subtitleText)
  if (!rawTime && !subtitle) return

  const timeNumber = Number(rawTime || 0)
  if (!Number.isFinite(timeNumber) || timeNumber < 0) {
    error.value = '时间点必须是大于等于 0 的数字'
    return
  }

  timestamps.value = sortTimestamps([
    ...timestamps.value,
    toEditableTimestamp({
      time_seconds: timeNumber,
      subtitle_text: subtitle
    })
  ])
  draftTimestamp.timeSeconds = ''
  draftTimestamp.subtitleText = ''
  error.value = ''
}

const removeTimestamp = (localKey) => {
  timestamps.value = timestamps.value.filter((item) => item.localKey !== localKey)
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
  const currentById = new Map(
    timestamps.value.filter((item) => item.id).map((item) => [Number(item.id), item])
  )

  for (const original of originalTimestamps.value) {
    const current = currentById.get(Number(original.id))
    if (!current) {
      await deleteNoteTimestamp(noteId, original.id)
      continue
    }

    if (!timestampsEqual(current, original)) {
      await deleteNoteTimestamp(noteId, original.id)
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
    if (!payload.content) {
      error.value = '请填写内容，或至少关联视频/添加重点时间点后再保存'
      return
    }

    if (isNew.value) {
      const response = await createNote({
        ...payload,
        timestamps: timestamps.value.map((item) => toTimestampPayload(item))
      })
      const created = normalizeNote(response?.data)
      const createdId = created?.id ? String(created.id) : ''
      const query = {}
      if (createdId) query.noteId = createdId
      query.noteAction = 'created'
      if (payload.video_id) query.videoId = String(payload.video_id)
      await router.replace({ path: '/notes', query })
      return
    }

    const response = await updateNote(id.value, payload)
    await syncTimestamps(id.value)
    const updated = normalizeNote(response?.data)
    const updatedId = updated?.id ? String(updated.id) : String(id.value)
    const query = {
      noteId: updatedId,
      noteAction: 'updated'
    }
    if (payload.video_id) query.videoId = String(payload.video_id)
    await router.replace({ path: '/notes', query })
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
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 20px rgba(24, 45, 73, 0.08);
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
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
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
  background: linear-gradient(180deg, #ffffff, #f9fbfd);
  border: 1px solid rgba(32, 42, 55, 0.09);
  box-shadow: 0 16px 30px rgba(24, 45, 73, 0.1);
}

.context-card {
  background: linear-gradient(180deg, rgba(31, 122, 140, 0.12), rgba(61, 141, 160, 0.06));
}

.context-line,
.section-tip,
.empty-inline {
  font-size: 13px;
  line-height: 1.6;
  color: #475569;
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

.tag-chip {
  border: 1px solid rgba(15, 118, 110, 0.16);
  background: rgba(15, 118, 110, 0.08);
  color: #0f766e;
  border-radius: 999px;
  padding: 8px 10px;
  font-weight: 800;
  font-size: 12px;
}

.tag-chip--active {
  background: #0f766e;
  color: #fff;
  border-color: transparent;
}

.timestamp-list {
  display: grid;
  gap: 12px;
  margin-top: 14px;
}

.timestamp-card {
  border: 1px solid rgba(32, 42, 55, 0.08);
  border-radius: 18px;
  padding: 14px;
  background: #fff;
}

.timestamp-grid,
.adder-grid {
  display: grid;
  gap: 12px;
}

.timestamp-actions {
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.time-preview {
  font-size: 12px;
  color: #0c4a6e;
  font-weight: 800;
}

.adder {
  margin-top: 16px;
  border-top: 1px solid rgba(32, 42, 55, 0.08);
  padding-top: 14px;
}

.mini {
  margin-top: 12px;
  border: 0;
  border-radius: 12px;
  padding: 10px 12px;
  background: rgba(15, 118, 110, 0.12);
  color: #0f766e;
  font-weight: 800;
  font-size: 12px;
}

.danger-link {
  border: 0;
  background: transparent;
  color: #b91c1c;
  font-weight: 900;
}

.danger {
  margin-top: 12px;
  width: 100%;
  border: 0;
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
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
