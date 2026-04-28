<template>
  <div class="ios-page home-page">
    <header class="welcome ios-card">
      <div class="welcome__top">
        <div class="welcome__brand">
          <div class="welcome__brand-surface">
            <div class="welcome__brand-icon">
              <BrandLogo :width="64" variant="plain" logo-type="mark" rounded />
            </div>
            <div class="welcome__brand-copy">
              <span class="welcome__brand-mark">EduMind</span>
              <strong class="welcome__brand-title">智能伴学</strong>
            </div>
          </div>
        </div>
        <button class="guide-btn" @click="go('/guide')" aria-label="打开使用指南">使用指南</button>
      </div>

      <div class="welcome__hero">
        <div class="welcome__copy">
          <p class="welcome__eyebrow">Learning Dashboard</p>
          <h1 class="welcome__title">智能伴学中心</h1>
          <p class="welcome__subtitle">把上传、跟进、复盘和推荐收进同一条学习动线里，页面保持简洁，下一步一眼就能决定。</p>
        </div>
        <aside class="welcome__spotlight">
          <span class="welcome__spotlight-label">当前重心</span>
          <strong class="welcome__spotlight-value">{{ featuredVideo ? featuredVideoEyebrow : '从上传开始' }}</strong>
          <p class="welcome__spotlight-note">
            {{ featuredVideo ? (featuredVideo.title || '未命名视频') : '先上传一个视频，系统就会开始整理学习轨迹。' }}
          </p>
          <button class="welcome__spotlight-link" @click="featuredVideo ? openVideo(featuredVideo) : go('/upload')">
            {{ featuredVideo ? featuredVideoActionLabel : '开始上传' }}
          </button>
        </aside>
      </div>

      <div class="hero-actions">
        <button class="hero-btn hero-btn--primary" @click="go('/upload')">立即上传</button>
        <button class="hero-btn hero-btn--secondary" @click="go('/videos')">浏览视频库</button>
      </div>

      <div class="home-semantic-search">
        <label class="home-semantic-search__label" for="home-semantic-search-input">{{ SEARCH_COPY_HOME_SEMANTIC_TITLE }}</label>
        <p class="home-semantic-search__scope">{{ SEARCH_COPY_HOME_SEMANTIC_DESCRIPTION }}</p>
        <div class="home-semantic-search__row">
          <input
            id="home-semantic-search-input"
            v-model.trim="semanticSearchDraft"
            class="home-semantic-search__input"
            type="search"
            enterkeyhint="search"
            autocomplete="off"
            :placeholder="SEARCH_COPY_HOME_INPUT_PLACEHOLDER"
            @keyup.enter="submitHomeSemanticSearch"
          />
          <button type="button" class="home-semantic-search__btn" @click="submitHomeSemanticSearch">
            {{ SEARCH_COPY_SEARCH_BUTTON }}
          </button>
        </div>
      </div>

      <div class="welcome__subnote">
        <span>登录后，站外可导入推荐会先写入你的视频库，再出现在下方卡片里，点进去即可走下载与处理全流程。</span>
      </div>

      <div class="stats">
        <button type="button" class="stat-pill" @click="goStat('recent')">
          <span class="stat-pill__label">最近视频</span>
          <strong class="stat-pill__value">{{ recentCount }}</strong>
        </button>
        <button type="button" class="stat-pill stat-pill--ok" @click="goStat('completed')">
          <span class="stat-pill__label">已完成</span>
          <strong class="stat-pill__value">{{ completedCount }}</strong>
        </button>
        <button type="button" class="stat-pill stat-pill--warn" @click="goStat('active')">
          <span class="stat-pill__label">进行中</span>
          <strong class="stat-pill__value">{{ inProgressCount }}</strong>
        </button>
        <button type="button" class="stat-pill stat-pill--feature" @click="go('/recommendations')">
          <span class="stat-pill__label">推荐系统</span>
          <strong class="stat-pill__value">{{ recommendationEntryValue }}</strong>
        </button>
      </div>
    </header>

    <section class="overview ios-card">
      <div class="section-head">
        <div>
          <h2>学习概览</h2>
          <p>把最近任务和回看入口压缩成一屏里的稳定节奏。</p>
        </div>
        <button class="overview-link" @click="reloadDashboard" :disabled="loading || recommendationLoading">
          {{ loading ? '刷新中…' : '刷新' }}
        </button>
      </div>

      <div v-if="error" class="message message--error">
        <span>{{ error }}</span>
        <button class="overview-link" @click="reloadDashboard">重试</button>
      </div>

      <div v-else-if="loading && !featuredVideo" class="skeleton-list">
        <div v-for="i in 3" :key="i" class="skeleton-item"></div>
      </div>

      <div v-else class="overview__body">
        <button v-if="featuredVideo" class="focus-card" @click="openVideo(featuredVideo)">
          <span class="focus-card__eyebrow">{{ featuredVideoEyebrow }}</span>
          <h3 class="focus-card__title">{{ featuredVideo.title || '未命名视频' }}</h3>
          <div class="focus-card__meta">
            <span class="video-item__status" :class="statusClass(featuredVideo.status)">{{ statusText(featuredVideo.status) }}</span>
            <span class="focus-card__note">{{ featuredVideoNote }}</span>
          </div>
          <span class="focus-card__cta">{{ featuredVideoActionLabel }}</span>
        </button>

        <div v-else class="message message--empty">
          还没有学习内容，先上传一个视频建立你的学习轨迹。
          <button class="overview-link" @click="go('/upload')">去上传</button>
        </div>

        <div class="summary-grid">
          <button class="summary-card summary-card--soft" @click="goStat(completedCount > 0 ? 'completed' : 'recent')">
            <span class="summary-card__label">可复盘内容</span>
            <strong class="summary-card__value">{{ completedCount }}</strong>
            <span class="summary-card__note">优先进入已完成视频整理笔记</span>
          </button>
        </div>

        <div v-if="recentListVideos.length > 0" class="recent-inline">
          <div class="recent-inline__head">
            <h3>最近进入</h3>
            <button class="overview-link" @click="go('/videos')">查看全部</button>
          </div>
          <div class="video-list">
            <button v-for="video in recentListVideos" :key="video.id" class="video-item" @click="openVideo(video)">
              <div class="video-item__info">
                <p class="video-item__title">{{ video.title || '未命名视频' }}</p>
                <span class="video-item__status" :class="statusClass(video.status)">{{ statusText(video.status) }}</span>
              </div>
              <span class="video-item__arrow">›</span>
            </button>
          </div>
        </div>
      </div>
    </section>

    <section class="recommend-panel ios-card">
      <div class="section-head">
        <h2>为你推荐</h2>
      </div>

      <div v-if="homeAutoMaterializeBanner" class="message message--hint">
        <span>{{ homeAutoMaterializeBanner }}</span>
      </div>

      <div v-if="recommendationExternalFetchBanner" class="message message--warn">
        <span>{{ recommendationExternalFetchBanner }}</span>
        <button type="button" class="overview-link" @click="go('/recommendations')">去推荐页</button>
      </div>

      <div v-if="homeRecommendationFallbackBanner" class="message message--hint">
        <span>{{ homeRecommendationFallbackBanner }}</span>
      </div>

      <div v-if="showHomeProviderDiagnostics" class="recommend-provider-list">
        <article
          v-for="provider in recommendationProviderReports"
          :key="provider.provider"
          class="recommend-provider-card"
          :class="{
            'recommend-provider-card--failed': provider.status === 'failed',
            'recommend-provider-card--empty': provider.status === 'empty'
          }"
        >
          <div class="recommend-provider-card__top">
            <strong>{{ provider.source_label }}</strong>
            <span>{{ providerStatusText(provider) }}</span>
          </div>
          <p>{{ providerStatusDetail(provider) }}</p>
        </article>
      </div>

      <div v-if="recommendationLoading && recommendations.length === 0" class="skeleton-list">
        <div v-for="i in 2" :key="`recommend-${i}`" class="skeleton-item skeleton-item--tall"></div>
      </div>

      <div v-else-if="recommendations.length === 0" class="message">
        {{ recommendationEmptyText }}
        <button v-if="!hasAuthToken" type="button" class="overview-link" @click="go('/login')">去登录</button>
        <button type="button" class="overview-link" @click="go('/videos')">视频库</button>
        <button type="button" class="overview-link" @click="go('/recommendations')">推荐页</button>
      </div>

      <div v-else class="recommend-list">
        <button
          v-for="item in recommendationCards"
          :key="recommendationKey(item)"
          class="recommend-card"
          @click="openRecommendation(item)"
        >
          <div class="recommend-card__top">
            <span class="recommend-card__reason">{{ item.reason_label || '推荐' }}</span>
            <span
              v-if="recommendationStatusLabel(item)"
              class="video-item__status"
              :class="recommendationStatusClass(item)"
            >
              {{ recommendationStatusLabel(item) }}
            </span>
          </div>
          <div class="recommend-card__title">{{ item.title || '未命名视频' }}</div>
          <div class="recommend-card__meta">
            <span>{{ item.source_label || '站内视频' }}</span>
            <span v-if="item.subjectText">{{ item.subjectText }}</span>
            <span v-if="formatTimeText(item.upload_time)">{{ formatTimeText(item.upload_time) }}</span>
          </div>
          <div v-if="item.importHint" class="recommend-card__hint">{{ item.importHint }}</div>
          <span class="recommend-card__next">{{ recommendationNextStepText(item) }}</span>
        </button>
      </div>

      <button class="hero-btn hero-btn--secondary" @click="go('/recommendations')">进入推荐中枢</button>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import BrandLogo from '@/components/BrandLogo.vue'
