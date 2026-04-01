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

      <div class="welcome__subnote">
        <span>推荐页会继续承接站内学习与站外导入，首页只保留最重要的下一步。</span>
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
          <p>把最近任务、本地离线结果和回看入口压缩成一屏里的稳定节奏。</p>
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
          <button class="summary-card" @click="go('/local-transcripts')">
            <span class="summary-card__label">本地离线转录</span>
            <strong class="summary-card__value">{{ localTranscriptCount }}</strong>
            <span class="summary-card__note">查看 iOS 端侧转录结果</span>
          </button>
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

    <section class="support-strip ios-card">
      <div class="section-head section-head--compact">
        <div>
          <h2>辅助入口</h2>
          <p>保留高频学习动作，其余入口用轻量方式承接，不打断主页面节奏。</p>
        </div>
      </div>
      <div class="support-strip__list">
        <button
          v-for="item in supportActions"
          :key="item.route"
          class="support-link"
          @click="go(item.route)"
        >
          <span class="quick-card__tag" :class="item.tagClass">{{ item.tag }}</span>
          <span class="support-link__label">{{ item.title }}</span>
          <span class="support-link__arrow">›</span>
        </button>
      </div>
    </section>

    <section class="recommend-panel ios-card">
      <div class="section-head">
        <div>
          <h2>推荐中枢预览</h2>
          <p>首页只预览最值得继续的方向，真正的相关推荐和站外导入放进推荐页里完成。</p>
        </div>
        <button class="overview-link" @click="reloadRecommendations" :disabled="recommendationLoading">
          {{ recommendationLoading ? '刷新中…' : '刷新推荐' }}
        </button>
      </div>

      <div v-if="recommendations.length > 0" class="recommend-summary">
        <article class="recommend-summary__card">
          <span class="recommend-summary__label">当前预览</span>
          <strong class="recommend-summary__value">{{ recommendations.length }}</strong>
          <span class="recommend-summary__note">首页先看最值得继续的 {{ recommendations.length }} 条内容</span>
        </article>
        <article class="recommend-summary__card recommend-summary__card--soft">
          <span class="recommend-summary__label">结果构成</span>
          <strong class="recommend-summary__value">{{ recommendationMixValue }}</strong>
          <span class="recommend-summary__note">{{ recommendationMixNote }}</span>
        </article>
        <article class="recommend-summary__card recommend-summary__card--action">
          <span class="recommend-summary__label">下一步</span>
          <strong class="recommend-summary__value">进推荐页</strong>
          <span class="recommend-summary__note">继续筛场景、看相关推荐或导入站外候选</span>
        </article>
      </div>

      <div v-if="recommendationQuerySummary" class="message message--hint">
        <span>本轮站外检索围绕：{{ recommendationQuerySummary }}</span>
      </div>

      <div v-if="recommendationExternalFetchBanner" class="message message--warn">
        <span>{{ recommendationExternalFetchBanner }}</span>
        <button type="button" class="overview-link" @click="go('/recommendations')">去推荐页</button>
      </div>

      <div v-if="recommendationProviderReports.length > 0" class="recommend-provider-list">
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
        <button class="overview-link" @click="go('/videos')">查看视频库</button>
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
          <p class="recommend-card__desc">{{ item.reason_text || item.summary || '从这里继续进入学习。' }}</p>
          <div class="recommend-card__meta">
            <span v-if="Array.isArray(item.tags) && item.tags.length > 0">{{ item.tags.slice(0, 2).join(' · ') }}</span>
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
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import BrandLogo from '@/components/BrandLogo.vue'
import { getVideoRecommendations } from '@/api/recommendation'
import { shouldIncludeExternalRecommendationsByDefault } from '@/config'
import { getVideoList } from '@/api/video'
import { listNativeOfflineTranscripts } from '@/services/nativeOfflineTranscripts'
import { isActiveVideoStatus, isCompletedVideoStatus, videoStatusText, videoStatusTone } from '@/services/videoStatus'

const quickActions = [
  { route: '/local-transcripts', tag: '本地', tagClass: 'tag--mint', title: '本地转录', desc: '查看 iOS 离线转录结果' },
  { route: '/notes', tag: '笔记', tagClass: 'tag--leaf', title: '学习笔记', desc: '把结论沉淀成稳定回看入口' },
  { route: '/qa', tag: '问答', tagClass: 'tag--lilac', title: 'AI 问答', desc: '围绕课程内容继续追问' },
  { route: '/recommendations', tag: '推荐', tagClass: 'tag--cobalt', title: '推荐学习', desc: '集中查看继续学习、复盘与相关推荐' },
  { route: '/learning-path', tag: '路径', tagClass: 'tag--teal', title: '学习路径', desc: '后续承接推荐学习顺序' }
]

