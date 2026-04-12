<template>
  <div class="ios-page recommendations-page" role="main" aria-label="推荐学习中枢">
    <header class="hero ios-card">
      <div class="hero__copy">
        <p class="hero__eyebrow">Recommendation Hub</p>
        <h1 class="hero__title">推荐学习中枢</h1>
        <p class="hero__desc">打开即可看到可学习的视频推荐。登录后，站外链接会先写入你的视频库再展示，确保能继续完整视频处理链路。</p>
      </div>
      <ol class="hero__flow" aria-label="推荐使用步骤">
        <li>看推荐列表</li>
        <li>点卡片直接进入详情或导入学习</li>
        <li>在详情页继续完整处理链路</li>
      </ol>
      <div class="hero__actions">
        <button type="button" class="hero-btn hero-btn--ghost" @click="go('/upload')">去上传</button>
        <button type="button" class="hero-btn hero-btn--primary" @click="reloadAll" :disabled="pageLoading">
          {{ pageLoading ? '刷新中…' : '刷新推荐' }}
        </button>
      </div>
    </header>

    <section class="panel ios-card">
      <div class="section-head">
        <div>
          <h2>推荐视频</h2>
          <p>仅展示可直接打开或继续导入处理的视频卡片。</p>
        </div>
        <button type="button" class="panel-link" @click="reloadAll" :disabled="pageLoading">
          {{ pageLoading ? '刷新中…' : '刷新列表' }}
        </button>
      </div>

      <div v-if="pageError" class="message message--error" role="alert">
        <span>{{ pageError }}</span>
        <button type="button" class="panel-link" @click="reloadAll">重试</button>
      </div>

      <div v-if="externalFetchBanner" class="message message--warn">
        <span>{{ externalFetchBanner }}</span>
      </div>
      <div v-if="autoMaterializeBanner" class="message message--hint">
        <span>{{ autoMaterializeBanner }}</span>
      </div>

      <div
        v-if="pageLoading && filteredItems.length === 0"
        class="skeleton-list"
        aria-busy="true"
        aria-live="polite"
      >
        <div v-for="index in 3" :key="`scene-skeleton-${index}`" class="skeleton-card"></div>
      </div>

      <div v-else-if="filteredItems.length === 0" class="message" role="status">
        当前还没有可展示的推荐项。
      </div>

      <div v-else class="card-list">
        <article v-for="item in filteredItems" :key="item.key" class="recommend-card">
          <div class="recommend-card__top">
            <span class="badge badge--reason">{{ item.reasonLabel }}</span>
            <span class="badge" :class="item.sourceBadgeClass">{{ item.sourceLabel }}</span>
          </div>
          <h3 class="recommend-card__title">{{ item.title }}</h3>
          <div class="recommend-card__meta">
            <span v-if="item.timeText">{{ item.timeText }}</span>
            <span v-if="item.statusText">{{ item.statusText }}</span>
            <span v-if="item.subjectText">{{ item.subjectText }}</span>
          </div>
          <div v-if="item.importHint" class="recommend-card__hint">{{ item.importHint }}</div>
          <div class="recommend-card__actions">
            <button
              type="button"
              class="action-btn action-btn--primary"
              :disabled="item.primaryActionDisabled"
              @click="openRecommendation(item)"
            >
              {{ item.primaryActionLabel }}
            </button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getVideoRecommendations } from '@/api/recommendation'
import {
  isRecommendationPrimaryActionDisabled,
  parseRecommendationActionTarget,
  resolveRecommendationUrl,
  shouldOpenRecommendationExternalSource
} from '@/services/recommendationActions'
import { videoStatusText } from '@/services/videoStatus'

const router = useRouter()
const pageLoading = ref(false)
const pageError = ref('')
const items = ref([])
const meta = ref({
  externalFetchFailed: false,
  autoMaterializedExternalCount: 0,
  autoMaterializationFailedCount: 0
})