import { getVideoRecommendations } from '@/api/recommendation'
import { shouldIncludeExternalRecommendationsOnHome } from '@/config'
import { storageGet } from '@/utils/storage'
import {
  DEFAULT_SEARCH_SCOPE,
  SEARCH_ROUTE_AUTO_SEARCH_QUERY,
  SEARCH_COPY_HOME_INPUT_PLACEHOLDER,
  SEARCH_COPY_HOME_SEMANTIC_DESCRIPTION,
  SEARCH_COPY_HOME_SEMANTIC_TITLE,
  SEARCH_COPY_SEARCH_BUTTON,
  SEARCH_ROUTE_PREFILL_QUERY,
  SEARCH_ROUTE_SCOPE_QUERY
} from '@/config/searchDefaults'
import {
  isRecommendationPrimaryActionDisabled,
  parseRecommendationActionTarget,
  resolveRecommendationUrl,
  shouldOpenRecommendationExternalSource
} from '@/services/recommendationActions'
import { VIDEO_DELETED_EVENT_NAME, filterDeletedVideosLocally, getVideoList } from '@/api/video'
import { isActiveVideoStatus, isCompletedVideoStatus, videoStatusText, videoStatusTone } from '@/services/videoStatus'

const router = useRouter()
const semanticSearchDraft = ref('')
const loading = ref(false)
const recommendationLoading = ref(false)
const error = ref('')
const recommendationError = ref('')
const recommendationFallbackMode = ref('none')
const allVideos = ref([])
const recommendations = ref([])
const recommendationMeta = ref({
  sources: [],
  externalProviders: [],
  externalQuery: null,
  internalItemCount: 0,
  externalItemCount: 0,
  externalFailedProviderCount: 0,
  externalFetchFailed: false,
  flowVersion: 'recommendation_flow_v1',
  autoMaterializedExternalCount: 0,
  autoMaterializationFailedCount: 0
})

