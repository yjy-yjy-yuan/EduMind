<template>
  <div class="page">
    <header class="topbar">
      <div class="topbar__copy">
        <h2>导入学习内容</h2>
        <p>本地上传和推荐导入都走同一条处理链路。</p>
      </div>
      <button class="link" @click="resetAll" :disabled="busy">重置</button>
    </header>

    <div v-if="hasRecommendationImport" class="card import-banner">
      <div class="import-banner__top">
        <div>
          <div class="card-title">推荐导入</div>
          <div class="muted">你正在承接来自 {{ importSourceLabel }} 的推荐内容，提交后会进入现有下载与处理链路，不会直接当作已入库视频播放。</div>
        </div>
        <span class="import-badge">{{ importSourceLabel }}</span>
      </div>
      <div class="import-banner__url">{{ importPreviewUrl }}</div>
      <div class="import-banner__actions">
        <button class="btn btn--primary" @click="uploadUrl" :disabled="!videoUrl || busy">{{ busy ? '提交中…' : '提交当前推荐链接' }}</button>
        <button class="btn" @click="router.push('/recommendations')" :disabled="busy">返回推荐页</button>
      </div>
    </div>

    <div class="card" :class="{ 'card--active': submissionMode === 'file' }">
      <WhisperModelPicker
        title="Whisper 模型"
        :model="processingSettings.model"
        :options="whisperModelOptions"
        :disabled="busy"
        @select="selectProcessingModel"
      />
    </div>

    <div class="card" :class="{ 'card--active': submissionMode === 'file' }">
      <div class="card-title">本地视频</div>
      <input
        ref="fileInputRef"
        class="file file--hidden"
        type="file"
        accept=".mp4,.avi,.mov,.mkv,.webm,.flv"
        @change="onFileChange"
        :disabled="busy"
      />
      <div class="file-picker" :class="{ 'file-picker--selected': hasVisibleFileMeta }">
        <button class="file-picker__button" type="button" @click="openFilePicker" :disabled="busy">
          {{ hasVisibleFileMeta ? '重新选择视频' : '选择本地视频' }}
        </button>
        <div class="file-picker__meta">
          <strong class="file-picker__title">{{ currentFileDisplayName }}</strong>
          <span class="file-picker__desc">{{ currentFileDisplayHint }}</span>
        </div>
      </div>
      <button class="btn btn--primary" @click="uploadFile" :disabled="!file || busy">
        {{ busy ? '上传中…' : '开始上传' }}
      </button>
      <button class="btn btn--native" @click="startNativeOfflineTranscriptionFlow" :disabled="busy || nativeBusy">
        {{ nativeBusy ? '准备本地离线转录…' : 'iOS 本地离线转录' }}
      </button>
      <label class="field field--native">
        <span class="field-label">本地识别语言/方言</span>
        <select
          class="input"
          :value="processingSettings.nativeLocale"
          :disabled="busy || nativeBusy"
          @change="selectNativeLocale($event.target.value)"
        >
          <option v-for="option in NATIVE_LOCALE_OPTIONS" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </label>
      <div class="muted">当前处理：{{ processingSettingsSummary }}</div>
      <div class="muted">本地离线转录优先使用 iOS 原生识别能力，只处理当前设备上的本地视频，不依赖 FastAPI。</div>
      <div class="muted">如果视频是粤语、吴语、繁体中文或明显口音内容，请先切换到更接近的本地识别语言/方言。</div>

      <div v-if="busy" class="progress">
        <div class="bar" :style="{ width: `${progress}%` }"></div>
      </div>
      <div v-if="busy" class="muted">进度：{{ progress }}%</div>
      <div class="muted">离线补跑仅适用于已配置真实后端地址但暂时不可达；纯 UI ONLY 演示模式不会进入真实离线补跑。</div>
    </div>

    <div class="card" :class="{ 'card--active': submissionMode === 'url', 'card--spotlight': hasRecommendationImport }">
      <div class="card-title">视频链接</div>
      <div v-if="hasRecommendationImport" class="import-tip">
        <span class="import-badge import-badge--inline">{{ importSourceLabel }}</span>
        <span class="muted">当前链接来自推荐系统，提交后不会直接播放，而是进入导入学习流程。</span>
      </div>
      <input class="input" v-model.trim="videoUrl" placeholder="请输入视频链接（B站/YouTube等）" :disabled="busy" />
      <button class="btn" @click="uploadUrl" :disabled="!videoUrl || busy">{{ busy ? '提交中…' : '提交链接' }}</button>
      <div class="muted">支持：B站、YouTube、中国大学慕课（icourse163）</div>
      <div class="muted">将沿用当前处理设置：{{ processingSettingsSummary }}</div>
    </div>

    <div v-if="uploadRecommendationItems.length > 0" class="card upload-followup">
      <div class="card-head">
        <div class="card-title">上传后推荐</div>
        <div class="card-head-actions">
          <button class="link link--small" @click="openLatestUploadedVideo" :disabled="!latestUploadedVideoId">查看刚上传内容</button>
          <button class="link link--small" @click="clearUploadRecommendations" :disabled="busy">收起</button>
        </div>
      </div>
      <div class="muted">{{ uploadRecommendationIntro }}</div>
      <div v-if="uploadRecommendationQuerySummary" class="upload-followup__context">
        当前推荐围绕：{{ uploadRecommendationQuerySummary }}
      </div>
      <div class="upload-followup__list">
        <article v-for="item in uploadRecommendationItems" :key="item.key" class="upload-followup__item">
          <div class="upload-followup__top">
            <span class="recent-tag">{{ item.reasonLabel }}</span>
            <span class="recent-tag recent-tag--soft">{{ item.sourceLabel }}</span>
          </div>
          <strong class="upload-followup__title">{{ item.title }}</strong>
          <p class="upload-followup__desc">{{ item.summaryText }}</p>
          <div v-if="item.tags.length > 0" class="upload-followup__tags">
            <span v-for="tag in item.tags.slice(0, 4)" :key="`${item.key}-${tag}`" class="upload-followup__tag">{{ tag }}</span>
          </div>
          <div class="upload-followup__meta">
            <span v-if="item.statusText">{{ item.statusText }}</span>
            <span v-if="item.subjectText">{{ item.subjectText }}</span>
            <span v-if="item.timeText">{{ item.timeText }}</span>
          </div>
          <div v-if="item.importHint" class="upload-followup__hint">{{ item.importHint }}</div>
          <button
            class="btn btn--primary"
            @click="openUploadRecommendation(item)"
            :disabled="item.primaryActionDisabled || busy"
          >
            {{ item.primaryActionLabel }}
          </button>
        </article>
      </div>
    </div>

    <div v-if="nativeTask" class="card">
      <div class="card-head">
        <div class="card-title">iOS 本地离线转录</div>
        <div class="card-head-actions">
          <button class="link link--small" @click="openNativeTaskDetail(nativeTask.taskId)" :disabled="!nativeTask.taskId">查看详情</button>
          <button class="link link--small" @click="clearNativeTask" :disabled="nativeBusy">清除结果</button>
        </div>
      </div>
      <div class="recent-title">{{ nativeTask.fileName || '本地视频' }}</div>
      <div class="muted">
        {{ readableSize(nativeTask.fileSize) }} · {{ nativeTask.engineLabel }} · {{ nativeTask.localeLabel }}
      </div>
      <div class="recent-meta">
        <span class="status" :class="statusClass(nativeTask.status)">{{ statusText(nativeTask.status) }}</span>
      </div>
      <div class="recent-progress">
        <div class="recent-progress__text">{{ displayProgress(nativeTask.progress) }}% · {{ nativeTask.currentStep }}</div>
        <div class="progress progress--compact">
          <div class="bar bar--native" :style="{ width: `${displayProgress(nativeTask.progress)}%` }"></div>
        </div>
      </div>
      <div v-if="nativeTask.transcriptText" class="native-result">
        <div class="card-title">转录文本</div>
        <pre class="native-result__text">{{ nativeTask.transcriptText }}</pre>
      </div>
      <div v-if="nativeTask.errorMessage" class="alert alert--bad">{{ nativeTask.errorMessage }}</div>
    </div>

    <div v-if="nativeHistory.length > 0" class="card">
      <div class="card-head">
        <div class="card-title">本地转录历史</div>
        <button class="link link--small" @click="reloadNativeHistory" :disabled="nativeBusy">刷新</button>
      </div>
      <div class="recent-list">
        <div v-for="item in nativeHistory" :key="item.taskId" class="recent-item">
          <div class="recent-main">
            <div class="recent-title">{{ item.fileName || '本地视频' }}</div>
            <div class="muted">{{ readableSize(item.fileSize) }} · {{ formatTimeText(item.updatedAt || item.createdAt) }}</div>
            <div class="muted">{{ nativeEngineLabel(item.engine) }} · {{ nativeLocaleLabel(item.locale) }}</div>
            <div class="recent-meta">
              <span class="status" :class="statusClass(item.status)">{{ statusText(item.status) }}</span>
            </div>
          </div>
          <div class="recent-actions">
            <button class="mini" @click="openNativeTaskDetail(item.taskId)">查看</button>
            <button class="mini mini--warn" @click="removeNativeHistoryItem(item.taskId)" :disabled="nativeBusy">删除</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="recentUploads.length > 0" class="card">
      <div class="card-head">
        <div class="card-title">最近上传</div>
        <div class="card-head-actions">
          <button class="link link--small" @click="syncRecentStatuses" :disabled="busy || syncingRecent">
            {{ syncingRecent ? '刷新中…' : '刷新状态' }}
          </button>
          <button class="link link--small" @click="clearRecentUploads" :disabled="busy || syncingRecent">清空</button>
        </div>
      </div>
      <div class="filters">
        <button
          v-for="f in STATUS_FILTERS"
          :key="f.value"
          class="filter"
          :class="{ 'filter--active': statusFilter === f.value }"
          @click="statusFilter = f.value"
        >
          {{ f.label }}
        </button>
      </div>
      <div class="recent-list">
        <div v-for="item in filteredRecentUploads" :key="item.key" class="recent-item">
          <div class="recent-main">
            <div class="recent-title">{{ item.title }}</div>
            <div class="muted">{{ item.typeText }} · {{ item.timeText }}</div>
            <div v-if="recentModelText(item)" class="muted">{{ recentModelText(item) }}</div>
            <div class="recent-meta">
              <span class="status" :class="statusClass(item.status)">{{ statusText(item.status) }}</span>
            </div>
            <div v-if="isActiveStatus(item.status)" class="recent-progress">
              <div class="recent-progress__text">{{ displayProgress(item.progress) }}% · {{ item.currentStep || '处理中' }}</div>
              <div class="progress progress--compact">
                <div class="bar" :style="{ width: `${displayProgress(item.progress)}%` }"></div>
              </div>
            </div>
          </div>
          <div class="recent-actions">
            <span class="recent-tag" :class="recentTagClass(item)">
              {{ recentTagText(item) }}
            </span>
            <button class="mini" @click="openRecent(item)" :disabled="!item.videoId">查看</button>
            <button
              v-if="item.status === 'failed' && item.videoId"
              class="mini mini--warn"
              @click="retryRecent(item)"
              :disabled="busy || syncingRecent || item.retrying || !item.videoId"
            >
              {{ item.retrying ? '重试中…' : '重试处理' }}
            </button>
          </div>
        </div>
        <div v-if="filteredRecentUploads.length === 0" class="empty">当前筛选下没有记录。</div>
      </div>
    </div>

    <div v-if="message" class="alert alert--ok">{{ message }}</div>
    <div v-if="error" class="alert alert--bad">{{ error }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  generateTranscriptSummary,
  getVideoProcessingOptions,
  getVideoStatus,
  hasLiveVideoBackend,
  getVideoUploadQueueableMessage,
  isVideoUploadQueueableError,
  processVideo,
  syncOfflineTranscriptToVideo,
  uploadLocalVideo,
  uploadVideoUrl
} from '@/api/video'
import WhisperModelPicker from '@/components/WhisperModelPicker.vue'
import {
  OFFLINE_QUEUE_EVENT_NAME,
  OFFLINE_TASK_STATUSES,
  createLocalUploadTask,
  createUrlImportTask,
  deleteOfflineTask,
  flushOfflineQueue,
  getOfflineTasks
} from '@/services/offlineQueue'
import {
  appendProcessingSettingsToFormData,
  buildProcessPayload,
  getProcessingSettings,
  getWhisperModelOptions,
  languageLabel,
  NATIVE_LOCALE_OPTIONS,
  nativeLocaleLabel,
  resolveNativeTranscriptionLocale,
  saveWhisperModelCatalog,
  saveProcessingSettings,
  summaryStyleLabel,
  whisperModelLabel
} from '@/services/processingSettings'
import { normalizeVideoStatus, videoStatusText, videoStatusTone } from '@/services/videoStatus'
import {
  NATIVE_OFFLINE_TRANSCRIPTION_COMPLETED_EVENT,
  NATIVE_OFFLINE_TRANSCRIPTION_FAILED_EVENT,
  NATIVE_OFFLINE_TRANSCRIPTION_PROGRESS_EVENT,
  hasNativeBridge,
  onNativeEvent,
  startNativeOfflineTranscription
} from '@/services/nativeBridge'
import {
  NATIVE_OFFLINE_TRANSCRIPTS_EVENT_NAME,
  deleteNativeOfflineTranscript,
  getNativeOfflineTranscript,
  getLatestNativeOfflineTranscript,
  listNativeOfflineTranscripts,
  saveNativeOfflineTranscript
} from '@/services/nativeOfflineTranscripts'
import { storageGet, storageRemove, storageSet } from '@/utils/storage'