const go = (path) => router.push(path)

const RECOMMENDATION_TITLE_BLOCKLIST = ['排列组合插空法详解']

const isBlockedRecommendationTitle = (item) => {
  const title = String(item?.title || '').trim()
  if (!title) return false
  return RECOMMENDATION_TITLE_BLOCKLIST.some((keyword) => keyword && title.includes(keyword))
}

const normalizeRecommendationItems = (payload) => {
  const rows = Array.isArray(payload?.items) ? payload.items : Array.isArray(payload?.data?.items) ? payload.data.items : []
  return rows.filter((item) => !isBlockedRecommendationTitle(item))
}

const normalizeRecommendationCount = (payload, key) => {
  const value = payload?.[key] ?? payload?.data?.[key] ?? 0
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : 0
}

const formatTimeText = (rawValue) => {
  if (!rawValue) return ''
  const date = new Date(rawValue)
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleString()
}

const resolvePrimaryUrl = (item) => resolveRecommendationUrl(item)
const resolveItemKey = (item, index = 0) => String(item?.id || item?.video_id || resolvePrimaryUrl(item) || `item-${index}`)

const isExternalItem = (item) => {
  const itemType = String(item?.item_type || item?.content_type || item?.origin_type || '').trim().toLowerCase()
  if (item?.is_external === true) return true
  if (['external', 'external_candidate', 'candidate'].includes(itemType)) return true
  return !item?.id && Boolean(resolvePrimaryUrl(item))
}

const resolveSourceLabel = (item) => {
  const explicit = String(item?.source_label || item?.source_platform_label || item?.external_source_label || item?.platform_label || '').trim()
  if (explicit) return explicit
  if (isExternalItem(item)) return '站外候选'
  if (item?.processing_origin === 'ios_offline') return 'iOS 离线'
  return String(item?.upload_source_label || '站内视频')
}

const decorateItem = (item, index = 0) => {
  const sourceLabel = resolveSourceLabel(item)
  const isExternal = isExternalItem(item)
  const actionLabel = String(item?.action_label || '').trim()
  const importHint = String(item?.import_hint || '').trim()
  const subjectText = String(item?.subject || '').trim()
  return {
    ...item,
    key: resolveItemKey(item, index),
    title: String(item?.title || '未命名内容'),
    reasonLabel: String(item?.reason_label || '推荐'),
    statusText: item?.status ? videoStatusText(item.status) : '',
    timeText: formatTimeText(item?.upload_time || item?.updated_at || item?.created_at),
    sourceLabel,
    sourceBadgeClass: isExternal ? 'badge--external' : item?.processing_origin === 'ios_offline' ? 'badge--mint' : 'badge--soft',
    primaryActionLabel: actionLabel || (isExternal ? '导入学习' : item?.processing_origin === 'ios_offline' ? '打开本地结果' : '打开详情'),
    primaryActionDisabled: isRecommendationPrimaryActionDisabled(item, isExternal),
    canImport: Boolean(item?.can_import ?? false),
    importHint,
    actionTarget: String(item?.action_target || '').trim(),
    actionApi: String(item?.action_api || '').trim(),
    actionMethod: String(item?.action_method || '').trim().toUpperCase(),
    subjectText: subjectText ? `科目 · ${subjectText}` : ''
  }
}

const filteredItems = computed(() => items.value.map((item, index) => decorateItem(item, index)))

const externalFetchBanner = computed(() => {
  if (!meta.value.externalFetchFailed) return ''
  return '部分站外来源未返回结果，站内推荐仍可使用。可检查网络后刷新重试。'
})

const autoMaterializeBanner = computed(() => {
  const count = Number(meta.value.autoMaterializedExternalCount || 0)
  const failed = Number(meta.value.autoMaterializationFailedCount || 0)
  if (count > 0 && failed > 0) return `已自动入库 ${count} 条站外推荐，另有 ${failed} 条入库失败，可稍后刷新重试。`
  if (count > 0) return `已自动入库 ${count} 条站外推荐，可直接打开详情并继续视频处理链路。`
  if (failed > 0) return `本次有 ${failed} 条站外推荐自动入库失败，保留为候选链接。`
  return ''
})