const normalizeList = (payload) => {
  const list = payload?.videos || payload?.items || payload?.data || payload || []
  return filterDeletedVideosLocally(Array.isArray(list) ? list : [])
}

const RECOMMENDATION_TITLE_BLOCKLIST = ['排列组合插空法详解']
const isBlockedRecommendationTitle = (item) => {
  const title = String(item?.title || '').trim()
  if (!title) return false
  return RECOMMENDATION_TITLE_BLOCKLIST.some((keyword) => keyword && title.includes(keyword))
}

const normalizeRecommendationItems = (payload) => {
  const items = payload?.items || payload?.recommendations || payload?.data || []
  return Array.isArray(items) ? items.filter((item) => !isBlockedRecommendationTitle(item)) : []
}
const normalizeRecommendationSources = (payload) => Array.isArray(payload?.sources) ? payload.sources : []
const normalizeRecommendationProviders = (payload) => Array.isArray(payload?.external_providers) ? payload.external_providers : []
const normalizeRecommendationQuery = (payload) => payload?.external_query || null
const normalizeRecommendationCount = (payload, key) => {
  const numeric = Number(payload?.[key] || 0)
  return Number.isFinite(numeric) ? numeric : 0
}
const createRecommendationMeta = () => ({
  sources: [],
  externalProviders: [],
  externalQuery: null,
  internalItemCount: 0,
  externalItemCount: 0,
  externalFailedProviderCount: 0,
  externalFetchFailed: false,
  flowVersion: 'recommendation_flow_v1',
  autoMaterializedExternalCount: 0,
  autoMaterializationFailedCount: 0
})
const buildRecommendationMeta = (payload) => ({
  sources: normalizeRecommendationSources(payload),
  externalProviders: normalizeRecommendationProviders(payload),
  externalQuery: normalizeRecommendationQuery(payload),
  internalItemCount: normalizeRecommendationCount(payload, 'internal_item_count'),
  externalItemCount: normalizeRecommendationCount(payload, 'external_item_count'),
  externalFailedProviderCount: normalizeRecommendationCount(payload, 'external_failed_provider_count'),
  externalFetchFailed: Boolean(payload?.external_fetch_failed || false),
  flowVersion: String(payload?.flow_version || 'recommendation_flow_v1'),
  autoMaterializedExternalCount: normalizeRecommendationCount(payload, 'auto_materialized_external_count'),
  autoMaterializationFailedCount: normalizeRecommendationCount(payload, 'auto_materialization_failed_count')
})

const formatTimeText = (rawValue) => {
  if (!rawValue) return ''
  try {
    const date = new Date(rawValue)
    if (Number.isNaN(date.getTime())) return ''
    return date.toLocaleString()
  } catch {
    return ''
  }
}

const statusText = videoStatusText

const statusClass = (status) => {
  const tone = videoStatusTone(status)
  if (tone === 'ok') return 'status--ok'
  if (tone === 'bad') return 'status--bad'
  if (tone === 'warn') return 'status--warn'
  return 'status--info'
}

