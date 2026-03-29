<template>
  <div class="page">
    <header class="topbar">
      <h2>笔记</h2>
      <div class="actions">
        <button class="link" @click="reload" :disabled="loading">{{ loading ? '…' : '刷新' }}</button>
        <button class="link" @click="goNewNote">新建</button>
      </div>
    </header>

    <div v-if="error" class="alert alert--bad">
      <span>{{ error }}</span>
      <button class="link" @click="reload">重试</button>
    </div>

    <div v-else-if="focusMessage" class="alert alert--ok">
      <span>{{ focusMessage }}</span>
      <button class="link" @click="clearFocusState">知道了</button>
    </div>

    <section class="filter-card">
      <div class="filter-head">
        <div>
          <div class="section-title">筛选与搜索</div>
          <div class="section-tip">按关键词、视频和标签快速定位学习笔记。</div>
        </div>
        <button class="ghost" @click="clearFilters" :disabled="loading || !hasActiveFilters">清空</button>
      </div>

      <div class="filter-grid">
        <label class="field">
          <span class="label">关键词</span>
          <input
            v-model.trim="filters.search"
            class="input"
            type="search"
            placeholder="搜索标题、内容或标签"
            @keydown.enter.prevent="applyFilters"
          />
        </label>

        <label class="field">
          <span class="label">关联视频</span>
          <select v-model="filters.videoId" class="input">
            <option value="">全部视频</option>
            <option v-for="item in videoOptions" :key="item.id" :value="String(item.id)">{{ item.title || `视频 ${item.id}` }}</option>
          </select>
        </label>
      </div>

      <div v-if="tagOptions.length > 0" class="tag-filter">
        <button
          v-for="item in tagOptions"
          :key="item.name"
          class="tag-chip"
          :class="{ 'tag-chip--active': filters.tag === item.name }"
          @click="toggleTag(item.name)"
        >
          {{ item.name }}
          <span class="tag-chip__count">{{ item.count }}</span>
        </button>
      </div>

      <div class="filter-actions">
        <button class="btn btn--primary" @click="applyFilters" :disabled="loading">应用筛选</button>
      </div>
    </section>

    <div v-if="loading && notes.length === 0" class="skeleton">
      <div v-for="i in 4" :key="i" class="sk-card"></div>
    </div>
    <div v-else-if="notes.length === 0" class="empty">
      <div class="empty__title">当前没有符合条件的笔记。</div>
      <div class="empty__tip">可以从这里新建普通笔记，也可以从视频详情页带着上下文进入记笔记。</div>
    </div>

    <div v-else class="content">
      <div class="section-head">
        <div class="section-title">笔记列表</div>
        <div class="section-tip">共 {{ notes.length }} 条，按最近更新时间排序。</div>
      </div>

      <div class="list">
        <button
          v-for="note in notes"
          :key="noteKey(note)"
          class="card"
          :class="{ 'card--focus': noteKey(note) === focusedNoteKey }"
          :data-note-id="noteKey(note)"
          @click="go(`/notes/${noteKey(note)}`)"
        >
          <div class="row">
            <div class="title">{{ note.title || '未命名笔记' }}</div>
            <i class="arrow">›</i>
          </div>

          <div class="excerpt">{{ buildExcerpt(note.content) }}</div>

          <div class="meta-list">
            <span v-if="note.video_title" class="meta-pill meta-pill--video">{{ note.video_title }}</span>
            <span v-else class="meta-pill">普通笔记</span>
            <span v-if="Array.isArray(note.timestamps) && note.timestamps.length > 0" class="meta-pill meta-pill--time">
              {{ formatTimestampSummary(note.timestamps) }}
            </span>
            <span v-if="note.sync_status === 'pending'" class="meta-pill">待同步</span>
            <span v-else-if="note.sync_status === 'failed'" class="meta-pill">同步失败</span>
          </div>

          <div v-if="Array.isArray(note.tags) && note.tags.length > 0" class="tag-row">
            <span v-for="tag in note.tags.slice(0, 4)" :key="`${note.id}-${tag}`" class="tag-pill">{{ tag }}</span>
          </div>

          <div class="muted">{{ formatTime(note.updated_at || note.created_at) }}</div>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getNote, getNoteTags, getNotes } from '@/api/note'