const resolveRecommendationRoute = (item) => {
  const actionLocation = parseRecommendationActionTarget(item?.actionTarget || item?.action_target)
  if (actionLocation) return actionLocation
  if (isExternalItem(item) && !shouldOpenRecommendationExternalSource(item)) {
    const url = resolvePrimaryUrl(item)
    if (!url) return null
    return { path: '/upload', query: { mode: 'url', url, source: item.sourceLabel || '站外推荐' } }
  }
  if (item.processing_origin === 'ios_offline' && item.task_id) return `/local-transcripts/${item.task_id}`
  if (item.id) return `/videos/${item.id}`
  return null
}

const openRecommendation = (item) => {
  if (isExternalItem(item)) {
    if (!item.canImport && !resolvePrimaryUrl(item)) {
      pageError.value = item.importHint || '当前站外候选暂不可直接导入。'
      return
    }
  }
  const location = resolveRecommendationRoute(item)
  if (!location) {
    if (shouldOpenRecommendationExternalSource(item)) {
      const externalTarget = String(item?.actionTarget || item?.action_target || '').trim() || resolvePrimaryUrl(item)
      if (externalTarget && typeof window !== 'undefined') {
        window.location.assign(externalTarget)
        return
      }
    }
    pageError.value = '当前推荐项缺少可用的跳转动作。'
    return
  }
  router.push(location)
}

const reloadAll = async () => {
  pageLoading.value = true
  pageError.value = ''
  try {
    const res = await getVideoRecommendations({
      scene: 'home',
      limit: 8,
      include_external: true
    })
    const payload = res?.data || {}
    items.value = normalizeRecommendationItems(payload)
    meta.value = {
      externalFetchFailed: Boolean(payload?.external_fetch_failed ?? payload?.data?.external_fetch_failed ?? false),
      autoMaterializedExternalCount: normalizeRecommendationCount(payload, 'auto_materialized_external_count'),
      autoMaterializationFailedCount: normalizeRecommendationCount(payload, 'auto_materialization_failed_count')
    }
  } catch (error) {
    pageError.value = error?.message || '推荐页面加载失败'
    items.value = []
    meta.value = {
      externalFetchFailed: false,
      autoMaterializedExternalCount: 0,
      autoMaterializationFailedCount: 0
    }
  } finally {
    pageLoading.value = false
  }
}

onMounted(reloadAll)
</script>

<style scoped>
.recommendations-page {
  display: grid;
  gap: 16px;
  padding-top: calc(16px + env(safe-area-inset-top));
  font-family: 'Avenir Next', 'SF Pro Display', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.hero,
.panel {
  display: grid;
  gap: 16px;
  padding: 20px;
  border-radius: 28px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(242, 235, 248, 0.93);
  box-shadow: 0 18px 38px rgba(73, 51, 104, 0.12);
}

.hero {
  position: relative;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(242, 235, 248, 0.98), rgba(242, 235, 248, 0.95)),
    radial-gradient(circle at top right, rgba(143, 115, 186, 0.18), transparent 34%),
    radial-gradient(circle at 16% 100%, rgba(183, 157, 213, 0.14), transparent 28%);
}

.hero::after {
  content: '';
  position: absolute;
  width: 240px;
  height: 240px;
  top: -130px;
  right: -100px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(95, 71, 126, 0.08) 0%, rgba(95, 71, 126, 0.01) 64%, transparent 72%);
  pointer-events: none;
}

.hero__copy,
.hero__flow,
.hero__actions {
  position: relative;
  z-index: 1;
}