const router = useRouter()
const route = useRoute()
const fileInputRef = ref(null)

const file = ref(null)
const savedFileMeta = ref(null)
const videoUrl = ref('')
const submissionMode = ref('file')
const recommendationSource = ref('')
const busy = ref(false)
const nativeBusy = ref(false)
const progress = ref(0)
const message = ref('')
const error = ref('')
const recentUploads = ref([])
const nativeTask = ref(null)
const nativeHistory = ref([])
const syncingRecent = ref(false)
const statusFilter = ref('all')
let recentStatusTimer = null
const processingSettings = ref(getProcessingSettings())
const whisperModelOptions = ref(getWhisperModelOptions())

const MAX_UPLOAD_SIZE_BYTES = 500 * 1024 * 1024
const ALLOWED_EXTENSIONS = new Set(['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv'])
const RECENT_UPLOADS_KEY = 'm_recent_uploads'
const MAX_RECENT_UPLOADS = 8
const STATUS_FILTERS = [
  { value: 'all', label: '全部' },
  { value: 'failed', label: '失败' },
  { value: 'active', label: '进行中' },
  { value: 'completed', label: '已完成' }
]
let syncingOfflineRecent = false
const nativeEventDisposers = []
const UPLOAD_RECOMMENDATION_SCENE_LABELS = {
  home: '首页推荐',
  continue: '继续学习',
  review: '复盘推荐',
  related: '相关推荐'
}

const processingSettingsSummary = computed(() => {
  const current = processingSettings.value || getProcessingSettings()
  const parts = [
    `${whisperModelLabel(current.model)} 模型`,
    languageLabel(current.language)
  ]
  if (current.nativeLocale && current.nativeLocale !== 'auto') {
    parts.push(`端侧${nativeLocaleLabel(current.nativeLocale)}`)
  }
  parts.push(
    `${summaryStyleLabel(current.summaryStyle)}摘要`
  )
  if (current.autoGenerateSummary) parts.push('自动摘要')
  if (current.autoGenerateTags) parts.push('自动标签')
  return parts.join(' · ')
})
const hasRecommendationImport = computed(() => Boolean(recommendationSource.value || videoUrl.value) && submissionMode.value === 'url')
const importSourceLabel = computed(() => recommendationSource.value || '推荐系统')
const importPreviewUrl = computed(() => String(videoUrl.value || '').trim() || '等待带入推荐链接')
const hasVisibleFileMeta = computed(() => Boolean(file.value || savedFileMeta.value))
const currentFileDisplayName = computed(() => {
  if (file.value?.name) return file.value.name
  if (savedFileMeta.value?.name) return savedFileMeta.value.name
  return '未选择本地视频'
})
const currentFileDisplayHint = computed(() => {
  if (file.value) {
    return `已选择 · ${readableSize(file.value.size)}`
  }
  if (savedFileMeta.value?.name) {
    return `上次选择 · ${readableSize(savedFileMeta.value.size)} · 返回后需重新选择`
  }
  return '支持 MP4、AVI、MOV、MKV、WEBM、FLV'
})
const uploadRecommendationPayload = ref(null)
const latestUploadedVideoId = ref(0)
const latestUploadedTitle = ref('')
const normalizeRecommendationItems = (payload) => Array.isArray(payload?.items) ? payload.items : []
const normalizeRecommendationQuery = (payload) => payload?.external_query || null
const resolveRecommendationItemKey = (item, index = 0) =>
  String(item?.id || item?.video_id || item?.external_url || item?.url || `upload-recommendation-${index}`)
const resolveRecommendationUrl = (item) =>
  String(item?.external_url || item?.target_url || item?.source_url || item?.url || item?.link || '').trim()
