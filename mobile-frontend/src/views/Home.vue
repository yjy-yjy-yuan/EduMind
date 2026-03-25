<template>
  <div class="ios-page home-page">
    <header class="welcome ios-card">
      <div class="welcome__top">
        <div class="welcome__brand">
          <BrandLogo :width="138" compact />
        </div>
        <button class="guide-btn" @click="go('/guide')" aria-label="打开使用指南">使用指南</button>
      </div>
      <h1 class="welcome__title gradient-text">智能伴学中心</h1>
      <p class="welcome__subtitle">围绕你的学习流程，快速进入视频、笔记、问答与知识梳理。</p>

      <div class="stats">
        <button type="button" class="stat-pill stat-pill--link" @click="goStat('recent')">
          <span class="stat-pill__label">最近视频</span>
          <strong class="stat-pill__value">{{ recentCount }}</strong>
        </button>
        <button type="button" class="stat-pill stat-pill--link stat-pill--ok" @click="goStat('completed')">
          <span class="stat-pill__label">已完成</span>
          <strong class="stat-pill__value">{{ completedCount }}</strong>
        </button>
        <button type="button" class="stat-pill stat-pill--link stat-pill--warn" @click="goStat('active')">
          <span class="stat-pill__label">进行中</span>
          <strong class="stat-pill__value">{{ inProgressCount }}</strong>
        </button>
      </div>
    </header>

    <section class="quick-grid">
      <button
        v-for="item in quickActions"
        :key="item.route"
        class="quick-card ios-card"
        @click="go(item.route)"
      >
        <span class="quick-card__tag" :class="item.tagClass">{{ item.tag }}</span>
        <h2 class="quick-card__title">{{ item.title }}</h2>
        <p class="quick-card__desc">{{ item.desc }}</p>
      </button>
    </section>

    <section class="recent ios-card">
      <div class="recent__head">
        <h3>本地离线转录</h3>
        <button class="refresh-btn" @click="reload" :disabled="loading || recommendationLoading">
          {{ loading ? '加载中…' : '刷新' }}
        </button>
      </div>
      <div class="message">
        当前已保存 {{ localTranscriptCount }} 条本地离线转录结果。
        <button class="message__link" @click="go('/local-transcripts')">查看列表</button>
      </div>
    </section>

    <section class="recent ios-card">
      <div class="recent__head">
        <h3>最近学习内容</h3>
        <button class="refresh-btn" @click="reload" :disabled="loading || recommendationLoading">
          {{ loading ? '加载中…' : '刷新' }}
        </button>
      </div>

      <div v-if="error" class="message message--error">
        <span>{{ error }}</span>
        <button class="message__link" @click="reload">重试</button>
      </div>

      <div v-else-if="loading" class="skeleton-list">
        <div v-for="i in 3" :key="i" class="skeleton-item"></div>
      </div>

      <div v-else-if="allVideos.length === 0" class="message">暂无视频，先上传一个开始学习吧。</div>

      <div v-else class="video-list">
        <button v-for="video in recentVideos" :key="video.id" class="video-item" @click="openVideo(video)">
          <div class="video-item__info">
            <p class="video-item__title">{{ video.title || '未命名视频' }}</p>
            <span class="video-item__status" :class="statusClass(video.status)">{{ statusText(video.status) }}</span>
          </div>
          <span class="video-item__arrow">›</span>
        </button>
      </div>
    </section>

    <section class="recent ios-card">
      <div class="recent__head">
        <h3>推荐视频</h3>
        <button class="refresh-btn" @click="reloadRecommendations" :disabled="recommendationLoading">
          {{ recommendationLoading ? '加载中…' : '刷新推荐' }}
        </button>
      </div>

      <div v-if="recommendationLoading && recommendations.length === 0" class="skeleton-list">
        <div v-for="i in 2" :key="`recommend-${i}`" class="skeleton-item skeleton-item--tall"></div>
      </div>

      <div v-else-if="recommendations.length === 0" class="message">
        <span>{{ recommendationEmptyText }}</span>
        <button class="message__link" @click="go('/videos')">查看视频库</button>
      </div>

      <div v-else class="recommend-list">
        <button
          v-for="item in recommendations"
          :key="item.id"
          class="recommend-item"
          @click="openRecommendation(item)"
        >
          <div class="recommend-item__top">
            <span class="recommend-item__reason">{{ item.reason_label || '推荐' }}</span>
            <span class="video-item__status" :class="statusClass(item.status)">{{ statusText(item.status) }}</span>
          </div>
          <p class="recommend-item__title">{{ item.title || '未命名视频' }}</p>
          <p class="recommend-item__desc">{{ item.reason_text || item.summary || '从这里继续进入学习。' }}</p>
          <div class="recommend-item__meta">
            <span v-if="Array.isArray(item.tags) && item.tags.length > 0">{{ item.tags.slice(0, 2).join(' · ') }}</span>
            <span v-if="formatTimeText(item.upload_time)">{{ formatTimeText(item.upload_time) }}</span>
          </div>
        </button>
      </div>
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
  { route: '/videos', tag: '视频', tagClass: 'tag--mint', title: '视频库', desc: '查看列表与处理状态' },
  { route: '/upload', tag: '上传', tagClass: 'tag--teal', title: '上传中心', desc: '支持本地文件和链接' },
  { route: '/local-transcripts', tag: '本地', tagClass: 'tag--mint', title: '本地转录', desc: '查看 iOS 离线转录结果' },
  { route: '/notes', tag: '笔记', tagClass: 'tag--leaf', title: '学习笔记', desc: '随学随记，整理知识片段' },
  { route: '/qa', tag: '问答', tagClass: 'tag--amber', title: 'AI 问答', desc: '基于课程内容即时提问' },
  { route: '/learning-path', tag: '路径', tagClass: 'tag--teal', title: '学习路径', desc: '获取下一步学习建议' }
]