const router = useRouter()
const loading = ref(false)
const recommendationLoading = ref(false)
const error = ref('')
const recommendationError = ref('')
const allVideos = ref([])
const localTranscriptCount = ref(0)
const recommendations = ref([])
const recommendationMeta = ref({
  sources: [],
  externalProviders: [],
  externalQuery: null,
  internalItemCount: 0,
  externalItemCount: 0,
  externalFailedProviderCount: 0,
  externalFetchFailed: false
})

const supportActions = computed(() => quickActions)

const normalizeList = (payload) => {
  const list = payload?.videos || payload?.items || payload?.data || payload || []
  return Array.isArray(list) ? list : []
}

const normalizeRecommendationItems = (payload) => {
  const items = payload?.items || payload?.recommendations || payload?.data || []
  return Array.isArray(items) ? items : []
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
  externalFetchFailed: false
})
const buildRecommendationMeta = (payload) => ({
  sources: normalizeRecommendationSources(payload),
  externalProviders: normalizeRecommendationProviders(payload),
  externalQuery: normalizeRecommendationQuery(payload),
  internalItemCount: normalizeRecommendationCount(payload, 'internal_item_count'),
  externalItemCount: normalizeRecommendationCount(payload, 'external_item_count'),
  externalFailedProviderCount: normalizeRecommendationCount(payload, 'external_failed_provider_count'),
  externalFetchFailed: Boolean(payload?.external_fetch_failed || false)
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
  videos.slice(0, 4).map((video, index) => ({
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
    const [videos, transcripts] = await Promise.all([
      fetchAllVideos(),
      listNativeOfflineTranscripts().catch(() => [])
    ])
    allVideos.value = mergeVideosById(videos)
    localTranscriptCount.value = transcripts.length
  } catch (e) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const reloadRecommendations = async () => {
  recommendationLoading.value = true
  recommendationError.value = ''
  try {
    const res = await getVideoRecommendations({
      scene: 'home',
      limit: 4,
      include_external: shouldIncludeExternalRecommendationsByDefault()
    })
    const payload = res?.data || {}
    const items = normalizeRecommendationItems(payload)
    recommendations.value = items.length > 0 ? items : fallbackRecommendations(allVideos.value)
    recommendationMeta.value = buildRecommendationMeta(payload)
  } catch (e) {
    recommendationError.value = e?.message || '推荐加载失败'
    recommendations.value = fallbackRecommendations(allVideos.value)
    recommendationMeta.value = createRecommendationMeta()
  } finally {
    recommendationLoading.value = false
  }
}

const go = (path) => router.push(path)
const goStat = (scope) => {
  console.info(`[INFO][Home] stat-card-click scope=${scope}`)
  router.push({ path: '/videos', query: { scope } })
}

const openVideo = (video) => {
  const current = video || {}
  if (current.processing_origin === 'ios_offline' && current.task_id) {
    router.push(`/local-transcripts/${current.task_id}`)
    return
  }
  if (!current.id) return
  router.push(`/videos/${current.id}`)
}

const recommendationEmptyText = computed(() => {
  if (recommendationError.value) return recommendationError.value
  return '上传更多视频后，这里会按处理状态和内容相关度给你推荐下一步。'
})
const decorateRecommendationItem = (item) => ({
  ...item,
  subjectText: String(item?.subject || '').trim() ? `科目 · ${String(item.subject).trim()}` : '',
  importHint: String(item?.import_hint || '').trim(),
  actionTarget: String(item?.action_target || '').trim(),
  primaryActionDisabled: isExternalRecommendation(item)
    ? !Boolean(item?.can_import ?? resolveRecommendationUrl(item))
    : false
})
const recommendationCards = computed(() => recommendations.value.map((item) => decorateRecommendationItem(item)))
const externalRecommendationCount = computed(() => recommendationCards.value.filter((item) => isExternalRecommendation(item)).length)
const internalRecommendationCount = computed(() => {
  if (recommendationMeta.value.internalItemCount > 0 || recommendationMeta.value.externalItemCount > 0) {
    return recommendationMeta.value.internalItemCount
  }
  return Math.max(recommendationCards.value.length - externalRecommendationCount.value, 0)
})
const recommendationProviderReports = computed(() => recommendationMeta.value.externalProviders || [])
const recommendationQuerySummary = computed(() => {
  const query = recommendationMeta.value.externalQuery
  if (!query) return ''
  const parts = [query.subject, query.primary_topic].filter(Boolean)
  if (Array.isArray(query.preferred_tags) && query.preferred_tags.length > 0) {
    parts.push(`优先标签：${query.preferred_tags.join('、')}`)
  }
  return parts.join(' · ')
})
const recommendationMixValue = computed(() => {
  if (externalRecommendationCount.value === 0) return `站内 ${internalRecommendationCount.value}`
  return `${internalRecommendationCount.value} / ${externalRecommendationCount.value}`
})
const recommendationMixNote = computed(() => {
  if (recommendations.value.length === 0) return '当前还没有推荐结果。'
  if (externalRecommendationCount.value === 0) return '当前首页预览以站内学习内容为主。'
  if (internalRecommendationCount.value === 0) return '当前首页预览以站外候选为主。'
  return `站内 ${internalRecommendationCount.value} 条，站外 ${externalRecommendationCount.value} 条。`
})
const providerStatusText = (provider) => {
  if (provider?.status === 'failed') return '抓取失败'
  if (provider?.status === 'empty') return '暂无候选'
  return `${Number(provider?.candidate_count || 0)} 条候选`
}
const recommendationExternalFetchBanner = computed(() => {
  if (!recommendationMeta.value.externalFetchFailed) return ''
  return '部分站外来源未返回结果，站内推荐仍可使用。可检查网络后刷新本页，或前往推荐页重试；若需加快首屏，请保持关闭站外（环境变量 VITE_RECOMMENDATION_INCLUDE_EXTERNAL）。'
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

const resolveRecommendationUrl = (item) =>
  String(item?.external_url || item?.target_url || item?.source_url || item?.link || '').trim()
const parseRecommendationActionTarget = (target) => {
  const text = String(target || '').trim()
  if (!text || !text.startsWith('/')) return null
  const [path, search = ''] = text.split('?')
  if (!search) return { path }
  const query = {}
  new URLSearchParams(search).forEach((value, key) => {
    query[key] = value
  })
  return { path, query }
}

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
  const actionLocation = parseRecommendationActionTarget(item?.actionTarget || item?.action_target)
  if (actionLocation) {
    router.push(actionLocation)
    return
  }
  if (isExternalRecommendation(item)) {
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
  await Promise.all([reload(), reloadRecommendations()])
}

onMounted(reloadDashboard)
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
.recommend-panel,
.support-strip {
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
.recommend-summary,
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

.hero-btn,
.stat-pill,
.summary-card,
.focus-card,
.recommend-card,
.video-item,
.support-link {
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
.recommend-panel,
.support-strip {
  display: grid;
  gap: 16px;
  padding: 20px;
  border-radius: 28px;
}

.recommend-summary {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.recommend-summary__card {
  display: grid;
  gap: 5px;
  border-radius: 20px;
  padding: 15px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(239, 231, 247, 0.92);
}

.recommend-summary__card--soft {
  background: rgba(232, 221, 244, 0.94);
}

.recommend-summary__card--action {
  background: linear-gradient(180deg, rgba(223, 210, 238, 0.98), rgba(244, 238, 249, 0.96));
}

.recommend-summary__label,
.recommend-summary__note,
.recommend-card__next {
  font-size: 12px;
  line-height: 1.5;
  color: #6b7280;
}

.recommend-summary__value {
  font-size: 19px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #111827;
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

.video-item__arrow,
.support-card__arrow {
  color: #8b7da3;
  font-size: 20px;
  line-height: 1;
}

.quick-card__tag {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 9px;
  font-size: 11px;
  font-weight: 700;
}

.tag--mint {
  background: rgba(234, 225, 246, 0.92);
  color: var(--ok-text);
}

.tag--leaf {
  background: rgba(233, 224, 243, 0.92);
  color: #6b5b84;
}

.tag--lilac {
  background: var(--lilac-bg);
  color: var(--lilac-text);
}

.tag--teal {
  background: rgba(231, 220, 243, 0.94);
  color: #6e5d7f;
}

.tag--cobalt {
  background: var(--info-bg);
  color: var(--info-text);
}

.section-head--compact {
  align-items: flex-start;
}

.support-strip__list {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.support-link {
  width: 100%;
  border-radius: 18px;
  padding: 14px 15px;
  display: flex;
  align-items: center;
  gap: 10px;
  text-align: left;
}

.support-link__label {
  flex: 1;
  font-size: 14px;
  font-weight: 700;
  color: #111827;
}

.support-link__arrow {
  color: #8b7da3;
  font-size: 18px;
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
  .recommend-summary,
  .recommend-list,
  .support-strip__list {
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