const recentCount = computed(() => allVideos.value.length)
const completedCount = computed(() => allVideos.value.filter((item) => isCompletedVideoStatus(item?.status)).length)
const inProgressCount = computed(() => allVideos.value.filter((item) => isActiveVideoStatus(item?.status)).length)
const recommendationEntryValue = computed(() => {
  if (recommendationLoading.value && recommendations.value.length === 0) return '...'
  return String(recommendations.value.length)
})
const featuredVideo = computed(() => allVideos.value.find((item) => isActiveVideoStatus(item?.status)) || allVideos.value[0] || null)
const recentListVideos = computed(() => {
  const featuredId = Number(featuredVideo.value?.id || 0)
  return allVideos.value.filter((item) => Number(item.id || 0) !== featuredId).slice(0, 3)
})
const featuredVideoEyebrow = computed(() => {
  if (!featuredVideo.value) return ''
  if (isActiveVideoStatus(featuredVideo.value?.status)) return '优先跟进'
  if (isCompletedVideoStatus(featuredVideo.value?.status)) return '适合复盘'
  return '最近进入'
})
const featuredVideoNote = computed(() => {
  if (!featuredVideo.value) return ''
  if (isActiveVideoStatus(featuredVideo.value?.status)) return '当前任务仍在推进'
  if (isCompletedVideoStatus(featuredVideo.value?.status)) return '已完成处理，可继续复盘'
  return '从这里继续进入'
})
const featuredVideoActionLabel = computed(() => (isActiveVideoStatus(featuredVideo.value?.status) ? '查看进度' : '打开详情'))

const mergeVideosById = (items) => {
  const map = new Map()
  for (const item of items) {
    if (!item?.id) continue
    map.set(Number(item.id), item)
  }
  return Array.from(map.values()).sort((a, b) => {
    const ta = new Date(a?.upload_time || 0).getTime()
    const tb = new Date(b?.upload_time || 0).getTime()
    return tb - ta
  })
}

const fallbackRecommendations = (videos) =>
  videos
    .filter((video) => !isBlockedRecommendationTitle(video))
    .slice(0, 6)
    .map((video, index) => ({
    ...video,
    reason_label: index === 0 ? '继续学习' : '最近内容',
    reason_text: index === 0 ? '当前最适合从这个任务继续进入。' : '最近进入视频库，适合继续学习。'
    }))

const fetchAllVideos = async () => {
  const first = await getVideoList(1, 100)
  const firstPayload = first?.data || {}
  const firstList = normalizeList(firstPayload)
  const totalPages = Math.max(1, Number(firstPayload?.total_pages || 1))
  if (totalPages <= 1) return firstList

  const all = [...firstList]
  for (let p = 2; p <= totalPages; p += 1) {
    const res = await getVideoList(p, 100)
    all.push(...normalizeList(res?.data || {}))
  }
  return all
}