import { getVideoList } from '@/api/video'
import {
  cacheNotes,
  cacheVideoList,
  getCachedVideoOptions,
  getOfflineNoteByIdentifier,
  getOfflineNoteTags,
  getOfflineNotes,
  shouldUseOfflineMemoryMode
} from '@/services/offlineMemory'

const route = useRoute()
const router = useRouter()
const go = (path) => router.push(path)

const loading = ref(false)
const error = ref('')
const notes = ref([])
const tagOptions = ref([])
const videoOptions = ref([])

const filters = reactive({
  search: String(route.query.search || ''),
  videoId: route.query.videoId ? String(route.query.videoId) : '',
  tag: String(route.query.tag || '')
})

const hasActiveFilters = computed(() => Boolean(filters.search || filters.videoId || filters.tag))
const focusedNoteKey = computed(() => String(route.query.noteId || '').trim())
const focusMessage = computed(() => {
  if (!focusedNoteKey.value) return ''
  if (route.query.noteAction === 'created') return '刚保存的笔记已为你置顶显示。'
  if (route.query.noteAction === 'updated') return '刚更新的笔记已为你置顶显示。'
  return '已定位到指定笔记。'
})
const selectedVideoTitle = computed(
  () => videoOptions.value.find((item) => String(item.id) === String(filters.videoId || ''))?.title || ''
)

const normalizeNoteList = (payload) => {
  const list = payload?.notes || payload?.items || payload?.data || payload || []
  return Array.isArray(list) ? list : []
}

const normalizeTagBuckets = (payload) => {
  const list = payload?.data || payload?.tags || payload || []
  return Array.isArray(list) ? list : []
}

const normalizeVideoList = (payload) => {
  const list = payload?.videos || payload?.items || payload?.data || payload || []
  return Array.isArray(list) ? list : []
}

const noteKey = (note) => String(note?.id || note?.server_id || note?.local_id || '')

const sortNotes = (list) =>
  [...list].sort((a, b) => {
    const aTime = new Date(a?.updated_at || a?.created_at || 0).getTime()
    const bTime = new Date(b?.updated_at || b?.created_at || 0).getTime()
    return bTime - aTime
  })

const buildParams = () => {
  const params = {}
  if (filters.search) params.search = filters.search
  if (filters.videoId) params.video_id = Number(filters.videoId)
  if (filters.tag) params.tag = filters.tag
  return params
}

const syncRouteQuery = async () => {
  const query = {}
  if (filters.search) query.search = filters.search
  if (filters.videoId) query.videoId = String(filters.videoId)
  if (filters.tag) query.tag = filters.tag
  if (focusedNoteKey.value) query.noteId = focusedNoteKey.value
  if (route.query.noteAction) query.noteAction = route.query.noteAction
  await router.replace({ path: route.path, query })
}

const loadOfflineState = async () => {
  let nextNotes = sortNotes(
    await getOfflineNotes({
      search: filters.search,
      videoId: filters.videoId ? Number(filters.videoId) : null,
      tag: filters.tag
    })
  )

  if (focusedNoteKey.value) {
    const existing = nextNotes.find((item) => noteKey(item) === focusedNoteKey.value)
    if (!existing) {
      const focused = await getOfflineNoteByIdentifier(focusedNoteKey.value)
      if (focused) {
        nextNotes = [focused, ...nextNotes]
      }
    } else {
      nextNotes = [existing, ...nextNotes.filter((item) => noteKey(item) !== focusedNoteKey.value)]
    }
  }

  notes.value = nextNotes
  tagOptions.value = await getOfflineNoteTags()
  videoOptions.value = await getCachedVideoOptions()
}

