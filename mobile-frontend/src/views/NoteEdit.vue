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
      <section v-if="selectedVideoLabel || hasPrefilledTimestamp || videoSummary" class="context-card">
        <div class="section-title">当前上下文</div>
        <div v-if="selectedVideoLabel" class="context-line">关联视频：{{ selectedVideoLabel }}</div>
        <div v-if="videoSummary" class="context-line">摘要已接入，可直接从摘要片段里挑选内容进入笔记。</div>
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

      <section v-if="hasVideoContext" class="card">
        <div class="section-head">
          <div>
            <div class="section-title">摘要关联片段</div>
            <div class="section-tip">按摘要主题整理字幕片段，可直接加入笔记正文和重点时间点。</div>
          </div>
          <div class="section-tip">{{ filteredSummarySegments.length }} 段</div>
        </div>

        <div v-if="videoContextLoading" class="empty-inline">正在加载摘要和字幕片段…</div>
        <div v-else-if="videoContextError" class="inline-note inline-note--bad">{{ videoContextError }}</div>
        <template v-else>
          <div v-if="videoSummary" class="summary-panel">
            <div class="summary-panel__title">当前摘要</div>
            <div class="summary-panel__body">{{ videoSummary }}</div>
          </div>

          <div v-if="summaryThemeOptions.length > 0" class="tag-row">
            <button class="tag-chip" :class="{ 'tag-chip--active': activeSummaryTheme === 'all' }" @click="activeSummaryTheme = 'all'">
              全部
            </button>
            <button
              v-for="theme in summaryThemeOptions"
              :key="theme"
              class="tag-chip"
              :class="{ 'tag-chip--active': activeSummaryTheme === theme }"
              @click="activeSummaryTheme = theme"
            >
              {{ theme }}
            </button>
          </div>

          <div v-if="filteredSummarySegments.length === 0" class="empty-inline">当前摘要下还没有可选片段。</div>
          <div v-else class="segment-list">
            <button
              v-for="segment in filteredSummarySegments"
              :key="segment.localKey"
              class="segment-card"
              @click="applySummarySegment(segment)"
            >
              <div class="segment-card__head">
                <span class="segment-card__theme">{{ segment.summaryTheme || segment.title || '字幕片段' }}</span>
                <span class="segment-card__time">{{ formatTimeRange(segment.start_time, segment.end_time) }}</span>
              </div>
              <div v-if="segment.title && segment.title !== segment.summaryTheme" class="segment-card__title">{{ segment.title }}</div>
              <div class="segment-card__text">{{ segment.text }}</div>
              <div class="segment-card__action">{{ isSummarySegmentApplied(segment) ? '已加入笔记' : '加入笔记' }}</div>
            </button>
          </div>
        </template>
      </section>

      <section class="card">
        <div class="section-head">
          <div>
            <div class="section-title">重点时间点</div>
            <div class="section-tip">新增秒数后会自动补最近字幕，并把对应片段追加到笔记正文。</div>
          </div>
          <div class="section-tip">{{ timestamps.length }} 个</div>
        </div>

        <div v-if="timestamps.length === 0" class="empty-inline">当前还没有重点时间点。</div>

        <div v-else class="timestamp-list">
          <div v-for="item in timestamps" :key="item.localKey" class="timestamp-card">
            <div class="timestamp-grid">
              <label class="field">
                <span class="label">秒数</span>
                <input
                  v-model="item.timeSeconds"
                  class="input"
                  type="number"
                  min="0"
                  step="0.1"
                  placeholder="例如 92.5"
                  @blur="autofillTimestampSubtitle(item)"
                />
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
              <input
                v-model="draftTimestamp.timeSeconds"
                class="input"
                type="number"
                min="0"
                step="0.1"
                placeholder="例如 120"
                @blur="autofillDraftTimestamp"
              />
            </label>

            <label class="field field--wide">
              <span class="label">新增字幕/提示</span>
              <input v-model.trim="draftTimestamp.subtitleText" class="input" placeholder="会按秒数自动补最近字幕，也可手动修改" />
            </label>
          </div>

          <button class="mini" @click="addDraftTimestamp">添加时间点</button>
          <div v-if="hasVideoContext" class="section-tip">如果已选择视频，系统会优先用该秒数附近的字幕和摘要片段补齐内容。</div>
        </div>
      </section>

      <button v-if="!isNew" class="danger" @click="remove" :disabled="saving">删除笔记</button>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { addNoteTimestamp, createNote, deleteNote, deleteNoteTimestamp, getNote, getNoteTags, updateNote } from '@/api/note'