const reload = async () => {
  loading.value = true
  error.value = ''
  try {
    const [videos] = await Promise.all([fetchAllVideos()])
    allVideos.value = mergeVideosById(videos)
  } catch (e) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const reloadRecommendations = async () => {
  recommendationLoading.value = true
  recommendationError.value = ''
  recommendationFallbackMode.value = 'none'
  try {
    const res = await getVideoRecommendations({
      scene: 'home',
      limit: 6,
      include_external: shouldIncludeExternalRecommendationsOnHome()
    })
    const payload = res?.data || {}
    const items = normalizeRecommendationItems(payload)
    if (items.length > 0) {
      recommendations.value = items
      recommendationFallbackMode.value = 'none'
    } else {
      recommendations.value = fallbackRecommendations(allVideos.value)
      recommendationFallbackMode.value = recommendations.value.length > 0 ? 'empty_result' : 'none'
    }
    recommendationMeta.value = buildRecommendationMeta(payload)
  } catch (e) {
    recommendationError.value = e?.message || '推荐加载失败'
    recommendations.value = fallbackRecommendations(allVideos.value)
    recommendationFallbackMode.value = recommendations.value.length > 0 ? 'api_error' : 'none'
    recommendationMeta.value = createRecommendationMeta()
  } finally {
    recommendationLoading.value = false
  }
}

const go = (path) => router.push(path)
const submitHomeSemanticSearch = () => {
  const q = String(semanticSearchDraft.value || '').trim()
  router.push({
    path: '/search',
    query: {
      [SEARCH_ROUTE_SCOPE_QUERY]: DEFAULT_SEARCH_SCOPE,
      ...(q ? { [SEARCH_ROUTE_AUTO_SEARCH_QUERY]: '1' } : {}),
      ...(q ? { [SEARCH_ROUTE_PREFILL_QUERY]: q } : {})
    }
  })
}
const goStat = (scope) => {
  console.info(`[INFO][Home] stat-card-click scope=${scope}`)
  router.push({ path: '/videos', query: { scope } })
}

const resolveVideoId = (video) => {
  const n = Number(video?.id ?? video?.video_id ?? video?.server_id ?? video?.local_id ?? 0)
  return Number.isFinite(n) && n > 0 ? Math.floor(n) : 0
}

const openVideo = (video) => {
  const current = video || {}
  const videoId = resolveVideoId(current)
  if (!videoId) return
  router.push(`/videos/${videoId}`)
}

const hasAuthToken = computed(() => Boolean(String(storageGet('m_token') || '').trim()))

const homeAutoMaterializeBanner = computed(() => {
  const count = Number(recommendationMeta.value.autoMaterializedExternalCount || 0)
  const failed = Number(recommendationMeta.value.autoMaterializationFailedCount || 0)
  if (count > 0 && failed > 0) return `已自动入库 ${count} 条站外推荐，另有 ${failed} 条未入库，可稍后在推荐页重试。`
  if (count > 0) return `已将 ${count} 条站外推荐写入视频库，可直接打开继续处理。`
  if (failed > 0) return `有 ${failed} 条站外推荐未能自动入库，仍可作为链接在推荐页导入。`
  return ''
})

/** 仅有结果时不展示各 provider 技术卡片，减少首页噪音；无结果时再展示便于排障 */
const showHomeProviderDiagnostics = computed(
  () =>
    recommendations.value.length === 0 &&
    recommendationProviderReports.value.length > 0
)

const recommendationEmptyText = computed(() => {
  if (recommendationError.value) return recommendationError.value
  if (!hasAuthToken.value) {
    return '登录后，系统才能把站外可导入推荐先写入你的视频库并出现在这里；也可先到推荐页浏览。'
  }
  return '上传或导入视频后，这里会按学习进度与主题推荐下一步。'
})
const decorateRecommendationItem = (item) => ({
  ...item,
  subjectText: String(item?.subject || '').trim() ? `科目 · ${String(item.subject).trim()}` : '',
  importHint: String(item?.import_hint || '').trim(),
  actionTarget: String(item?.action_target || '').trim(),
  primaryActionDisabled: isRecommendationPrimaryActionDisabled(item, isExternalRecommendation(item))
})
const recommendationCards = computed(() => recommendations.value.map((item) => decorateRecommendationItem(item)))
const recommendationProviderReports = computed(() => recommendationMeta.value.externalProviders || [])
const providerStatusText = (provider) => {
  if (provider?.status === 'failed') return '抓取失败'
  if (provider?.status === 'empty') return '暂无候选'
  return `${Number(provider?.candidate_count || 0)} 条候选`
}
const recommendationExternalFetchBanner = computed(() => {
  if (!recommendationMeta.value.externalFetchFailed) return ''
  return '部分站外来源暂时不可用，站内推荐仍有效。可检查网络后刷新，或到推荐页查看其它场景。'
})
const homeRecommendationFallbackBanner = computed(() => {
  if (recommendationFallbackMode.value === 'api_error' && recommendations.value.length > 0) {
    return '推荐服务暂时不可用，当前展示的是视频库兜底结果。可稍后刷新重试。'
  }
  if (recommendationFallbackMode.value === 'empty_result' && recommendations.value.length > 0) {
    return '当前暂无命中的个性化推荐，先为你展示视频库近期内容。'
  }
  return ''
})

const providerStatusDetail = (provider) => {
  if (provider?.status === 'failed')
    return String(
      provider?.error_message ||
        '当前来源抓取失败。可检查网络、稍后再试，或在环境变量中关闭站外默认加载。'
    )
  if (provider?.status === 'empty') return `当前已检索但没有返回可用候选，耗时 ${Number(provider?.latency_ms || 0)} ms`
  return `本轮抓取耗时 ${Number(provider?.latency_ms || 0)} ms，可在推荐页继续导入。`
}

const recommendationKey = (item) =>
  String(item?.id || item?.external_url || item?.target_url || item?.source_url || item?.link || item?.title || 'recommendation')

const isExternalRecommendation = (item) => {
  const itemType = String(item?.item_type || item?.content_type || item?.origin_type || '').trim().toLowerCase()
  if (item?.is_external === true) return true
  if (['external', 'external_candidate', 'candidate'].includes(itemType)) return true
  return !item?.id && Boolean(resolveRecommendationUrl(item))
}

const recommendationStatusLabel = (item) => {
  if (isExternalRecommendation(item)) {
    return String(item?.source_label || item?.external_source_label || item?.source_platform_label || '站外候选')
  }
  return item?.status ? statusText(item.status) : '站内推荐'
}

const recommendationStatusClass = (item) => {
  if (isExternalRecommendation(item)) return 'status--warn'
  return statusClass(item?.status)
}

const recommendationNextStepText = (item) =>
  String(item?.action_label || '').trim() || (isExternalRecommendation(item) ? '下一步：带着链接进入导入学习链路' : '下一步：打开详情继续学习')

const openRecommendation = (item) => {
  if (isExternalRecommendation(item) && item.primaryActionDisabled) {
    recommendationError.value = item.importHint || '当前站外候选暂不可直接导入。'
    return
  }
  const actionTarget = String(item?.actionTarget || item?.action_target || '').trim()
  const actionLocation = parseRecommendationActionTarget(actionTarget)
  if (actionLocation) {
    router.push(actionLocation)
    return
  }
  if (isExternalRecommendation(item)) {
    if (shouldOpenRecommendationExternalSource(item)) {
      const externalTarget = actionTarget || resolveRecommendationUrl(item)
      if (externalTarget && typeof window !== 'undefined') {
        window.location.assign(externalTarget)
        return
      }
    }
    const url = resolveRecommendationUrl(item)
    if (!url) return
    router.push({
      path: '/upload',
      query: {
        mode: 'url',
        url,
        source: String(item?.source_label || item?.external_source_label || item?.source_platform_label || '站外推荐')
      }
    })
    return
  }
  openVideo(item)
}

const reloadDashboard = async () => {
  await reload()
  await reloadRecommendations()
}

const removeVideoFromLocalState = (videoId) => {
  const id = Number(videoId)
  if (!Number.isFinite(id) || id <= 0) return
  allVideos.value = allVideos.value.filter((item) => Number(item?.id || 0) !== id)
  recommendations.value = recommendations.value.filter((item) => Number(item?.id || 0) !== id)
}

const handleVideoDeleted = (event) => {
  const deletedId = Number(event?.detail?.videoId || 0)
  removeVideoFromLocalState(deletedId)
}

onMounted(() => {
  window.addEventListener(VIDEO_DELETED_EVENT_NAME, handleVideoDeleted)
  void reloadDashboard()
})

onUnmounted(() => {
  window.removeEventListener(VIDEO_DELETED_EVENT_NAME, handleVideoDeleted)
})
</script>

<style scoped>
.home-page {
  display: grid;
  gap: 16px;
  padding-top: calc(16px + env(safe-area-inset-top));
  font-family: 'Avenir Next', 'SF Pro Display', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.welcome,
.overview,
.recommend-panel {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(242, 235, 248, 0.92);
  box-shadow: 0 18px 38px rgba(73, 51, 104, 0.12);
}

.welcome {
  padding: 24px;
  border-radius: 30px;
  background:
    linear-gradient(180deg, rgba(242, 235, 248, 0.98), rgba(242, 235, 248, 0.95)),
    radial-gradient(circle at top right, rgba(143, 115, 186, 0.18), transparent 34%),
    radial-gradient(circle at 18% 100%, rgba(183, 157, 213, 0.14), transparent 28%);
}

.welcome::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 1px;
  background: linear-gradient(90deg, rgba(95, 71, 126, 0), rgba(95, 71, 126, 0.14), rgba(95, 71, 126, 0));
}

.welcome::after {
  content: '';
  position: absolute;
  width: 240px;
  height: 240px;
  right: -90px;
  top: -120px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(95, 71, 126, 0.08) 0%, rgba(95, 71, 126, 0.01) 64%, transparent 72%);
  pointer-events: none;
}