const router = useRouter()
const loading = ref(false)
const recommendationLoading = ref(false)
const error = ref('')
const recommendationError = ref('')
const allVideos = ref([])
const localTranscriptCount = ref(0)
const recommendations = ref([])

const normalizeList = (payload) => {
  const list = payload?.videos || payload?.items || payload?.data || payload || []
  return Array.isArray(list) ? list : []
}

const normalizeRecommendationItems = (payload) => {
  const items = payload?.items || payload?.recommendations || payload?.data || []
  return Array.isArray(items) ? items : []
}

const resolveVideoTime = (video) => {
  const current = video || {}
  return current.upload_time || current.updated_at || current.created_at || ''
}

const mergeVideosById = (items) => {
  const map = new Map()
  for (const item of items) {
    if (!item?.id) continue
    map.set(Number(item.id), item)
  }
  return Array.from(map.values()).sort((a, b) => new Date(resolveVideoTime(b)).getTime() - new Date(resolveVideoTime(a)).getTime())
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

const fallbackRecommendations = (videos) =>
  videos.slice(0, 4).map((video, index) => ({
    ...video,
    reason_label: index === 0 ? '继续学习' : '最近内容',
    reason_text: index === 0 ? '当前最适合从这个任务继续进入。' : '最近进入视频库，适合继续学习。'
  }))

const statusText = videoStatusText

const statusClass = (status) => {
  const tone = videoStatusTone(status)
  if (tone === 'ok') return 'status--ok'
  if (tone === 'bad') return 'status--bad'
  if (tone === 'warn') return 'status--warn'
  return 'status--info'
}

const recentVideos = computed(() => allVideos.value.slice(0, 5))
const recentCount = computed(() => allVideos.value.length)
const completedCount = computed(() => allVideos.value.filter((item) => isCompletedVideoStatus(item?.status)).length)
const inProgressCount = computed(() => allVideos.value.filter((item) => isActiveVideoStatus(item?.status)).length)
const recommendationEmptyText = computed(() => {
  if (recommendationError.value) return recommendationError.value
  return '上传更多视频后，这里会按处理状态和内容相关度给你推荐下一步。'
})

const fetchAllVideos = async () => {
  const first = await getVideoList(1, 100)
  const firstPayload = first?.data || {}
  const firstList = normalizeList(firstPayload)
  const totalPages = Math.max(1, Number(firstPayload?.total_pages || 1))
  if (totalPages <= 1) return firstList

  const all = [...firstList]
  for (let page = 2; page <= totalPages; page += 1) {
    const res = await getVideoList(page, 100)
    all.push(...normalizeList(res?.data || {}))
  }
  return all
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

const reload = async () => {
  loading.value = true
  recommendationLoading.value = true
  error.value = ''
  recommendationError.value = ''

  const [videosResult, transcriptsResult, recommendationsResult] = await Promise.allSettled([
    fetchAllVideos(),
    listNativeOfflineTranscripts().catch(() => []),
    getVideoRecommendations({ scene: 'home', limit: 4 })
  ])

  let mergedVideos = allVideos.value

  if (videosResult.status === 'fulfilled') {
    mergedVideos = mergeVideosById(videosResult.value)
    allVideos.value = mergedVideos
  } else {
    error.value = videosResult.reason?.message || '加载失败'
  }

  if (transcriptsResult.status === 'fulfilled') {
    localTranscriptCount.value = Array.isArray(transcriptsResult.value) ? transcriptsResult.value.length : 0
  } else {
    localTranscriptCount.value = 0
  }

  if (recommendationsResult.status === 'fulfilled') {
    const items = normalizeRecommendationItems(recommendationsResult.value?.data || {})
    recommendations.value = items.length > 0 ? items : fallbackRecommendations(mergedVideos)
  } else {
    recommendationError.value = recommendationsResult.reason?.message || '推荐加载失败'
    recommendations.value = fallbackRecommendations(mergedVideos)
  }

  loading.value = false
  recommendationLoading.value = false
}

const go = (path) => router.push(path)
const goStat = (scope) => router.push({ path: '/videos', query: { scope } })

const openVideo = (video) => {
  const current = video || {}
  if (current.processing_origin === 'ios_offline' && current.task_id) {
    router.push(`/local-transcripts/${current.task_id}`)
    return
  }
  if (!current.id) return
  router.push(`/videos/${current.id}`)
}

const openRecommendation = (item) => openVideo(item)

onMounted(reload)
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
  padding: 20px;
  border-radius: 26px;
  border: 1px solid rgba(31, 122, 140, 0.16);
  background: linear-gradient(160deg, #ffffff 8%, #f2fbfc 92%);
  box-shadow: 0 20px 38px rgba(31, 122, 140, 0.14);
}

.welcome::after {
  content: '';
  position: absolute;
  width: 180px;
  height: 180px;
  right: -70px;
  top: -90px;
  border-radius: 54px;
  transform: rotate(18deg);
  background: linear-gradient(140deg, rgba(31, 122, 140, 0.18), rgba(31, 122, 140, 0.04));
  pointer-events: none;
}

.welcome__top,
.welcome__title,
.welcome__subtitle,
.stats {
  position: relative;
  z-index: 1;
}

.welcome__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.welcome__brand {
  display: inline-flex;
  align-items: center;
  flex: 0 0 auto;
  min-width: 132px;
}

.guide-btn {
  border: 1px solid rgba(31, 157, 116, 0.25);
  border-radius: 999px;
  background: rgba(31, 157, 116, 0.08);
  color: var(--primary-deep);
  font-size: 12px;
  font-weight: 700;
  padding: 6px 12px;
  flex: 0 0 auto;
}

.welcome__title {
  margin: 12px 0 0;
  font-size: 27px;
  line-height: 1.2;
  letter-spacing: 0.01em;
  text-shadow: 0 8px 22px rgba(22, 117, 190, 0.12);
}

.welcome__subtitle {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.5;
}

.stats {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.stat-pill {
  width: 100%;
  border: 1px solid rgba(32, 42, 55, 0.08);
  appearance: none;
  text-align: left;
  cursor: pointer;
  border-radius: 12px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.84);
}

.stat-pill--link {
  display: block;
  text-decoration: none;
  color: inherit;
}

.stat-pill--ok {
  background: rgba(55, 174, 115, 0.14);
}

.stat-pill--warn {
  background: rgba(242, 154, 74, 0.14);
}

.stat-pill__label {
  display: block;
  color: var(--muted);
  font-size: 11px;
  font-weight: 600;
}

.stat-pill__value {
  margin-top: 2px;
  display: block;
  font-size: 18px;
  color: var(--text);
}

.quick-grid {
  margin-top: 14px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.quick-card {
  text-align: left;
  border: 1px solid rgba(32, 42, 55, 0.08);
  padding: 14px;
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff, #f8fbff);
  box-shadow: 0 10px 22px rgba(24, 45, 73, 0.08);
}

.quick-card__tag,
.recommend-item__reason {
  display: inline-block;
  padding: 4px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.tag--mint {
  background: rgba(31, 157, 116, 0.14);
  color: #0f6c4f;
}

.tag--teal {
  background: rgba(76, 173, 195, 0.16);
  color: #166376;
}

.tag--leaf {
  background: rgba(114, 196, 106, 0.14);
  color: #326f2e;
}

.tag--amber {
  background: rgba(242, 154, 74, 0.16);
  color: #905214;
}

.quick-card__title {
  margin: 10px 0 0;
  font-size: 16px;
  color: #1f2a37;
}

.quick-card__desc,
.recommend-item__desc,
.recommend-item__meta {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--muted);
  line-height: 1.5;
}

.recent {
  margin-top: 14px;
  padding: 16px;
  border-radius: 24px;
  animation: rise-in 480ms ease-out;
}

.recent__head,
.recommend-item__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.recent__head h3 {
  margin: 0;
  font-size: 17px;
}

.refresh-btn {
  border: 0;
  background: transparent;
  color: var(--primary-deep);
  font-weight: 700;
  font-size: 13px;
}

.message {
  margin-top: 12px;
  border-radius: 12px;
  padding: 12px;
  color: var(--muted);
  font-size: 13px;
  background: var(--card-soft);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.message--error {
  color: #aa3232;
  background: rgba(223, 82, 82, 0.1);
}

.message__link {
  border: 0;
  background: transparent;
  color: #9a2d2d;
  font-weight: 700;
}

.skeleton-list,
.video-list,
.recommend-list {
  margin-top: 12px;
  display: grid;
  gap: 10px;
}

.skeleton-item {
  height: 54px;
  border-radius: 12px;
  background: linear-gradient(90deg, #edf3f0, #e3efe9, #edf3f0);
  background-size: 220% 100%;
  animation: shimmer 1.2s linear infinite;
}

.skeleton-item--tall {
  height: 132px;
}

.video-item {
  width: 100%;
  border: 1px solid rgba(32, 42, 55, 0.08);
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff, #f9fbfd);
  padding: 10px 12px;
  text-align: left;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.video-item__info {
  min-width: 0;
}

.video-item__title,
.recommend-item__title {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: #1f2a37;
  overflow-wrap: anywhere;
}

.video-item__status {
  margin-top: 5px;
  display: inline-block;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 700;
}

.status--ok {
  color: #157b4f;
  background: rgba(55, 174, 115, 0.14);
}

.status--warn {
  color: #8f5419;
  background: rgba(242, 154, 74, 0.14);
}

.status--bad {
  color: #9f3535;
  background: rgba(223, 82, 82, 0.14);
}

.status--info {
  color: #1f6a62;
  background: rgba(76, 173, 195, 0.14);
}

.video-item__arrow {
  color: #9bb0ae;
  font-size: 22px;
  line-height: 1;
}

.recommend-item {
  width: 100%;
  border: 1px solid rgba(32, 42, 55, 0.08);
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff, #f9fbfd);
  padding: 14px;
  text-align: left;
  display: grid;
  gap: 8px;
}

.recommend-item__reason {
  background: rgba(31, 122, 140, 0.12);
  color: var(--primary-deep);
}

.recommend-item__meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

@keyframes shimmer {
  from {
    background-position: 0% 0;
  }

  to {
    background-position: 220% 0;
  }
}

@keyframes rise-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 390px) {
  .quick-grid,
  .stats {
    grid-template-columns: 1fr;
  }

  .welcome__top {
    align-items: flex-start;
  }

  .welcome__brand {
    min-width: 120px;
  }

  .guide-btn {
    margin-left: auto;
  }

  .welcome__title {
    font-size: 24px;
  }
}
</style>