const reload = async () => {
  loading.value = true
  error.value = ''
  const [noteResult, tagResult, videoResult] = await Promise.allSettled([
    getNotes(buildParams()),
    getNoteTags(),
    getVideoList(1, 100)
  ])

  try {
    if (noteResult.status !== 'fulfilled') throw noteResult.reason
    let nextNotes = sortNotes(normalizeNoteList(noteResult.value?.data))
    await cacheNotes(nextNotes)

    if (focusedNoteKey.value) {
      const existing = nextNotes.find((item) => noteKey(item) === focusedNoteKey.value)
      if (existing) {
        nextNotes = [existing, ...nextNotes.filter((item) => noteKey(item) !== focusedNoteKey.value)]
      } else {
        try {
          const focusedResponse = await getNote(focusedNoteKey.value)
          const focusedNote = focusedResponse?.data?.note || focusedResponse?.data?.data || focusedResponse?.data
          if (focusedNote) {
            nextNotes = [focusedNote, ...nextNotes]
          }
        } catch {
          const focusedNote = await getOfflineNoteByIdentifier(focusedNoteKey.value)
          if (focusedNote) {
            nextNotes = [focusedNote, ...nextNotes]
          }
        }
      }
    }

    notes.value = nextNotes

    tagOptions.value = tagResult.status === 'fulfilled' ? normalizeTagBuckets(tagResult.value?.data) : []
    const normalizedVideos = videoResult.status === 'fulfilled' ? normalizeVideoList(videoResult.value?.data) : []
    if (normalizedVideos.length > 0) {
      await cacheVideoList(normalizedVideos)
    }
    videoOptions.value = videoResult.status === 'fulfilled' ? sortNotes(normalizedVideos) : []

    if (focusedNoteKey.value) {
      await nextTick()
      const target = document.querySelector(`[data-note-id="${focusedNoteKey.value}"]`)
      if (target?.scrollIntoView) {
        target.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }
  } catch (e) {
    if (shouldUseOfflineMemoryMode(e)) {
      await loadOfflineState()
      error.value = '当前后端不可达，已切换到本地离线笔记缓存'
    } else {
      error.value = e?.message || '加载失败'
    }
  } finally {
    loading.value = false
  }
}

const applyFilters = async () => {
  await syncRouteQuery()
  await reload()
}

const clearFilters = async () => {
  filters.search = ''
  filters.videoId = ''
  filters.tag = ''
  await applyFilters()
}

const toggleTag = async (name) => {
  filters.tag = filters.tag === name ? '' : name
  await applyFilters()
}

const goNewNote = () => {
  const query = {}
  if (filters.videoId) query.videoId = String(filters.videoId)
  if (selectedVideoTitle.value) query.videoTitle = selectedVideoTitle.value
  router.push({ path: '/notes/new', query })
}

const clearFocusState = async () => {
  const query = { ...route.query }
  delete query.noteId
  delete query.noteAction
  await router.replace({ path: route.path, query })
}
const buildExcerpt = (content) => {
  const text = String(content || '').replace(/\s+/g, ' ').trim()
  if (!text) return '暂无内容摘要。'
  return text.length > 72 ? `${text.slice(0, 72)}…` : text
}

const formatTime = (value) => {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString()
}

const formatTimestampSummary = (timestamps) => {
  const sorted = [...timestamps].sort((a, b) => Number(a?.time_seconds || 0) - Number(b?.time_seconds || 0))
  const first = sorted[0]
  const firstSecond = Number(first?.time_seconds || 0)
  const minutes = Math.floor(firstSecond / 60)
  const seconds = Math.floor(firstSecond % 60)
  const head = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  return sorted.length > 1 ? `${head} 等 ${sorted.length} 个时间点` : `${head} 重点时间点`
}

onMounted(reload)
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 12px 14px;
  border-radius: 18px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: rgba(242, 235, 248, 0.94);
  box-shadow: 0 10px 22px rgba(101, 87, 117, 0.09);
}

.topbar h2 {
  margin: 0;
  font-size: 18px;
}

.actions {
  display: flex;
  gap: 10px;
}

.link {
  border: 0;
  background: transparent;
  color: var(--primary);
  font-weight: 900;
}

.alert {
  padding: 10px 12px;
  border-radius: 12px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-weight: 700;
  margin-bottom: 12px;
}

.alert--bad {
  background: var(--lilac-bg);
  color: var(--lilac-text);
}

.alert--ok {
  background: var(--surface-lilac);
  color: var(--primary-deep);
}
.filter-card,
.card {
  border-radius: 22px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: linear-gradient(180deg, rgba(242, 235, 248, 0.98), rgba(242, 235, 248, 0.96));
  box-shadow: 0 16px 30px rgba(101, 87, 117, 0.08);
}