.welcome__top,
.welcome__hero,
.stats {
  position: relative;
  z-index: 1;
}

.welcome__top,
.section-head,
.recent-inline__head,
.recommend-card__top,
.recommend-card__meta,
.focus-card__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.welcome__brand {
  display: flex;
  align-items: center;
  min-width: 0;
  flex: 1 1 auto;
}

.welcome__brand-surface {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 0;
  background: transparent;
  border: 0;
  box-shadow: none;
}

.welcome__brand-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  width: 64px;
  height: 64px;
  padding: 0;
  border-radius: 20px;
  background: transparent;
  border: 0;
  box-shadow: none;
  overflow: hidden;
}

.welcome__brand-copy {
  display: grid;
  gap: 0;
  min-width: 0;
  padding-top: 0;
}

.welcome__brand-mark {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  color: var(--primary-deep);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  opacity: 0.82;
}

.welcome__brand-title {
  color: #221a30;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: -0.025em;
  line-height: 1.08;
}

.guide-btn,
.overview-link {
  border: 0;
  background: transparent;
  color: var(--primary-deep);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.01em;
}

.guide-btn {
  border: 1px solid rgba(17, 24, 39, 0.09);
  border-radius: 999px;
  background: rgba(244, 238, 249, 0.84);
  padding: 7px 11px;
  font-size: 11px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.68),
    0 6px 14px rgba(106, 75, 155, 0.06);
}

.welcome__hero {
  display: grid;
  gap: 14px;
  margin-top: 18px;
  grid-template-columns: minmax(0, 1.5fr) minmax(180px, 0.9fr);
}

.welcome__eyebrow,
.focus-card__eyebrow,
.recommend-card__reason {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  width: fit-content;
  padding: 5px 10px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  background: var(--primary-soft);
  color: var(--primary-deep);
}

.welcome__title {
  margin: 10px 0 0;
  font-size: 34px;
  line-height: 1.02;
  letter-spacing: -0.04em;
  color: #111827;
}

.welcome__subtitle,
.section-head p,
.quick-card__desc,
.summary-card__note,
.focus-card__note,
.recommend-card__desc,
.recommend-card__meta {
  color: var(--muted);
}

.welcome__subtitle {
  margin-top: 12px;
  font-size: 14px;
  line-height: 1.6;
  max-width: 28rem;
}