import { getMergedVideoSubtitles, getVideoSubtitles } from '@/api/subtitle'
import { getVideo, getVideoList } from '@/api/video'

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
const videoContextLoading = ref(false)
const videoContextError = ref('')
const videoSummary = ref('')
const videoSubtitles = ref([])
const summarySegments = ref([])
const activeSummaryTheme = ref('all')

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

const SUMMARY_STOPWORDS = new Set(['本节', '当前', '视频', '课程', '重点', '学习', '内容', '讲解', '相关', '这里', '这个'])

const hasPrefilledTimestamp = computed(
  () =>
    isNew.value &&
    (Boolean(route.query.time) || Boolean(route.query.subtitle)) &&
    timestamps.value.length > 0
)
const hasVideoContext = computed(() => Number(form.videoId || 0) > 0)
const selectedVideoId = computed(() => Number(form.videoId || 0))
const summaryOutline = computed(() => parseSummaryOutline(videoSummary.value))
const summaryThemeOptions = computed(() => {
  const values = [...summaryOutline.value, ...summarySegments.value.map((item) => normalizeText(item.summaryTheme))]
  return [...new Set(values.filter(Boolean))].slice(0, 8)
})
const filteredSummarySegments = computed(() => {
  if (activeSummaryTheme.value === 'all') return summarySegments.value
  return summarySegments.value.filter((item) => normalizeText(item.summaryTheme) === activeSummaryTheme.value)
})

const selectedVideoLabel = computed(() => {
  const currentVideoId = String(form.videoId || '')
  if (!currentVideoId) return normalizeText(route.query.videoTitle)
  return (
    videoOptions.value.find((item) => String(item.id) === currentVideoId)?.title ||
    normalizeText(route.query.videoTitle)
  )
})

const normalizeText = (value) => String(value || '').trim()
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
const normalizeTagBuckets = (payload) => {
  const list = payload?.data || payload?.tags || payload || []
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

const cleanSummaryLine = (value) =>
  normalizeText(value)
    .replace(/^[-•●▪]+\s*/, '')
    .replace(/^\d+[\.\)、]\s*/, '')
    .replace(/^(主题|学习重点|重点|总结|核心内容)[:：]\s*/, '')

const parseSummaryOutline = (summary) => {
  const text = normalizeText(summary)
  if (!text) return []

  const lines = text
    .split(/\n+/)
    .flatMap((line) => {
      const normalized = cleanSummaryLine(line)
      if (!normalized) return []
      if (/[。；;]/.test(normalized) && normalized.length > 18) {
        return normalized.split(/[。；;]/).map(cleanSummaryLine).filter(Boolean)
      }
      return [normalized]
    })
    .filter((item) => item && item !== '学习重点')

  return [...new Set(lines)].slice(0, 8)
}

const buildSearchTokens = (text) => {
  const normalized = normalizeText(text).replace(/[^\u4e00-\u9fa5a-zA-Z0-9]/g, '')
  const tokens = new Set()
  const latinMatches = normalized.match(/[A-Za-z0-9]{2,}/g) || []
  latinMatches.forEach((item) => tokens.add(item.toLowerCase()))

  const chineseMatches = normalized.match(/[\u4e00-\u9fa5]{2,}/g) || []
  chineseMatches.forEach((item) => {
    if (item.length <= 6 && !SUMMARY_STOPWORDS.has(item)) tokens.add(item)
    for (let size = 2; size <= Math.min(4, item.length); size += 1) {
      for (let index = 0; index <= item.length - size; index += 1) {
        const token = item.slice(index, index + size)
        if (!SUMMARY_STOPWORDS.has(token)) tokens.add(token)
      }
    }
  })

  return [...tokens].filter((item) => item.length >= 2)
}