.filter-card {
  padding: 16px;
  display: grid;
  gap: 14px;
}

.filter-head,
.section-head,
.row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 900;
  color: #0f172a;
}

.section-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
}

.ghost {
  border: 1px solid rgba(32, 42, 55, 0.12);
  background: rgba(242, 235, 248, 0.98);
  color: #334155;
  border-radius: 12px;
  padding: 8px 12px;
  font-weight: 800;
}

.filter-grid {
  display: grid;
  gap: 12px;
}

.field {
  display: grid;
  gap: 6px;
}

.label {
  font-size: 12px;
  color: #64748b;
  font-weight: 900;
}

.input {
  width: 100%;
  min-width: 0;
  border: 1px solid rgba(32, 42, 55, 0.14);
  border-radius: 14px;
  padding: 11px 12px;
  font-size: 14px;
  background: rgba(242, 235, 248, 0.98);
}

.tag-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-chip,
.tag-pill,
.meta-pill {
  border-radius: 999px;
  font-size: 12px;
}

.tag-chip {
  border: 1px solid var(--primary-soft-strong);
  background: var(--surface-lilac);
  color: var(--primary-deep);
  padding: 8px 10px;
  font-weight: 800;
}

.tag-chip--active {
  background: linear-gradient(135deg, #665775, #8b799d);
  color: #f9fafb;
  border-color: transparent;
}

.tag-chip__count {
  margin-left: 4px;
  opacity: 0.76;
}

.filter-actions {
  display: flex;
  justify-content: flex-end;
}

.btn {
  border: 0;
  border-radius: 16px;
  padding: 11px 14px;
  font-weight: 900;
}

.btn--primary {
  color: #f9fafb;
  background: linear-gradient(135deg, #665775, #8b799d);
}

.skeleton,
.content,
.list {
  display: grid;
  gap: 12px;
}

.content {
  margin-top: 16px;
}

.sk-card {
  height: 112px;
  border-radius: 20px;
  background: linear-gradient(90deg, #f3f4f6, #e5e7eb, #f3f4f6);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
}

@keyframes shimmer {
  0% { background-position: 0% 0; }
  100% { background-position: 200% 0; }
}

.empty {
  margin-top: 16px;
  border-radius: 20px;
  padding: 18px;
  background: rgba(242, 235, 248, 0.92);
  color: #0f172a;
}

.empty__title {
  font-size: 14px;
  font-weight: 900;
}

.empty__tip {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.6;
  color: #475569;
}

.card {
  border: 0;
  text-align: left;
  padding: 16px;
  display: grid;
  gap: 10px;
  background: rgba(242, 235, 248, 0.98);
}

.card--focus {
  border: 1px solid var(--primary-soft-strong);
  box-shadow: 0 0 0 2px var(--primary-soft), 0 16px 30px rgba(101, 87, 117, 0.1);
}

.title {
  font-size: 15px;
  font-weight: 900;
  color: #0f172a;
  min-width: 0;
  overflow-wrap: anywhere;
}

.arrow {
  color: #9ca3af;
  font-style: normal;
  font-size: 22px;
}

.excerpt {
  color: #475569;
  font-size: 13px;
  line-height: 1.6;
  overflow-wrap: anywhere;
}

.meta-list,
.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.meta-pill {
  padding: 6px 10px;
  background: rgba(15, 23, 42, 0.06);
  color: #334155;
  font-weight: 800;
}

.meta-pill--video {
  background: var(--surface-lilac);
  color: var(--primary-deep);
}

.meta-pill--time {
  background: var(--surface-lilac-deep);
  color: var(--lilac-text);
}

.tag-pill {
  padding: 6px 10px;
  background: var(--surface-lilac-deep);
  color: var(--lilac-text);
  font-weight: 800;
}

.muted {
  color: var(--muted);
  font-size: 12px;
}

@media (max-width: 420px) {
  .filter-head,
  .section-head,
  .row {
    flex-direction: column;
  }

  .filter-actions {
    justify-content: stretch;
  }

  .btn {
    width: 100%;
  }
}
</style>