.welcome__spotlight {
  display: grid;
  align-content: start;
  gap: 8px;
  padding: 16px;
  border-radius: 22px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: linear-gradient(180deg, rgba(242, 235, 248, 0.98), rgba(242, 235, 248, 0.94));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.welcome__spotlight-label {
  font-size: 11px;
  font-weight: 700;
  color: #6b7280;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.welcome__spotlight-value {
  font-size: 20px;
  line-height: 1.1;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #221a30;
}

.welcome__spotlight-note {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: #706781;
}

.welcome__spotlight-link {
  width: fit-content;
  border: 0;
  background: transparent;
  padding: 0;
  color: var(--primary-deep);
  font-size: 13px;
  font-weight: 700;
}

.welcome__subnote {
  margin-top: 14px;
  font-size: 12px;
  line-height: 1.5;
  color: #6b7280;
}

.hero-actions,
.summary-grid,
.video-list,
.recommend-list,
.skeleton-list {
  display: grid;
  gap: 10px;
}

.hero-actions {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 14px;
}

.home-semantic-search {
  display: grid;
  gap: 10px;
  margin-top: 12px;
  padding: 16px;
  border-radius: 20px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.55), rgba(239, 231, 247, 0.75));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.75),
    0 10px 22px rgba(95, 71, 126, 0.08);
}

.home-semantic-search__label {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #221a30;
}

.home-semantic-search__scope {
  margin: 0;
  font-size: 12px;
  line-height: 1.45;
  color: #6b7280;
}

.home-semantic-search__row {
  display: flex;
  gap: 8px;
  align-items: stretch;
}

.home-semantic-search__input {
  flex: 1 1 auto;
  min-width: 0;
  min-height: 44px;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid rgba(17, 24, 39, 0.1);
  background: rgba(255, 255, 255, 0.92);
  font-size: 15px;
  color: #111827;
}

.home-semantic-search__input::placeholder {
  color: #9ca3af;
}

.home-semantic-search__input:focus {
  outline: none;
  border-color: rgba(95, 71, 126, 0.35);
  box-shadow: 0 0 0 3px rgba(143, 115, 186, 0.18);
}

.home-semantic-search__btn {
  flex: 0 0 auto;
  min-height: 44px;
  padding: 0 16px;
  border-radius: 14px;
  border: 0;
  font-size: 14px;
  font-weight: 800;
  color: #f9fafb;
  background: linear-gradient(135deg, #5f477e, #8f73ba);
  box-shadow: 0 8px 18px rgba(95, 71, 126, 0.22);
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.home-semantic-search__btn:active {
  transform: scale(0.98);
}

.hero-btn,
.stat-pill,
.summary-card,
.focus-card,
.recommend-card,
.video-item {
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(247, 241, 251, 0.96);
}

.hero-btn {
  border-radius: 16px;
  padding: 14px 15px;
  font-size: 14px;
  font-weight: 800;
}

.hero-btn--primary {
  border: 0;
  color: #f9fafb;
  background: linear-gradient(135deg, #5f477e, #8f73ba);
  box-shadow: 0 16px 24px rgba(95, 71, 126, 0.24);
}

.hero-btn--secondary {
  color: var(--primary-deep);
  background: rgba(235, 226, 246, 0.94);
}

.stats,
.summary-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.stats {
  display: grid;
  margin-top: 18px;
  gap: 8px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  align-items: stretch;
}

.stat-pill {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 3px;
  min-height: 78px;
  text-align: center;
  border-radius: 18px;
  padding: 10px 4px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.68);
  width: 100%;
  min-width: 0;
}

.stat-pill--ok {
  background: rgba(234, 225, 246, 0.9);
}

.stat-pill--warn {
  background: var(--surface-lilac-deep);
}

.stat-pill--feature {
  background: linear-gradient(180deg, rgba(232, 221, 244, 0.98), rgba(243, 237, 249, 0.96));
}

.stat-pill__label,
.summary-card__label {
  display: block;
  font-size: 10px;
  line-height: 1.3;
  font-weight: 700;
  color: #6b7280;
}

.stat-pill__value,
.summary-card__value {
  display: block;
  margin-top: 0;
  font-size: 20px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: #111827;
}

.overview,
.recommend-panel {
  display: grid;
  gap: 16px;
  padding: 20px;
  border-radius: 28px;
}

.recommend-card__next {
  font-size: 12px;
  line-height: 1.5;
  color: #6b7280;
}

.recommend-provider-list {
  display: grid;
  gap: 10px;
}

.recommend-provider-card {
  display: grid;
  gap: 6px;
  border-radius: 18px;
  padding: 14px 15px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(239, 231, 247, 0.92);
}

.recommend-provider-card--failed {
  border-color: rgba(139, 121, 157, 0.18);
  background: var(--lilac-bg);
}

.recommend-provider-card--empty {
  background: rgba(237, 228, 245, 0.88);
}

.recommend-provider-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
  color: #221a30;
}

.recommend-provider-card__top span,
.recommend-provider-card p {
  font-size: 12px;
  line-height: 1.55;
  color: #6b7280;
}

.section-head h2,
.recent-inline__head h3 {
  margin: 0;
  font-size: 18px;
  letter-spacing: -0.02em;
  color: #111827;
}

.section-head p {
  margin-top: 4px;
  font-size: 13px;
  line-height: 1.55;
  max-width: 28rem;
}

.focus-card {
  display: grid;
  gap: 12px;
  width: 100%;
  padding: 18px;
  text-align: left;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(247, 241, 251, 0.98), rgba(228, 217, 241, 0.92));
  border: 1px solid rgba(17, 24, 39, 0.08);
}