const isExternalRecommendationItem = (item) => {
  const itemType = String(item?.item_type || item?.content_type || '').trim().toLowerCase()
  if (item?.is_external === true) return true
  return ['external', 'external_candidate', 'candidate'].includes(itemType) || (!item?.id && Boolean(resolveRecommendationUrl(item)))
}
const parseRecommendationActionTarget = (target) => {
  const text = String(target || '').trim()
  if (!text || !text.startsWith('/')) return null
  const [path, search = ''] = text.split('?')
  if (!search) return { path }
  const params = new URLSearchParams(search)
  const query = {}
  params.forEach((value, key) => {
    query[key] = value
  })
  return { path, query }
}
const formatRecommendationTime = (rawValue) => {
  if (!rawValue) return ''
  const date = new Date(rawValue)
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleString()
}
const decorateUploadRecommendationItem = (item, index = 0) => {
  const tags = Array.isArray(item?.tags) ? item.tags.filter(Boolean).map((tag) => String(tag).trim()) : []
  const isExternal = isExternalRecommendationItem(item)
  const sourceLabel = String(item?.source_label || item?.upload_source_label || (isExternal ? '站外候选' : '站内视频')).trim() || '站内视频'
  return {
    ...item,
    key: resolveRecommendationItemKey(item, index),
    title: String(item?.title || '未命名内容'),
    tags,
    sourceLabel,
    reasonLabel: String(item?.reason_label || '推荐'),
    summaryText: String(item?.reason_text || item?.summary || '可继续从这里进入学习链路。'),
    statusText: item?.status ? videoStatusText(item.status) : '',
    timeText: formatRecommendationTime(item?.upload_time || item?.updated_at || item?.created_at),
    subjectText: String(item?.subject || '').trim() ? `科目 · ${String(item.subject).trim()}` : '',
    importHint: String(item?.import_hint || '').trim(),
    primaryActionLabel: String(item?.action_label || '').trim() || (isExternal ? '导入学习' : '打开详情'),
    primaryActionDisabled: isExternal ? !Boolean(item?.can_import ?? resolveRecommendationUrl(item)) : false,
    actionTarget: String(item?.action_target || '').trim()
  }
}
const uploadRecommendationItems = computed(() =>
  normalizeRecommendationItems(uploadRecommendationPayload.value).map((item, index) => decorateUploadRecommendationItem(item, index))
)
const uploadRecommendationIntro = computed(() => {
  const scene = String(uploadRecommendationPayload.value?.scene || '').trim().toLowerCase()
  const label = UPLOAD_RECOMMENDATION_SCENE_LABELS[scene] || '下一步推荐'
  const title = latestUploadedTitle.value ? `《${latestUploadedTitle.value}》` : '当前上传内容'
  return `${title} 上传后，后端已自动返回 ${label}，你可以直接从这里决定下一步学什么。`
})
const uploadRecommendationQuerySummary = computed(() => {
  const query = normalizeRecommendationQuery(uploadRecommendationPayload.value)
  if (!query) return ''
  const parts = [query.subject, query.primary_topic].filter(Boolean)
  if (Array.isArray(query.preferred_tags) && query.preferred_tags.length > 0) {
    parts.push(`优先标签：${query.preferred_tags.join('、')}`)
  }
  return parts.join(' · ')
})

const clearUploadRecommendations = () => {
  uploadRecommendationPayload.value = null
}

const storeUploadRecommendations = (payload, videoId, title) => {
  uploadRecommendationPayload.value = payload && normalizeRecommendationItems(payload).length > 0 ? payload : null
  latestUploadedVideoId.value = Number(videoId || 0) || 0
  latestUploadedTitle.value = String(title || '').trim()
}

const openLatestUploadedVideo = () => {
  if (!latestUploadedVideoId.value) return
  router.push(`/videos/${latestUploadedVideoId.value}`)
}

const openUploadRecommendation = (item) => {
  if (isExternalRecommendationItem(item) && item.primaryActionDisabled) {
    error.value = item.importHint || '当前站外候选暂不可直接导入。'
    return
  }
  const actionLocation = parseRecommendationActionTarget(item.actionTarget || item?.action_target)
  if (actionLocation) {
    router.push(actionLocation)
    return
  }
  if (isExternalRecommendationItem(item)) {
    const url = resolveRecommendationUrl(item)
    if (!url) return
    router.push({ path: '/upload', query: { mode: 'url', url, source: item.sourceLabel || '站外推荐' } })
    return
  }
  if (item?.task_id) {
    router.push(`/local-transcripts/${item.task_id}`)
    return
  }
  if (item?.id) {
    router.push(`/videos/${item.id}`)
  }
}

const selectProcessingModel = (model) => {
  if (busy.value) return
  processingSettings.value = saveProcessingSettings({
    ...processingSettings.value,
    model
  })
}

const selectNativeLocale = (nativeLocale) => {
  if (busy.value || nativeBusy.value) return
  processingSettings.value = saveProcessingSettings({
    ...processingSettings.value,
    nativeLocale: String(nativeLocale || '').trim()
  })
}

const consumeUploadRouteIntent = async () => {
  const query = route.query || {}
  const normalizedMode = String(query.mode || '').trim().toLowerCase()
  const normalizedUrl = String(query.url || '').trim()
  const normalizedSource = String(query.source || '').trim()
  recommendationSource.value = normalizedSource

  const restQuery = { ...query }
  delete restQuery.mode
  delete restQuery.url
  delete restQuery.source

  let consumed = false
  if (normalizedMode === 'url' || normalizedUrl) {
    submissionMode.value = 'url'
    consumed = true
  } else if (normalizedMode === 'native') {
    submissionMode.value = 'native'
    consumed = true
  } else if (normalizedMode === 'file') {
    submissionMode.value = 'file'
    consumed = true
  }

  if (normalizedUrl) {
    videoUrl.value = normalizedUrl
    message.value = normalizedSource
      ? `已从 ${normalizedSource} 推荐带入链接，可直接提交导入。`
      : '已带入推荐链接，可直接提交导入。'
    consumed = true
  } else if (normalizedSource && normalizedMode === 'url') {
    message.value = `已切换到链接导入，可粘贴 ${normalizedSource} 链接。`
    consumed = true
  }

  if (consumed) {
    await router.replace({ path: route.path, query: restQuery }).catch(() => {})
  }
}