.hero__eyebrow,
.badge,
.pill {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero__eyebrow,
.badge--soft,
.pill {
  padding: 5px 10px;
  background: var(--primary-soft);
  color: var(--primary-deep);
}

.badge--reason {
  padding: 5px 10px;
  background: rgba(95, 71, 126, 0.1);
  color: #5f477e;
}

.badge--external {
  padding: 5px 10px;
  background: var(--surface-lilac-deep);
  color: var(--lilac-text);
}

.badge--mint {
  padding: 5px 10px;
  background: rgba(229, 217, 241, 0.94);
  color: var(--ok-text);
}

.hero__title {
  margin-top: 10px;
  font-size: 34px;
  line-height: 1.03;
  letter-spacing: -0.04em;
  color: #221a30;
}

.hero__desc,
.section-head p,
.recommend-card__meta,
.message {
  color: #706781;
}

.hero__desc {
  margin-top: 10px;
  font-size: 14px;
  line-height: 1.65;
  max-width: 32rem;
}

.hero__flow {
  margin: 12px 0 0;
  padding-left: 1.25rem;
  font-size: 13px;
  line-height: 1.55;
  color: #5b5268;
  max-width: 36rem;
}

.hero__flow li {
  margin-bottom: 4px;
}

.hero__actions,
.card-list,
.skeleton-list {
  display: grid;
  gap: 12px;
}

.hero__actions {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.hero-btn,
.recommend-card,
.action-btn {
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(247, 241, 251, 0.96);
}

.hero-btn,
.action-btn {
  border-radius: 16px;
  padding: 13px 14px;
  font-size: 13px;
  font-weight: 800;
}

.hero-btn--primary,
.action-btn--primary {
  border: 0;
  color: #f9fafb;
  background: linear-gradient(135deg, #5f477e, #8f73ba);
  box-shadow: 0 16px 24px rgba(95, 71, 126, 0.24);
}

.hero-btn--ghost,
.panel-link {
  color: var(--primary-deep);
}

.hero-btn--ghost {
  background: rgba(242, 235, 248, 0.94);
}

.section-head,
.recommend-card__top,
.recommend-card__meta,
.recommend-card__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.section-head h2 {
  margin: 0;
  font-size: 18px;
  letter-spacing: -0.02em;
  color: #111827;
}

.section-head p {
  margin-top: 4px;
  font-size: 13px;
  line-height: 1.6;
  max-width: 31rem;
}

.panel-link {
  border: 0;
  background: transparent;
  font-size: 13px;
  font-weight: 700;
}

.recommend-card {
  width: 100%;
  text-align: left;
  border-radius: 20px;
  padding: 16px;
  display: grid;
  gap: 10px;
}

.recommend-card__title {
  font-size: 16px;
  font-weight: 800;
  line-height: 1.35;
  color: #221a30;
}

.recommend-card__meta {
  font-size: 12px;
}

.recommend-card__hint {
  font-size: 12px;
  line-height: 1.6;
  color: var(--primary-deep);
  background: rgba(232, 221, 244, 0.76);
  border: 1px solid rgba(143, 115, 186, 0.18);
  border-radius: 16px;
  padding: 10px 12px;
}

.message {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 14px 15px;
  border-radius: 18px;
  background: rgba(238, 230, 246, 0.92);
  border: 1px dashed rgba(17, 24, 39, 0.12);
  font-size: 13px;
  line-height: 1.6;
}

.message--error {
  color: var(--lilac-text);
  background: var(--lilac-bg);
  border-style: solid;
  border-color: rgba(139, 121, 157, 0.14);
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

.skeleton-card {
  height: 132px;
  border-radius: 20px;
  background: linear-gradient(90deg, #f2ecf9, #e5daf2, #f2ecf9);
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }

  100% {
    background-position: -200% 0;
  }
}

@media (max-width: 720px) {
  .hero,
  .panel {
    padding: 18px;
  }

  .hero__actions {
    grid-template-columns: 1fr;
  }

  .hero__title {
    font-size: 30px;
  }
}
</style>
