<template>
  <div class="ios-page home-page">
    <header class="welcome ios-card">
      <div class="welcome__top">
        <div class="welcome__brand">
          <BrandLogo :width="138" compact />
        </div>
        <button class="guide-btn" @click="go('/guide')" aria-label="打开使用指南">使用指南</button>
      </div>

      <div class="welcome__hero">
        <div class="welcome__copy">
          <p class="welcome__eyebrow">首页更聚焦</p>
          <h1 class="welcome__title gradient-text">智能伴学中心</h1>
          <p class="welcome__subtitle">先上传，再跟进处理，最后复盘沉淀，不用在多个页面之间反复找入口。</p>
        </div>
        <div class="hero-actions">
          <button class="hero-btn hero-btn--primary" @click="go('/upload')">上传新内容</button>
          <button class="hero-btn hero-btn--secondary" @click="go('/videos')">查看视频库</button>
        </div>
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
          <h2>继续学习</h2>
          <p>把最近任务和本地离线结果收口到一个区域里，减少来回跳转。</p>
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
          <p>高频动作留在前面，低频入口收成轻量跳转。</p>
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
          <h2>推荐视频</h2>
          <p>预留真实后端推荐链路，优先返回值得继续处理、复盘或与你方向相关的内容。</p>
        </div>
        <button class="overview-link" @click="reloadRecommendations" :disabled="recommendationLoading">
          {{ recommendationLoading ? '刷新中…' : '刷新推荐' }}
        </button>
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
          v-for="item in recommendations"
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
            <span v-if="formatTimeText(item.upload_time)">{{ formatTimeText(item.upload_time) }}</span>
          </div>
        </button>
      </div>

      <button class="hero-btn hero-btn--secondary" @click="go('/recommendations')">打开推荐页</button>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import BrandLogo from '@/components/BrandLogo.vue'
import { getVideoRecommendations } from '@/api/recommendation'
import { getVideoList } from '@/api/video'
import { listNativeOfflineTranscripts } from '@/services/nativeOfflineTranscripts'
import { isActiveVideoStatus, isCompletedVideoStatus, videoStatusText, videoStatusTone } from '@/services/videoStatus'

const quickActions = [
  { route: '/local-transcripts', tag: '本地', tagClass: 'tag--mint', title: '本地转录', desc: '查看 iOS 离线转录结果' },
  { route: '/notes', tag: '笔记', tagClass: 'tag--leaf', title: '学习笔记', desc: '把结论沉淀成稳定回看入口' },
  { route: '/qa', tag: '问答', tagClass: 'tag--amber', title: 'AI 问答', desc: '围绕课程内容继续追问' },
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

const supportActions = computed(() => quickActions)

const normalizeList = (payload) => {
  const list = payload?.videos || payload?.items || payload?.data || payload || []
  return Array.isArray(list) ? list : []
}

const normalizeRecommendationItems = (payload) => {
  const items = payload?.items || payload?.recommendations || payload?.data || []
  return Array.isArray(items) ? items : []
}

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
    const res = await getVideoRecommendations({ scene: 'home', limit: 4 })
    const items = normalizeRecommendationItems(res?.data || {})
    recommendations.value = items.length > 0 ? items : fallbackRecommendations(allVideos.value)
  } catch (e) {
    recommendationError.value = e?.message || '推荐加载失败'
    recommendations.value = fallbackRecommendations(allVideos.value)
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

const recommendationKey = (item) =>
  String(item?.id || item?.external_url || item?.target_url || item?.source_url || item?.link || item?.title || 'recommendation')

const resolveRecommendationUrl = (item) =>
  String(item?.external_url || item?.target_url || item?.source_url || item?.link || '').trim()

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

const openRecommendation = (item) => {
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
  gap: 14px;
  padding-top: calc(16px + env(safe-area-inset-top));
}

.welcome {
  position: relative;
  overflow: hidden;
  padding: 22px;
  border-radius: 28px;
  border: 1px solid rgba(24, 45, 73, 0.08);
  background: linear-gradient(155deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 251, 252, 0.9) 58%, rgba(232, 247, 250, 0.84) 100%);
  box-shadow: 0 10px 28px rgba(24, 45, 73, 0.08);
}

.welcome::after {
  content: '';
  position: absolute;
  width: 180px;
  height: 180px;
  right: -70px;
  top: -90px;
  border-radius: 999px;
  transform: none;
  background: radial-gradient(circle, rgba(31, 122, 140, 0.14) 0%, rgba(31, 122, 140, 0.03) 62%, transparent 74%);
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
  display: inline-flex;
  align-items: center;
  min-width: 132px;
}

.guide-btn,
.overview-link {
  border: 0;
  background: transparent;
  color: var(--primary-deep);
  font-size: 13px;
  font-weight: 800;
}

.guide-btn {
  border: 1px solid rgba(24, 45, 73, 0.08);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  padding: 6px 12px;
}

.welcome__hero {
  display: grid;
  gap: 16px;
  margin-top: 16px;
}

.welcome__eyebrow,
.focus-card__eyebrow,
.recommend-card__reason {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 800;
  background: rgba(31, 122, 140, 0.12);
  color: var(--primary-deep);
}

.welcome__title {
  margin: 8px 0 0;
  font-size: 31px;
  line-height: 1.08;
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
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.6;
  max-width: 32rem;
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
}

.hero-btn,
.stat-pill,
.summary-card,
.focus-card,
.recommend-card,
.video-item,
.support-link {
  border: 1px solid rgba(24, 45, 73, 0.08);
  background: rgba(255, 255, 255, 0.88);
}