.focus-card__title,
.recommend-card__title,
.quick-card__title {
  margin: 0;
  font-size: 18px;
  line-height: 1.35;
  color: #111827;
}

.focus-card__cta {
  color: var(--primary-deep);
  font-size: 13px;
  font-weight: 700;
}

.summary-card {
  display: grid;
  gap: 6px;
  width: 100%;
  padding: 16px;
  text-align: left;
  border-radius: 20px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(238, 230, 246, 0.92);
}

.summary-card--soft {
  background: var(--surface-lilac);
}

.summary-card__note {
  font-size: 12px;
  line-height: 1.5;
}

.recent-inline {
  display: grid;
  gap: 10px;
}

.video-item,
.recommend-card,
.quick-card {
  width: 100%;
  padding: 16px;
  text-align: left;
  border-radius: 20px;
}

.video-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.video-item__info {
  min-width: 0;
}

.video-item__title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  overflow-wrap: anywhere;
  word-break: break-word;
  color: #111827;
}

.video-item__status {
  display: inline-flex;
  align-items: center;
  margin-top: 6px;
  border-radius: 999px;
  padding: 3px 9px;
  font-size: 11px;
  font-weight: 700;
}

.status--ok {
  background: var(--ok-bg);
  color: var(--ok-text);
}

.status--warn {
  background: var(--lilac-bg);
  color: var(--lilac-text);
}

.status--bad {
  background: var(--lilac-bg);
  color: var(--lilac-text);
}

.status--info {
  background: var(--info-bg);
  color: var(--info-text);
}

.video-item__arrow {
  color: #8b7da3;
  font-size: 20px;
  line-height: 1;
}

.recommend-list {
  grid-template-columns: 1fr;
}

.recommend-card {
  display: grid;
  gap: 10px;
  background: rgba(238, 230, 246, 0.92);
  border-radius: 20px;
  padding: 16px;
}

.recommend-card__reason {
  padding-inline: 9px;
}

.recommend-card__desc,
.recommend-card__meta {
  margin: 0;
  font-size: 12px;
  line-height: 1.55;
}

.recommend-card__hint {
  font-size: 12px;
  line-height: 1.6;
  color: var(--primary-deep);
  border-radius: 16px;
  padding: 10px 12px;
  background: rgba(240, 232, 245, 0.72);
  border: 1px solid rgba(139, 121, 157, 0.14);
}

.recommend-card__next {
  color: var(--primary-deep);
  font-weight: 700;
}

.message {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  border-radius: 18px;
  padding: 14px;
  font-size: 13px;
  background: rgba(238, 230, 246, 0.92);
  border: 1px dashed rgba(17, 24, 39, 0.12);
}

.message--error {
  background: var(--lilac-bg);
  color: var(--lilac-text);
  border-style: solid;
  border-color: rgba(139, 121, 157, 0.14);
}

.message--empty {
  justify-content: flex-start;
}

.message--hint {
  justify-content: flex-start;
  color: var(--primary-deep);
  background: var(--surface-lilac);
  border-style: solid;
  border-color: var(--primary-soft);
}

.message--warn {
  justify-content: flex-start;
  color: rgba(120, 53, 15, 0.95);
  background: rgba(254, 243, 199, 0.95);
  border-style: solid;
  border-color: rgba(251, 191, 36, 0.45);
}

.skeleton-item {
  height: 64px;
  border-radius: 18px;
  background: linear-gradient(90deg, #f2ecf9, #e5daf2, #f2ecf9);
  background-size: 220% 100%;
  animation: shimmer 1.2s linear infinite;
}

.skeleton-item--tall {
  height: 132px;
}

@keyframes shimmer {
  from {
    background-position: 0% 0;
  }

  to {
    background-position: 220% 0;
  }
}

@media (max-width: 640px) {
  .welcome {
    padding: 20px;
  }

  .welcome__hero,
  .hero-actions,
  .summary-grid,
  .recommend-list {
    grid-template-columns: 1fr;
  }

  .welcome__top {
    align-items: flex-start;
  }

  .welcome__brand {
    min-width: 0;
  }

  .welcome__brand-surface {
    width: auto;
    padding: 0;
    border-radius: 0;
  }

  .welcome__brand-icon {
    width: 64px;
    height: 64px;
    padding: 6px;
    border-radius: 18px;
  }

  .welcome__brand-title {
    font-size: 15px;
  }

  .stats {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 6px;
  }

  .stat-pill {
    min-height: 70px;
    padding: 8px 2px;
  }

  .welcome__title {
    font-size: 30px;
  }
}
</style>