const scoreSummaryThemeMatch = (segment, theme) => {
  const haystack = normalizeText(`${segment?.title || ''} ${segment?.text || ''}`).toLowerCase()
  return buildSearchTokens(theme).reduce((score, token) => {
    return haystack.includes(token.toLowerCase()) ? score + token.length : score
  }, 0)
}

const resolveSummaryTheme = (segment, themes) => {
  const fallbackTitle = normalizeText(segment?.title)
  if (themes.length === 0) return fallbackTitle

  let bestTheme = ''
  let bestScore = 0
  themes.forEach((theme) => {
    const currentScore = scoreSummaryThemeMatch(segment, theme)
    if (currentScore > bestScore) {
      bestScore = currentScore
      bestTheme = theme
    }
  })

  return bestScore > 0 ? bestTheme : fallbackTitle
}

const buildDecoratedSegments = (segments, themes, videoId) =>
  sortByStartTime(segments)
    .map((item, index) => ({
      localKey: `segment-${videoId}-${index}-${Number(item?.start_time || 0)}`,
      start_time: Number(item?.start_time || 0),
      end_time: Number(item?.end_time || item?.start_time || 0),
      text: normalizeText(item?.text),
      title: normalizeText(item?.title),
      summaryTheme: resolveSummaryTheme(item, themes)
    }))
    .filter((item) => item.text)

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
  const [videoResult, tagResult] = await Promise.allSettled([getVideoList(1, 100), getNoteTags()])
  videoOptions.value = videoResult.status === 'fulfilled' ? sortByUpdated(normalizeVideoList(videoResult.value?.data)) : []
  popularTags.value = tagResult.status === 'fulfilled' ? normalizeTagBuckets(tagResult.value?.data) : []
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
    getVideoSubtitles(videoId),
    getMergedVideoSubtitles(videoId)
  ])

  try {
    const videoDetail = videoResult.status === 'fulfilled' ? normalizeVideo(videoResult.value?.data) : null
    const currentSummary = normalizeText(videoDetail?.summary)
    const rawSubtitles =
      subtitleResult.status === 'fulfilled' ? sortByStartTime(normalizeSubtitleList(subtitleResult.value?.data)) : []
    const mergedSegments =
      segmentResult.status === 'fulfilled' ? sortByStartTime(normalizeSubtitleSegments(segmentResult.value?.data)) : []
    const themes = parseSummaryOutline(currentSummary)
    const segmentSource = mergedSegments.length > 0 ? mergedSegments : rawSubtitles

    videoSummary.value = currentSummary
    videoSubtitles.value = rawSubtitles
    summarySegments.value = buildDecoratedSegments(segmentSource, themes, videoId)

    if (!summarySegments.value.length && !videoSubtitles.value.length) {
      videoContextError.value = '当前视频还没有可用字幕，暂时无法自动回填重点时间点。'
    }
  } catch (e) {
    videoContextError.value = e?.message || '视频摘要与字幕上下文加载失败'
  } finally {
    videoContextLoading.value = false
  }
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
const findMatchingSegment = (seconds) => findClosestTimedItem(summarySegments.value, seconds, 36)

const suggestSubtitleText = (seconds) => {
  const subtitle = findMatchingSubtitle(seconds)
  if (subtitle?.text) return compactText(subtitle.text)
  const segment = findMatchingSegment(seconds)
  return compactText(segment?.text)
}

const buildContextSegmentForSeconds = (seconds, explicitText = '') => {
  const matchedSegment = findMatchingSegment(seconds)
  if (matchedSegment) return matchedSegment

  const matchedSubtitle = findMatchingSubtitle(seconds)
  if (matchedSubtitle) {
    return {
      start_time: Number(matchedSubtitle.start_time || 0),
      end_time: Number(matchedSubtitle.end_time || matchedSubtitle.start_time || 0),
      text: normalizeText(matchedSubtitle.text),
      title: '',
      summaryTheme: ''
    }
  }

  const fallbackText = normalizeText(explicitText)
  if (!fallbackText) return null
  return {
    start_time: seconds,
    end_time: seconds,
    text: fallbackText,
    title: '重点时间点',
    summaryTheme: ''
  }
}