const readableSize = (size) => {
  const n = Number(size || 0)
  if (!n) return '0 B'
  if (n >= 1024 * 1024 * 1024) return `${(n / (1024 * 1024 * 1024)).toFixed(2)} GB`
  if (n >= 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(2)} MB`
  if (n >= 1024) return `${(n / 1024).toFixed(2)} KB`
  return `${n} B`
}

const fileExt = (filename) => {
  const name = String(filename || '').trim()
  const idx = name.lastIndexOf('.')
  if (idx < 0) return ''
  return name.slice(idx + 1).toLowerCase()
}

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

const resolveVideoId = (payload) => {
  const data = payload?.data ?? payload
  return data?.video_id || data?.id || data?.video?.id || data?.data?.id || data?.data?.video_id
}

const statusText = videoStatusText
const isActiveStatus = (status) => ['pending', 'processing', 'downloading'].includes(normalizeVideoStatus(status))
const displayProgress = (value) => {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric)) return 0
  return Math.max(0, Math.min(100, Math.round(numeric)))
}

const statusClass = (status) => {
  const tone = videoStatusTone(status)
  if (tone === 'ok') return 'status--ok'
  if (tone === 'bad') return 'status--bad'
  if (tone === 'warn') return 'status--warn'
  return 'status--info'
}

const nativeEngineLabel = (engine) => {
  const normalized = String(engine || '').trim()
  if (normalized === 'whisper_cpp_on_device') return 'Whisper 本机离线转录'
  if (normalized === 'apple_speech_on_device') return 'Apple 端侧识别'
  if (normalized === 'backend_whisper') return 'Whisper 后端转录'
  return 'iOS 原生识别'
}

const logOfflineFlow = (stage, payload = {}) => {
  try {
    console.info(`[OfflineFlow] ${stage} ${JSON.stringify(payload)}`)
  } catch {
    console.info(`[OfflineFlow] ${stage}`)
  }
}

const upsertNativeTask = (patch = {}) => {
  const current = nativeTask.value || {}
  const tags = Array.isArray(patch.tags)
    ? patch.tags.filter(Boolean).map((tag) => String(tag).trim())
    : (Array.isArray(current.tags) ? current.tags : [])
  const next = {
    taskId: String(patch.taskId || current.taskId || ''),
    fileName: String(patch.fileName || current.fileName || '本地视频'),
    fileSize: Number(patch.fileSize ?? current.fileSize ?? 0),
    fileExt: String(patch.fileExt || current.fileExt || ''),
    status: normalizeVideoStatus(patch.status || current.status || 'pending'),
    progress: displayProgress(patch.progress ?? current.progress ?? 0),
    currentStep: String(patch.currentStep || patch.message || current.currentStep || '准备本地离线转录'),
    transcriptText: String(patch.transcriptText ?? current.transcriptText ?? ''),
    errorMessage: String(patch.errorMessage ?? current.errorMessage ?? ''),
    summary: String(patch.summary ?? current.summary ?? ''),
    summaryStyle: String(patch.summaryStyle || current.summaryStyle || processingSettings.value.summaryStyle || 'study'),
    summaryStatus: String(patch.summaryStatus || current.summaryStatus || 'idle').trim().toLowerCase() || 'idle',
    summaryErrorMessage: String(patch.summaryErrorMessage ?? current.summaryErrorMessage ?? ''),
    summaryUpdatedAt: String(patch.summaryUpdatedAt || current.summaryUpdatedAt || ''),
    autoGenerateSummary: typeof patch.autoGenerateSummary === 'boolean'
      ? patch.autoGenerateSummary
      : Boolean(current.autoGenerateSummary),
    autoGenerateTags: typeof patch.autoGenerateTags === 'boolean'
      ? patch.autoGenerateTags
      : (typeof current.autoGenerateTags === 'boolean' ? current.autoGenerateTags : Boolean(processingSettings.value.autoGenerateTags)),
    tags,
    syncedVideoId: Number(patch.syncedVideoId ?? current.syncedVideoId ?? 0) || 0,
    syncStatus: String(patch.syncStatus || current.syncStatus || 'idle').trim().toLowerCase() || 'idle',
    syncErrorMessage: String(patch.syncErrorMessage ?? current.syncErrorMessage ?? ''),
    syncUpdatedAt: String(patch.syncUpdatedAt || current.syncUpdatedAt || ''),
    locale: String(patch.locale || current.locale || ''),
    localeLabel: nativeLocaleLabel(patch.locale || current.locale || ''),
    engine: String(patch.engine || current.engine || 'apple_speech_on_device'),
    engineLabel: nativeEngineLabel(patch.engine || current.engine || 'apple_speech_on_device')
  }
  nativeTask.value = next
  return next
}

const clearNativeTask = () => {
  if (nativeBusy.value) return
  nativeTask.value = null
}

const reloadNativeHistory = async () => {
  try {
    nativeHistory.value = await listNativeOfflineTranscripts()
    if (!nativeTask.value) {
      const latest = await getLatestNativeOfflineTranscript()
      if (latest) upsertNativeTask(latest)
    }
  } catch (e) {
    error.value = e?.message || '加载本地转录历史失败'
  }
}

const persistNativeTask = async (patch = {}) => {
  const next = upsertNativeTask(patch)
  if (!next.taskId) return next
  await saveNativeOfflineTranscript(next)
  return next
}

const syncOfflineTranscriptRecord = async (taskId, { silent = false } = {}) => {
  const id = String(taskId || '').trim()
  if (!id) return null

  const current = await getNativeOfflineTranscript(id)
  if (!current?.transcriptText?.trim()) return null
  logOfflineFlow('sync-start', {
    taskId: id,
    apiBaseAvailable: hasLiveVideoBackend(),
    transcriptLength: String(current.transcriptText || '').trim().length,
    hasSummary: Boolean(String(current.summary || '').trim())
  })

  if (!hasLiveVideoBackend()) {
    logOfflineFlow('sync-skipped-backend-unavailable', {
      taskId: id
    })
    const skipped = await saveNativeOfflineTranscript({
      taskId: id,
      syncStatus: 'failed',
      syncErrorMessage: '当前未配置可用后端，无法写入视频库；可在后端恢复后再次同步。'
    })
    upsertNativeTask(skipped)
    return null
  }

  const pending = await persistNativeTask({
    taskId: id,
    syncStatus: 'syncing',
    syncErrorMessage: ''
  })

  try {
    const res = await syncOfflineTranscriptToVideo({
      task_id: pending.taskId,
      file_name: pending.fileName,
      file_ext: pending.fileExt,
      file_size: pending.fileSize,
      locale: pending.locale,
      engine: pending.engine,
      transcript_text: pending.transcriptText,
      summary: pending.summary || '',
      summary_style: pending.summaryStyle || processingSettings.value.summaryStyle || 'study',
      tags: Array.isArray(pending.tags) ? pending.tags : [],
      auto_generate_tags: typeof pending.autoGenerateTags === 'boolean'
        ? pending.autoGenerateTags
        : Boolean(processingSettings.value.autoGenerateTags),
      segments: Array.isArray(current.segments) ? current.segments : []
    })
    const data = res?.data || {}
    const videoId = resolveVideoId(data)
    const title = data?.video?.title || pending.fileName || '本地视频'
    const tags = Array.isArray(data?.video?.tags) ? data.video.tags : (Array.isArray(pending.tags) ? pending.tags : [])
    logOfflineFlow('sync-success', {
      taskId: id,
      videoId: videoId || 0,
      title,
      tagCount: tags.length
    })
    const saved = await persistNativeTask({
      taskId: id,
      syncedVideoId: videoId || 0,
      syncStatus: 'completed',
      syncErrorMessage: '',
      syncUpdatedAt: new Date().toISOString(),
      fileName: title,
      tags
    })
    upsertRecentUpload({
      key: `offline-synced-${videoId || id}`,
      videoId: videoId || null,
      title,
      typeText: 'iOS 离线处理',
      time: new Date().toISOString(),
      status: 'completed',
      progress: 100,
      currentStep: 'iOS 本地离线结果已写入视频库',
      tags,
      offlineTaskId: id,
      tempKey: `ios-offline-${id}`,
      requestedModel: '',
      effectiveModel: ''
    })
    if (!silent) {
      message.value = '本地离线转录结果已写入视频库'
    }
    return saved
  } catch (e) {
    logOfflineFlow('sync-failed', {
      taskId: id,
      error: extractErrorMessage(e, '写入视频库失败')
    })
    const saved = await persistNativeTask({
      taskId: id,
      syncStatus: 'failed',
      syncErrorMessage: extractErrorMessage(e, '写入视频库失败'),
      syncUpdatedAt: new Date().toISOString()
    })
    if (!silent) {
      error.value = saved.syncErrorMessage || '写入视频库失败'
    }
    return saved
  }
}

const generateOfflineTranscriptSummaryForTask = async (taskId, { silent = false } = {}) => {
  const id = String(taskId || '').trim()
  if (!id) return null

  const current = await getNativeOfflineTranscript(id)
  if (!current?.transcriptText?.trim()) return null
  logOfflineFlow('summary-start', {
    taskId: id,
    apiBaseAvailable: hasLiveVideoBackend(),
    style: String(current.summaryStyle || processingSettings.value.summaryStyle || 'study')
  })

  if (!hasLiveVideoBackend()) {
    logOfflineFlow('summary-skipped-backend-unavailable', {
      taskId: id
    })
    const skipped = await saveNativeOfflineTranscript({
      taskId: id,
      summaryStatus: 'failed',
      summaryErrorMessage: '当前未配置可用后端，无法提取摘要；可在后端恢复后进入详情页重试。'
    })
    upsertNativeTask(skipped)
    return null
  }

  await persistNativeTask({
    taskId: id,
    summaryStatus: 'generating',
    summaryErrorMessage: '',
    currentStep: current.status === 'completed' ? '转录完成，正在提取摘要' : current.currentStep
  })

  try {
    const style = String(current.summaryStyle || processingSettings.value.summaryStyle || 'study')
    const res = await generateTranscriptSummary({
      title: current.fileName || '本地视频',
      transcript_text: current.transcriptText,
      style
    })
    const data = res?.data || {}
    logOfflineFlow('summary-success', {
      taskId: id,
      style: data.style || style,
      summaryLength: String(data.summary || '').trim().length
    })
    const saved = await persistNativeTask({
      taskId: id,
      summary: data.summary || '',
      summaryStyle: data.style || style,
      summaryStatus: 'completed',
      summaryErrorMessage: '',
      summaryUpdatedAt: new Date().toISOString(),
      autoGenerateTags: Boolean(processingSettings.value.autoGenerateTags),
      currentStep: current.status === 'completed' ? '本地离线转录完成' : current.currentStep
    })
    await syncOfflineTranscriptRecord(id, { silent })
    if (!silent) {
      message.value = saved.summary ? 'iOS 本地离线转录完成，摘要已生成' : 'iOS 本地离线转录完成'
    }
    return saved
  } catch (e) {
    logOfflineFlow('summary-failed', {
      taskId: id,
      error: extractErrorMessage(e, '摘要提取失败')
    })
    const saved = await persistNativeTask({
      taskId: id,
      summaryStatus: 'failed',
      summaryErrorMessage: extractErrorMessage(e, '摘要提取失败'),
      currentStep: current.status === 'completed' ? '本地离线转录完成' : current.currentStep
    })
    if (!silent) {
      error.value = saved.summaryErrorMessage || '摘要提取失败'
    }
    return saved
  }
}

const openNativeTaskDetail = (taskId) => {
  const id = String(taskId || '').trim()
  if (!id) return
  router.push(`/local-transcripts/${id}`)
}

const removeNativeHistoryItem = async (taskId) => {
  const id = String(taskId || '').trim()
  if (!id) return
  try {
    await deleteNativeOfflineTranscript(id)
    if (nativeTask.value?.taskId === id) nativeTask.value = null
    await reloadNativeHistory()
  } catch (e) {
    error.value = e?.message || '删除本地转录历史失败'
  }
}

const handleNativeTranscriptStoreEvent = async () => {
  await reloadNativeHistory()
}

const formatTimeText = (isoText) => {
  if (!isoText) return ''
  try {
    const d = new Date(isoText)
    if (Number.isNaN(d.getTime())) return ''
    return d.toLocaleString()
  } catch {
    return ''
  }
}

const normalizeRecentUploads = (list) => {
  if (!Array.isArray(list)) return []
  return list
    .filter(Boolean)
    .map((item) => ({
      key: String(item.key || `${item.videoId || 'none'}-${item.time || ''}`),
      videoId: item.videoId ? Number(item.videoId) : null,
      title: String(item.title || '未命名视频'),
      typeText: String(item.typeText || '上传'),
      time: String(item.time || ''),
      timeText: formatTimeText(item.time),
      duplicate: Boolean(item.duplicate),
      status: normalizeVideoStatus(item.status || (item.duplicate ? 'uploaded' : 'pending')),
      progress: displayProgress(item.progress),
      currentStep: String(item.currentStep || ''),
      tags: Array.isArray(item.tags) ? item.tags.filter(Boolean).map((tag) => String(tag).trim()) : [],
      offlineTaskId: item.offlineTaskId ? String(item.offlineTaskId) : '',
      tempKey: item.tempKey ? String(item.tempKey) : '',
      requestedModel: String(item.requestedModel || item.requested_model || '').trim().toLowerCase(),
      effectiveModel: String(item.effectiveModel || item.effective_model || item.requestedModel || item.requested_model || '').trim().toLowerCase(),
      retrying: false
    }))
    .filter((item) => item.key)
}

const recentModelText = (item) => {
  const model = String(item?.effectiveModel || item?.requestedModel || '').trim().toLowerCase()
  return model ? `本次任务：${whisperModelLabel(model)} 模型` : ''
}

const recentTagText = (item) => {
  if (item?.duplicate) return '重复'
  if (normalizeVideoStatus(item?.status) === 'uploading') return '补跑中'
  if (item?.offlineTaskId && !item?.videoId) return '离线队列'
  return '在线任务'
}

const recentTagClass = (item) => ({
  'recent-tag--dup': Boolean(item?.duplicate),
  'recent-tag--offline': Boolean(item?.offlineTaskId) && !item?.duplicate
})

const hasActiveRecentUploads = computed(() => recentUploads.value.some((item) => isActiveStatus(item.status)))
const isRecentQueueStatus = (status) => ['offline_queued', 'uploading'].includes(normalizeVideoStatus(status))

const filteredRecentUploads = computed(() => {
  if (statusFilter.value === 'all') return recentUploads.value
  if (statusFilter.value === 'active') {
    return recentUploads.value.filter((item) =>
      ['pending', 'processing', 'downloading', 'offline_queued', 'uploading'].includes(normalizeVideoStatus(item.status))
    )
  }
  return recentUploads.value.filter((item) => normalizeVideoStatus(item.status) === statusFilter.value)
})

const loadRecentUploads = () => {
  try {
    const raw = storageGet(RECENT_UPLOADS_KEY)
    recentUploads.value = normalizeRecentUploads(raw ? JSON.parse(raw) : [])
  } catch {
    recentUploads.value = []
  }
}

const persistRecentUploads = () => {
  try {
    storageSet(RECENT_UPLOADS_KEY, JSON.stringify(recentUploads.value))
  } catch {
    // ignore storage errors
  }
}

const refreshWhisperModelOptions = async () => {
  try {
    const res = await getVideoProcessingOptions()
    const catalog = saveWhisperModelCatalog(res?.data || {})
    whisperModelOptions.value = catalog.options
    processingSettings.value = saveProcessingSettings(processingSettings.value)
  } catch {
    whisperModelOptions.value = getWhisperModelOptions()
    processingSettings.value = saveProcessingSettings(processingSettings.value)
  }
}

const findRecentUploadIndex = (item = {}) =>
  recentUploads.value.findIndex((current) => {
    if (item.key && current.key === item.key) return true
    if (item.offlineTaskId && current.offlineTaskId === item.offlineTaskId) return true
    if (item.tempKey && current.tempKey === item.tempKey) return true
    if (item.videoId && current.videoId && Number(current.videoId) === Number(item.videoId)) return true
    return false
  })

const upsertRecentUpload = (item) => {
  const normalized = normalizeRecentUploads([item])[0]
  if (!normalized) return

  const next = [...recentUploads.value]
  const idx = findRecentUploadIndex(normalized)
  if (idx >= 0) {
    next[idx] = { ...next[idx], ...normalized }
    recentUploads.value = next
  } else {
    recentUploads.value = [normalized, ...next].slice(0, MAX_RECENT_UPLOADS)
  }

  persistRecentUploads()
}

const addRecentUpload = ({
  videoId,
  title,
  typeText,
  duplicate = false,
  status = 'pending',
  requestedModel = '',
  effectiveModel = ''
}) => {
  const now = new Date().toISOString()
  const normalizedStatus = normalizeVideoStatus(duplicate ? 'uploaded' : status)
  const item = {
    key: `${videoId || 'none'}-${now}`,
    videoId: videoId ? Number(videoId) : null,
    title: String(title || '未命名视频'),
    typeText: String(typeText || '上传'),
    time: now,
    timeText: formatTimeText(now),
    duplicate: Boolean(duplicate),
    status: normalizedStatus,
    progress: 0,
    currentStep: normalizedStatus === 'downloading' ? '已提交，等待下载' : '已提交，等待处理',
    requestedModel: String(requestedModel || '').trim().toLowerCase(),
    effectiveModel: String(effectiveModel || requestedModel || '').trim().toLowerCase(),
    retrying: false
  }
  upsertRecentUpload(item)
  scheduleRecentStatusSync()
}

const buildOfflineCurrentStep = (task) => {
  if (task.status === OFFLINE_TASK_STATUSES.UPLOADING) return '后端已恢复，正在自动补跑'
  if (task.status === OFFLINE_TASK_STATUSES.FAILED) return task.lastError || '自动补跑失败，等待稍后重试'
  if (task.status === OFFLINE_TASK_STATUSES.COMPLETED && task.videoId) return '离线补跑成功，正在同步处理状态'
  return '已加入离线队列，等待后端恢复自动补跑'
}

const buildRecentUploadFromOfflineTask = (task, current = {}) => {
  const requestedModel = String(task?.processing?.model || current.requestedModel || '').trim().toLowerCase()
  const liveStatus =
    task.status === OFFLINE_TASK_STATUSES.COMPLETED && task.videoId
      ? normalizeVideoStatus(current.status || 'pending')
      : normalizeVideoStatus(task.status)
  const time = current.time || task.createdAt
  return {
    key: current.key || task.tempKey || `offline-${task.taskId}`,
    offlineTaskId: task.taskId,
    tempKey: task.tempKey || current.tempKey || `offline-${task.taskId}`,
    videoId: task.videoId || current.videoId || null,
    title: current.title || task.fileName || task.videoUrl || '离线任务',
    typeText:
      current.typeText
      || (task.type === 'local_upload' ? `本地文件 · ${readableSize(task.fileSize)}` : '链接导入'),
    time,
    timeText: formatTimeText(time),
    duplicate: Boolean(current.duplicate),
    status: liveStatus,
    progress: task.videoId ? current.progress || 0 : 0,
    currentStep: buildOfflineCurrentStep(task),
    tags: Array.isArray(current.tags) ? current.tags : [],
    requestedModel,
    effectiveModel: String(current.effectiveModel || requestedModel).trim().toLowerCase(),
    retrying: false
  }
}

const syncOfflineRecentUploads = async () => {
  if (syncingOfflineRecent) return false
  syncingOfflineRecent = true

  try {
    const tasks = await getOfflineTasks()
    let promoted = false

    for (const task of tasks) {
      const current = recentUploads.value[findRecentUploadIndex({ offlineTaskId: task.taskId, tempKey: task.tempKey, videoId: task.videoId })] || {}
      const nextItem = buildRecentUploadFromOfflineTask(task, current)
      upsertRecentUpload(nextItem)

      if (task.status === OFFLINE_TASK_STATUSES.COMPLETED && task.videoId) {
        promoted = true
        await deleteOfflineTask(task.taskId)
      }
    }

    scheduleRecentStatusSync()
    return promoted
  } finally {
    syncingOfflineRecent = false
  }
}

const clearRecentStatusSync = () => {
  if (recentStatusTimer == null) return
  window.clearTimeout(recentStatusTimer)
  recentStatusTimer = null
}

const scheduleRecentStatusSync = () => {
  clearRecentStatusSync()
  if (busy.value || syncingRecent.value || !hasActiveRecentUploads.value) return
  recentStatusTimer = window.setTimeout(async () => {
    recentStatusTimer = null
    await syncRecentStatuses()
  }, 3000)
}

const syncRecentStatuses = async () => {
  const targets = recentUploads.value.filter((item) => item.videoId)
  if (targets.length === 0) return

  syncingRecent.value = true
  try {
    const updates = await Promise.all(
      targets.map(async (item) => {
        try {
          const res = await getVideoStatus(item.videoId)
          const data = res?.data || {}
          return {
            key: item.key,
            status: normalizeVideoStatus(data?.status || data?.data?.status),
            progress: displayProgress(data?.progress ?? data?.data?.progress),
            currentStep: String(data?.current_step || data?.data?.current_step || ''),
            requestedModel: String(data?.requested_model || data?.data?.requested_model || '').trim().toLowerCase(),
            effectiveModel: String(data?.effective_model || data?.data?.effective_model || data?.requested_model || '').trim().toLowerCase()
          }
        } catch {
          return {
            key: item.key,
            status: normalizeVideoStatus(item.status),
            progress: displayProgress(item.progress),
            currentStep: String(item.currentStep || ''),
            requestedModel: String(item.requestedModel || '').trim().toLowerCase(),
            effectiveModel: String(item.effectiveModel || item.requestedModel || '').trim().toLowerCase()
          }
        }
      })
    )
    const statusMap = new Map(updates.map((u) => [u.key, u]))
    recentUploads.value = recentUploads.value.map((item) => ({
      ...item,
      status: statusMap.get(item.key)?.status || item.status,
      progress: statusMap.get(item.key)?.progress ?? item.progress,
      currentStep: statusMap.get(item.key)?.currentStep ?? item.currentStep,
      requestedModel: statusMap.get(item.key)?.requestedModel || item.requestedModel,
      effectiveModel: statusMap.get(item.key)?.effectiveModel || item.effectiveModel
    }))
    persistRecentUploads()
  } finally {
    syncingRecent.value = false
    scheduleRecentStatusSync()
  }
}

const clearRecentUploads = () => {
  if (busy.value) return
  clearRecentStatusSync()
  recentUploads.value = []
  try {
    storageRemove(RECENT_UPLOADS_KEY)
  } catch {
    // ignore storage errors
  }
}

const openRecent = (item) => {
  if (item?.offlineTaskId) {
    router.push(`/local-transcripts/${item.offlineTaskId}`)
    return
  }
  if (!item?.videoId) return
  router.push(`/videos/${item.videoId}`)
}

const handleOfflineQueueEvent = async () => {
  const promoted = await syncOfflineRecentUploads()
  if (promoted) await syncRecentStatuses()
}

const retryRecent = async (item) => {
  if (!item?.videoId) return
  const idx = recentUploads.value.findIndex((x) => x.key === item.key)
  if (idx < 0) return

  recentUploads.value[idx] = { ...recentUploads.value[idx], retrying: true }
  error.value = ''
  message.value = ''
  try {
    processingSettings.value = getProcessingSettings()
    await processVideo(item.videoId, buildProcessPayload(processingSettings.value))
    recentUploads.value[idx] = {
      ...recentUploads.value[idx],
      status: 'pending',
      progress: 0,
      currentStep: '已提交，等待处理',
      requestedModel: String(processingSettings.value.model || '').trim().toLowerCase(),
      effectiveModel: String(processingSettings.value.model || '').trim().toLowerCase(),
      retrying: false
    }
    message.value = `视频 ${item.videoId} 已重新提交处理`
    persistRecentUploads()
    await syncRecentStatuses()
  } catch (e) {
    recentUploads.value[idx] = { ...recentUploads.value[idx], retrying: false }
    error.value = extractErrorMessage(e, '重试失败')
  }
}

const queueOfflineLocalUpload = async (selectedFile) => {
  const task = await createLocalUploadTask({
    file: selectedFile,
    processing: processingSettings.value
  })
  upsertRecentUpload(buildRecentUploadFromOfflineTask(task))
  savedFileMeta.value = { name: selectedFile.name, size: Number(selectedFile.size || 0) }
  file.value = null
  progress.value = 0
  if (fileInputRef.value) fileInputRef.value.value = ''
  message.value = '后端暂时不可达，已加入离线队列，等待后端恢复后自动补跑'
}

const queueOfflineUrlImport = async (trimmedUrl) => {
  const task = await createUrlImportTask({
    videoUrl: trimmedUrl,
    processing: processingSettings.value
  })
  upsertRecentUpload(buildRecentUploadFromOfflineTask(task))
  videoUrl.value = ''
  progress.value = 0
  message.value = '链接任务已加入离线队列，等待后端恢复后自动补跑'
}

const validateVideoUrl = (url) => {
  const value = String(url || '').trim()
  if (!value) return '请输入视频链接'
  const ok = /(bilibili\.com|b23\.tv|youtube\.com|youtu\.be|icourse163\.org)/i.test(value)
  if (!ok) return '仅支持 B站 / YouTube / 中国大学慕课 链接'
  return ''
}

const onFileChange = (e) => {
  const selected = e?.target?.files?.[0] || null
  error.value = ''
  message.value = ''
  progress.value = 0
  if (!selected) {
    file.value = null
    return
  }
  const ext = fileExt(selected.name)
  if (!ALLOWED_EXTENSIONS.has(ext)) {
    file.value = null
    if (fileInputRef.value) fileInputRef.value.value = ''
    error.value = `不支持的文件类型：.${ext || '未知'}，请上传 ${[...ALLOWED_EXTENSIONS].join(', ')}`
    return
  }
  if (Number(selected.size || 0) > MAX_UPLOAD_SIZE_BYTES) {
    file.value = null
    if (fileInputRef.value) fileInputRef.value.value = ''
    error.value = `文件过大（${readableSize(selected.size)}），当前上限为 ${readableSize(MAX_UPLOAD_SIZE_BYTES)}`
    return
  }
  file.value = selected
  savedFileMeta.value = { name: selected.name, size: Number(selected.size || 0) }
}

const resetAll = () => {
  if (busy.value) return
  file.value = null
  savedFileMeta.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
  videoUrl.value = ''
  submissionMode.value = 'file'
  recommendationSource.value = ''
  progress.value = 0
  message.value = ''
  error.value = ''
  clearUploadRecommendations()
  latestUploadedVideoId.value = 0
  latestUploadedTitle.value = ''
  if (!nativeBusy.value) nativeTask.value = null
}

const openFilePicker = () => {
  if (busy.value) return
  fileInputRef.value?.click()
}

const startNativeOfflineTranscriptionFlow = async () => {
  if (busy.value || nativeBusy.value) return
  processingSettings.value = getProcessingSettings()
  message.value = ''
  error.value = ''

  if (!hasNativeBridge()) {
    error.value = '当前环境不是 iOS 原生容器，无法进行本地离线转录'
    return
  }

  nativeBusy.value = true
  let started = false
  try {
    const requestedLocale = resolveNativeTranscriptionLocale(processingSettings.value)
    logOfflineFlow('native-start-request', {
      locale: requestedLocale,
      language: processingSettings.value.language,
      model: processingSettings.value.model,
      apiBaseAvailable: hasLiveVideoBackend()
    })
    const response = await startNativeOfflineTranscription({
      locale: requestedLocale,
      language: processingSettings.value.language,
      model: processingSettings.value.model
    })
    started = true
    await persistNativeTask({
      taskId: response?.taskId,
      fileName: response?.fileName,
      fileSize: response?.fileSize,
      fileExt: response?.fileExt,
      status: response?.status || 'preparing',
      progress: 5,
      currentStep: response?.message || '已选择本地视频，准备本地离线转录',
      locale: response?.locale || requestedLocale || processingSettings.value.language,
      engine: response?.engine || 'apple_speech_on_device',
      autoGenerateSummary: processingSettings.value.autoGenerateSummary,
      summaryStyle: processingSettings.value.summaryStyle,
      summary: '',
      summaryStatus: 'idle',
      summaryErrorMessage: '',
      syncStatus: 'idle',
      syncErrorMessage: '',
      syncedVideoId: 0,
      transcriptText: '',
      errorMessage: ''
    })
    logOfflineFlow('native-started', {
      taskId: response?.taskId,
      fileName: response?.fileName,
      locale: response?.locale || requestedLocale || processingSettings.value.language
    })
    message.value = '已启动 iOS 本地离线转录'
  } catch (e) {
    logOfflineFlow('native-start-failed', {
      error: extractErrorMessage(e, '无法启动 iOS 本地离线转录')
    })
    error.value = extractErrorMessage(e, '无法启动 iOS 本地离线转录')
  } finally {
    if (!started) nativeBusy.value = false
  }
}

const handleNativeProgressEvent = async (detail = {}) => {
  nativeBusy.value = true
  logOfflineFlow('native-progress', {
    taskId: detail.taskId,
    status: detail.status || detail.phase || 'processing',
    progress: Number(detail.progress ?? 0) || 0,
    message: detail.message || '正在本地离线转录'
  })
  await persistNativeTask({
    taskId: detail.taskId,
    fileName: detail.fileName,
    fileSize: detail.fileSize,
    status: detail.status || detail.phase || 'processing',
    progress: detail.progress,
    currentStep: detail.message || '正在本地离线转录',
    locale: detail.locale,
    engine: detail.engine
  })
}

const handleNativeCompletedEvent = async (detail = {}) => {
  nativeBusy.value = false
  logOfflineFlow('native-completed', {
    taskId: detail.taskId,
    progress: Number(detail.progress ?? 100) || 100,
    transcriptLength: String(detail.transcriptText || '').trim().length,
    segmentCount: Array.isArray(detail.segments) ? detail.segments.length : 0
  })
  const saved = await persistNativeTask({
    taskId: detail.taskId,
    fileName: detail.fileName,
    fileSize: detail.fileSize,
    fileExt: detail.fileExt,
    status: detail.status || 'completed',
    progress: detail.progress ?? 100,
    currentStep: detail.message || '本地离线转录完成',
    transcriptText: detail.transcriptText || '',
    errorMessage: '',
    locale: detail.locale,
    engine: detail.engine
  })
  if (saved?.autoGenerateSummary) {
    message.value = 'iOS 本地离线转录完成，正在提取摘要'
    void generateOfflineTranscriptSummaryForTask(saved.taskId)
    return
  }
  void syncOfflineTranscriptRecord(saved.taskId)
  message.value = 'iOS 本地离线转录完成'
}

const handleNativeFailedEvent = async (detail = {}) => {
  nativeBusy.value = false
  logOfflineFlow('native-failed', {
    taskId: detail.taskId,
    progress: Number(detail.progress ?? 0) || 0,
    error: detail.message || 'iOS 本地离线转录失败'
  })
  await persistNativeTask({
    taskId: detail.taskId,
    fileName: detail.fileName,
    fileSize: detail.fileSize,
    status: detail.status || 'failed',
    progress: detail.progress ?? 0,
    currentStep: detail.message || '本地离线转录失败',
    errorMessage: detail.message || '本地离线转录失败',
    locale: detail.locale,
    engine: detail.engine
  })
  error.value = detail.message || 'iOS 本地离线转录失败'
}

const uploadFile = async () => {
  if (!file.value || busy.value) return
  busy.value = true
  progress.value = 0
  message.value = ''
  error.value = ''
  clearUploadRecommendations()
  try {
    const form = new FormData()
    form.append('file', file.value)
    processingSettings.value = getProcessingSettings()
    appendProcessingSettingsToFormData(form, processingSettings.value)
    const res = await uploadLocalVideo(form, {
      onUploadProgress: (evt) => {
        if (!evt.total) return
        progress.value = Math.min(100, Math.round((evt.loaded / evt.total) * 100))
      }
    })
    const data = res?.data || {}
    const videoId = resolveVideoId(data)
    const uploadedTitle = data?.data?.title || file.value?.name || '本地视频'
    progress.value = 100
    message.value = data?.duplicate
      ? (data?.message || '视频已存在，已为你跳转到详情页')
      : (data?.message || '上传成功，已为你自动开始处理')
    storeUploadRecommendations(data?.recommendations, videoId, uploadedTitle)
    addRecentUpload({
      videoId,
      title: uploadedTitle,
      typeText: `本地文件 · ${readableSize(file.value?.size)}`,
      duplicate: Boolean(data?.duplicate),
      status: data?.status || 'uploaded',
      requestedModel: data?.data?.requested_model || processingSettings.value.model,
      effectiveModel: data?.data?.effective_model || data?.data?.requested_model || processingSettings.value.model
    })
    savedFileMeta.value = file.value ? { name: file.value.name, size: Number(file.value.size || 0) } : savedFileMeta.value
    file.value = null
    if (fileInputRef.value) fileInputRef.value.value = ''
    if (uploadRecommendationItems.value.length > 0) {
      message.value = `${message.value} 下方已自动给出下一步推荐。`
      return
    }
    router.push(videoId ? { path: `/videos/${videoId}`, query: data?.duplicate ? undefined : { autostart: '1' } } : '/videos')
  } catch (e) {
    if (isVideoUploadQueueableError(e)) {
      try {
        await queueOfflineLocalUpload(file.value)
      } catch (queueError) {
        error.value = `${getVideoUploadQueueableMessage(e, '后端暂时不可达')}；当前设备无法写入离线队列`
      }
    } else {
      error.value = extractErrorMessage(e, '上传失败')
    }
  } finally {
    busy.value = false
  }
}

const uploadUrl = async () => {
  if (!videoUrl.value || busy.value) return
  const validationError = validateVideoUrl(videoUrl.value)
  if (validationError) {
    error.value = validationError
    return
  }
  busy.value = true
  progress.value = 0
  message.value = ''
  error.value = ''
  clearUploadRecommendations()
  try {
    const trimmedUrl = String(videoUrl.value).trim()
    processingSettings.value = getProcessingSettings()
    const res = await uploadVideoUrl({ url: trimmedUrl, ...buildProcessPayload(processingSettings.value) })
    const data = res?.data || {}
    const videoId = resolveVideoId(data)
    const uploadedTitle = data?.data?.title || trimmedUrl
    message.value = data?.message || '已提交链接，下载完成后会自动开始处理'
    storeUploadRecommendations(data?.recommendations, videoId, uploadedTitle)
    recommendationSource.value = ''
    addRecentUpload({
      videoId,
      title: uploadedTitle,
      typeText: '链接导入',
      duplicate: Boolean(data?.duplicate),
      status: data?.status || 'downloading',
      requestedModel: data?.data?.requested_model || processingSettings.value.model,
      effectiveModel: data?.data?.effective_model || data?.data?.requested_model || processingSettings.value.model
    })
    videoUrl.value = ''
    if (uploadRecommendationItems.value.length > 0) {
      message.value = `${message.value} 下方已自动给出下一步推荐。`
      return
    }
    router.push(videoId ? { path: `/videos/${videoId}`, query: data?.duplicate ? undefined : { autostart: '1' } } : '/videos')
  } catch (e) {
    if (isVideoUploadQueueableError(e)) {
      try {
        await queueOfflineUrlImport(String(videoUrl.value).trim())
      } catch (queueError) {
        error.value = `${getVideoUploadQueueableMessage(e, '后端暂时不可达')}；当前设备无法写入离线队列`
      }
    } else {
      error.value = extractErrorMessage(e, '提交失败')
    }
  } finally {
    busy.value = false
  }
}

onMounted(async () => {
  await consumeUploadRouteIntent()
  nativeEventDisposers.push(onNativeEvent(NATIVE_OFFLINE_TRANSCRIPTION_PROGRESS_EVENT, handleNativeProgressEvent))
  nativeEventDisposers.push(onNativeEvent(NATIVE_OFFLINE_TRANSCRIPTION_COMPLETED_EVENT, handleNativeCompletedEvent))
  nativeEventDisposers.push(onNativeEvent(NATIVE_OFFLINE_TRANSCRIPTION_FAILED_EVENT, handleNativeFailedEvent))
  window.addEventListener(NATIVE_OFFLINE_TRANSCRIPTS_EVENT_NAME, handleNativeTranscriptStoreEvent)
  processingSettings.value = getProcessingSettings()
  await refreshWhisperModelOptions()
  await reloadNativeHistory()
  loadRecentUploads()
  window.addEventListener(OFFLINE_QUEUE_EVENT_NAME, handleOfflineQueueEvent)
  await syncOfflineRecentUploads()
  await flushOfflineQueue()
  await syncOfflineRecentUploads()
  await syncRecentStatuses()
  scheduleRecentStatusSync()
})

watch(
  () => route.fullPath,
  async () => {
    await consumeUploadRouteIntent()
  }
)

onUnmounted(() => {
  clearRecentStatusSync()
  window.removeEventListener(OFFLINE_QUEUE_EVENT_NAME, handleOfflineQueueEvent)
  window.removeEventListener(NATIVE_OFFLINE_TRANSCRIPTS_EVENT_NAME, handleNativeTranscriptStoreEvent)
  nativeEventDisposers.splice(0).forEach((dispose) => dispose?.())
})
</script>

<style scoped>
.page {
  max-width: 520px;
  margin: 0 auto;
  padding: calc(14px + env(safe-area-inset-top)) 16px 0;
  font-family: 'Avenir Next', 'SF Pro Display', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.topbar,
.card {
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(242, 235, 248, 0.93);
  box-shadow: 0 18px 38px rgba(73, 51, 104, 0.12);
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 5;
  padding: 12px 14px;
  border-radius: 20px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  flex-wrap: wrap;
}

.topbar__copy {
  display: grid;
  gap: 4px;
}

.topbar h2 {
  margin: 0;
  font-size: 20px;
  line-height: 1.1;
  letter-spacing: -0.03em;
  color: #221a30;
}

.topbar__copy p {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: #706781;
}

.link {
  border: 0;
  background: transparent;
  color: var(--primary-deep);
  font-weight: 700;
}

.link--small {
  font-size: 12px;
}

.card {
  padding: 16px;
  border-radius: 24px;
  display: grid;
  gap: 12px;
  margin-bottom: 12px;
}

.card--active {
  border-color: var(--primary-soft-strong);
  background: linear-gradient(180deg, rgba(232, 221, 244, 0.98), rgba(247, 241, 251, 0.98));
}

.card--spotlight {
  background: linear-gradient(180deg, rgba(232, 221, 244, 0.98), rgba(247, 241, 251, 0.98));
}

.import-banner {
  gap: 14px;
  border-color: var(--primary-soft);
  background: linear-gradient(180deg, rgba(242, 235, 248, 0.98), rgba(242, 235, 248, 0.96));
}

.import-banner__top,
.import-banner__actions,
.import-tip,
.card-head,
.card-head-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.import-banner__url {
  border-radius: 16px;
  padding: 13px 14px;
  font-size: 12px;
  line-height: 1.6;
  color: #221a30;
  background: rgba(247, 241, 251, 0.92);
  border: 1px dashed rgba(17, 24, 39, 0.12);
  overflow-wrap: anywhere;
  word-break: break-word;
}

.upload-followup__context,
.upload-followup__hint {
  border-radius: 16px;
  padding: 12px 14px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--primary-deep);
  background: var(--surface-lilac);
  border: 1px solid rgba(143, 115, 186, 0.18);
}

.upload-followup__list {
  display: grid;
  gap: 10px;
}

.upload-followup__item {
  display: grid;
  gap: 10px;
  border-radius: 20px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(238, 230, 246, 0.92);
  padding: 14px;
}

.upload-followup__top,
.upload-followup__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.upload-followup__title {
  font-size: 15px;
  line-height: 1.45;
  color: #221a30;
}

.upload-followup__desc,
.upload-followup__meta {
  font-size: 12px;
  line-height: 1.6;
  color: #706781;
}

.upload-followup__tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.upload-followup__tag {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 5px 10px;
  background: var(--surface-lilac-deep);
  color: var(--lilac-text);
  font-size: 11px;
  font-weight: 700;
}

.import-badge,
.recent-tag,
.status {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.import-badge {
  padding: 5px 10px;
  color: var(--primary-deep);
  background: var(--primary-soft);
}

.import-badge--inline {
  flex-shrink: 0;
}

.card-title {
  font-size: 15px;
  font-weight: 800;
  color: #221a30;
}

.filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.filter,
.mini {
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(247, 241, 251, 0.96);
  border-radius: 999px;
  padding: 7px 11px;
  font-size: 12px;
  font-weight: 700;
  color: #111827;
  text-align: center;
}

.filter--active {
  border-color: var(--primary-soft-strong);
  background: var(--surface-lilac);
  color: var(--primary-deep);
}

.input {
  width: 100%;
  border-radius: 14px;
  border: 1px solid rgba(17, 24, 39, 0.12);
  padding: 12px;
  outline: none;
  background: rgba(238, 230, 246, 0.92);
  color: #221a30;
}

.btn {
  border-radius: 16px;
  padding: 13px;
  font-weight: 800;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(242, 235, 248, 0.98);
  width: 100%;
  text-align: center;
}

.btn--primary {
  border: 0;
  color: #f9fafb;
  background: linear-gradient(135deg, #5f477e, #8f73ba);
  box-shadow: 0 16px 24px rgba(95, 71, 126, 0.24);
}

.btn--native {
  border: 1px solid rgba(41, 98, 66, 0.16);
  color: var(--primary-deep);
  background: linear-gradient(180deg, var(--surface-lilac-deep), rgba(242, 235, 248, 0.98));
}

.btn:disabled,
.mini:disabled {
  opacity: 0.6;
}

.bar {
  height: 100%;
  background: linear-gradient(90deg, #5f477e, #8f73ba);
}

.bar--native {
  background: linear-gradient(90deg, #9b82c7, #b79dd5);
}

.progress {
  height: 8px;
  border-radius: 999px;
  background: rgba(17, 24, 39, 0.06);
  overflow: hidden;
}

.progress--compact {
  height: 6px;
}

.muted,
.empty {
  font-size: 12px;
  line-height: 1.6;
  color: #706781;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.file {
  width: 100%;
}

.file--hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.file-picker {
  display: grid;
  grid-template-columns: minmax(0, 132px) minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  border-radius: 18px;
  border: 1px solid rgba(95, 71, 126, 0.14);
  background: rgba(238, 230, 246, 0.92);
  padding: 12px;
}

.file-picker--selected {
  background: linear-gradient(180deg, rgba(236, 227, 246, 0.96), rgba(247, 241, 251, 0.96));
}

.file-picker__button {
  min-height: 46px;
  border: 0;
  border-radius: 14px;
  padding: 0 14px;
  font-size: 13px;
  font-weight: 800;
  color: #f9fafb;
  background: linear-gradient(135deg, #5f477e, #8f73ba);
  box-shadow: 0 12px 20px rgba(95, 71, 126, 0.2);
}

.file-picker__button:disabled {
  opacity: 0.6;
}

.file-picker__meta {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.file-picker__title {
  font-size: 14px;
  line-height: 1.45;
  color: #221a30;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.file-picker__desc {
  font-size: 12px;
  line-height: 1.6;
  color: #706781;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.recent-list {
  display: grid;
  gap: 10px;
}

.recent-item {
  border-radius: 18px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(238, 230, 246, 0.92);
  padding: 12px 14px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  text-align: left;
  flex-wrap: wrap;
}

.recent-main,
.native-result {
  min-width: 0;
  display: grid;
  gap: 6px;
}

.recent-title {
  font-size: 14px;
  font-weight: 700;
  line-height: 1.45;
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
  color: #221a30;
}

.recent-meta {
  margin-top: 2px;
}

.recent-progress {
  display: grid;
  gap: 6px;
  margin-top: 2px;
}

.recent-progress__text {
  font-size: 12px;
  color: #706781;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.status {
  padding: 4px 9px;
}

.status--ok {
  background: rgba(242, 235, 248, 0.92);
  color: var(--ok-text);
}

.status--bad {
  background: var(--lilac-bg);
  color: var(--lilac-text);
}

.status--warn {
  background: var(--lilac-bg);
  color: var(--lilac-text);
}

.status--info {
  background: var(--info-bg);
  color: var(--info-text);
}

.recent-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
  margin-left: auto;
}

.native-result__text {
  margin: 0;
  padding: 12px;
  border-radius: 16px;
  background: rgba(17, 24, 39, 0.04);
  border: 1px solid rgba(17, 24, 39, 0.08);
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  line-height: 1.6;
  max-height: 260px;
  overflow: auto;
}

.recent-tag {
  padding: 4px 10px;
  background: var(--info-bg);
  color: var(--info-text);
  white-space: normal;
  text-align: center;
}

.recent-tag--dup {
  background: var(--lilac-bg);
  color: var(--lilac-text);
}

.recent-tag--offline {
  background: var(--surface-lilac);
  color: var(--primary-deep);
}

.recent-tag--soft {
  background: var(--surface-lilac-deep);
  color: var(--lilac-text);
}

.mini--warn {
  border-color: rgba(106, 75, 155, 0.16);
  background: var(--lilac-bg);
  color: var(--lilac-text);
}

.alert {
  padding: 11px 13px;
  border-radius: 16px;
  font-weight: 700;
  margin-bottom: 12px;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.alert--ok {
  background: var(--surface-lilac);
  color: var(--primary-deep);
}

.alert--bad {
  background: var(--lilac-bg);
  color: var(--lilac-text);
}

@media (max-width: 480px) {
  .topbar,
  .card {
    padding: 14px;
  }

  .file-picker {
    grid-template-columns: 1fr;
  }

  .import-banner__actions {
    display: grid;
    grid-template-columns: 1fr;
  }

  .recent-actions {
    width: 100%;
    margin-left: 0;
    justify-content: flex-start;
  }

  .mini,
  .recent-tag,
  .link--small {
    max-width: 100%;
  }
}
</style>