.hero-btn {
  border-radius: 14px;
  padding: 13px 14px;
  font-size: 14px;
  font-weight: 900;
}

.hero-btn--primary {
  border: 0;
  color: #f4feff;
  background: linear-gradient(135deg, #145b66, #1f7a8c);
  box-shadow: 0 10px 18px rgba(31, 122, 140, 0.18);
}

.hero-btn--secondary {
  color: var(--primary-deep);
}

.stats,
.summary-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.stats {
  display: grid;
  margin-top: 16px;
  gap: 6px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  align-items: stretch;
}

.stat-pill {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 3px;
  min-height: 74px;
  text-align: center;
  border-radius: 12px;
  padding: 8px 4px;
  box-shadow: none;
  width: 100%;
  min-width: 0;
}

.stat-pill--ok {
  background: rgba(31, 157, 116, 0.1);
}

.stat-pill--warn {
  background: rgba(242, 154, 74, 0.14);
}

.stat-pill--feature {
  background: linear-gradient(135deg, rgba(20, 91, 102, 0.16), rgba(31, 122, 140, 0.08));
}

.stat-pill__label,
.summary-card__label {
  display: block;
  font-size: 10px;
  line-height: 1.3;
  font-weight: 700;
  color: var(--muted);
}

.stat-pill__value,
.summary-card__value {
  display: block;
  margin-top: 0;
  font-size: 18px;
  line-height: 1;
  font-weight: 900;
  color: var(--text);
}

.overview,
.recommend-panel,
.support-strip {
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: 24px;
  border: 1px solid rgba(24, 45, 73, 0.08);
  background: rgba(255, 255, 255, 0.7);
  box-shadow: 0 10px 24px rgba(24, 45, 73, 0.06);
}

.section-head h2,
.recent-inline__head h3 {
  margin: 0;
  font-size: 17px;
}

.section-head p {
  margin-top: 4px;
  font-size: 13px;
  line-height: 1.55;
}

.focus-card {
  display: grid;
  gap: 10px;
  width: 100%;
  padding: 18px 16px;
  text-align: left;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 251, 252, 0.94));
  border-left: 4px solid rgba(31, 122, 140, 0.5);
}

.focus-card__title,
.recommend-card__title,
.quick-card__title {
  margin: 0;
  font-size: 17px;
  color: #1f2a37;
}

.focus-card__cta {
  color: var(--primary-deep);
  font-size: 13px;
  font-weight: 800;
}

.summary-card {
  display: grid;
  gap: 6px;
  width: 100%;
  padding: 14px;
  text-align: left;
  border-radius: 16px;
  border: 1px solid rgba(24, 45, 73, 0.08);
  background: rgba(255, 255, 255, 0.82);
}

.summary-card--soft {
  background: rgba(244, 250, 252, 0.92);
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
  padding: 14px;
  text-align: left;
  border-radius: 18px;
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
  font-weight: 800;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.video-item__status {
  display: inline-flex;
  align-items: center;
  margin-top: 6px;
  border-radius: 999px;
  padding: 3px 9px;
  font-size: 11px;
  font-weight: 800;
}

.status--ok {
  background: var(--ok-bg);
  color: var(--ok-text);
}

.status--warn {
  background: var(--warn-bg);
  color: var(--warn-text);
}

.status--bad {
  background: var(--bad-bg);
  color: var(--bad-text);
}

.status--info {
  background: var(--info-bg);
  color: var(--info-text);
}

.video-item__arrow,
.support-card__arrow {
  color: #8ba4ae;
  font-size: 20px;
  line-height: 1;
}

.quick-card__tag {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 9px;
  font-size: 11px;
  font-weight: 800;
}

.tag--mint {
  background: rgba(31, 157, 116, 0.14);
  color: #0f6c4f;
}

.tag--leaf {
  background: rgba(114, 196, 106, 0.14);
  color: #326f2e;
}

.tag--amber {
  background: rgba(242, 154, 74, 0.16);
  color: #905214;
}

.tag--teal {
  background: rgba(76, 173, 195, 0.16);
  color: #166376;
}

.tag--cobalt {
  background: rgba(60, 104, 221, 0.14);
  color: #274ba4;
}

.section-head--compact {
  align-items: flex-start;
}

.support-strip__list {
  display: grid;
  gap: 10px;
}

.support-link {
  width: 100%;
  border-radius: 16px;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  text-align: left;
}

.support-link__label {
  flex: 1;
  font-size: 14px;
  font-weight: 800;
  color: #1f2a37;
}

.support-link__arrow {
  color: #8ba4ae;
  font-size: 18px;
}

.recommend-list {
  grid-template-columns: 1fr;
}

.recommend-card {
  display: grid;
  gap: 8px;
  background: rgba(255, 255, 255, 0.86);
  border-radius: 18px;
  padding: 14px 15px;
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

.message {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  border-radius: 16px;
  padding: 14px;
  font-size: 13px;
  background: var(--card-soft);
}

.message--error {
  background: rgba(223, 82, 82, 0.1);
  color: #aa3232;
}

.message--empty {
  justify-content: flex-start;
}

.skeleton-item {
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(90deg, #edf3f0, #e3efe9, #edf3f0);
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
  .hero-actions,
  .summary-grid,
  .recommend-list {
    grid-template-columns: 1fr;
  }

  .stats {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 6px;
  }

  .stat-pill {
    min-height: 70px;
    padding: 8px 2px;
  }
}
</style>