const formatTimeRange = (startTime, endTime) => {
  const startLabel = formatSeconds(startTime)
  const endLabel = formatSeconds(endTime)
  return startLabel === endLabel ? startLabel : `${startLabel}-${endLabel}`
}

const buildSegmentContentBlock = (segment) => {
  const contentText = normalizeText(segment?.text || segment?.subtitle_text)
  if (!contentText) return ''

  const startTime = Number(segment?.start_time ?? segment?.time_seconds ?? 0)
  const endTime = Number(segment?.end_time ?? segment?.time_seconds ?? startTime)
  const title = normalizeText(segment?.summaryTheme || segment?.title)
  const lines = [`[${formatTimeRange(startTime, endTime)}]${title ? ` ${title}` : ''}`]

  if (segment?.title && segment?.summaryTheme && normalizeText(segment.title) !== normalizeText(segment.summaryTheme)) {
    lines.push(`片段：${normalizeText(segment.title)}`)
  }

  lines.push(contentText)
  return lines.join('\n')
}

const appendSegmentToNoteContent = (segment) => {
  const block = buildSegmentContentBlock(segment)
  if (!block) return

  const current = normalizeText(form.content)
  if (current.includes(block)) return
  form.content = current ? `${current}\n\n${block}` : block
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

const autofillDraftTimestamp = () => {
  if (normalizeText(draftTimestamp.subtitleText)) return
  const seconds = parsePositiveSeconds(draftTimestamp.timeSeconds)
  if (seconds == null) return
  draftTimestamp.subtitleText = suggestSubtitleText(seconds)
}

const autofillTimestampSubtitle = (item) => {
  if (!item || normalizeText(item.subtitleText)) return
  const seconds = parsePositiveSeconds(item.timeSeconds)
  if (seconds == null) return
  item.subtitleText = suggestSubtitleText(seconds)
}

const isSummarySegmentApplied = (segment) => {
  const seconds = Number(segment?.start_time || 0)
  const block = buildSegmentContentBlock(segment)
  return hasTimestampAt(seconds) && normalizeText(form.content).includes(block)
}

const applySummarySegment = (segment) => {
  const seconds = Number(segment?.start_time || 0)
  const subtitleText = compactText(segment?.text)
  addTimestampEntry(seconds, subtitleText)
  appendSegmentToNoteContent(segment)
  error.value = ''
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

  const timeNumber = parsePositiveSeconds(rawTime)
  if (timeNumber == null) {
    error.value = '时间点必须是大于等于 0 的数字'
    return
  }

  const resolvedSubtitle = subtitle || suggestSubtitleText(timeNumber)
  const added = addTimestampEntry(timeNumber, resolvedSubtitle)
  if (!added) {
    error.value = '该重点时间点已经存在'
    return
  }

  const contextSegment = buildContextSegmentForSeconds(timeNumber, resolvedSubtitle)
  if (contextSegment) appendSegmentToNoteContent(contextSegment)

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
  background: rgba(251, 245, 239, 0.92);
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
  background: linear-gradient(180deg, #ffffff, #f7f0ea);
  border: 1px solid rgba(32, 42, 55, 0.09);
  box-shadow: 0 16px 30px rgba(101, 87, 117, 0.1);
}

.context-card {
  background: linear-gradient(180deg, rgba(139, 121, 157, 0.12), rgba(200, 171, 108, 0.08));
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
  background: rgba(239, 68, 68, 0.1);
  color: #b91c1c;
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

.summary-panel {
  margin-top: 12px;
  border-radius: 18px;
  padding: 14px;
  background: rgba(200, 171, 108, 0.12);
  display: grid;
  gap: 8px;
}

.summary-panel__title {
  font-size: 12px;
  font-weight: 900;
  color: #8f7040;
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
  color: #8f7040;
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
  border: 1px solid rgba(200, 171, 108, 0.18);
  background: rgba(200, 171, 108, 0.12);
  color: #8f7040;
  border-radius: 999px;
  padding: 8px 10px;
  font-weight: 800;
  font-size: 12px;
}

.tag-chip--active {
  background: #8f7040;
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
  color: #7a667f;
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
  background: rgba(200, 171, 108, 0.14);
  color: #8f7040;
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
