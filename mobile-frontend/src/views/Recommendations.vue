<template>
  <div class="ios-page recommendations-page">
    <header class="hero ios-card">
      <div class="hero__copy">
        <p class="hero__eyebrow">Recommendation Hub</p>
        <h1 class="hero__title">推荐学习中枢</h1>
        <p class="hero__desc">先看站内主题，再扩到相近内容，最后把站外候选送回导入链路，让推荐动作本身也保持清晰和克制。</p>
      </div>
      <div class="hero__actions">
        <button type="button" class="hero-btn hero-btn--ghost" @click="go('/upload')">去上传</button>
        <button type="button" class="hero-btn hero-btn--primary" @click="reloadAll" :disabled="pageLoading">
          {{ pageLoading ? '刷新中…' : '刷新推荐' }}
        </button>
      </div>
      <div class="hero__stats">
        <div class="hero-stat"><span>场景</span><strong>{{ displayScenes.length }}</strong></div>
        <div class="hero-stat"><span>主题</span><strong>{{ tagClusters.length }}</strong></div>
        <div class="hero-stat"><span>入口</span><strong>{{ providerShortcuts.length }}</strong></div>
      </div>
      <div class="hero__notice">
        <strong>这一页先帮你决定下一步学什么。</strong>
        <span>站内内容会直接打开详情，站外候选只做元数据推荐，点击后会带着链接进入导入学习链路。</span>
      </div>
    </header>

    <section class="panel panel--compact ios-card">
      <div class="section-head">
        <div>
          <h2>推荐路线</h2>
          <p>先看当前场景，再按标签收窄，最后把站外候选导回学习系统，避免推荐和学习流程脱节。</p>
        </div>
      </div>
      <div class="journey-grid">
        <article class="journey-card">
          <span class="journey-card__step">01</span>
          <strong class="journey-card__title">选当前场景</strong>
          <span class="journey-card__desc">先决定是继续学习、复盘，还是围绕某条内容扩相关推荐。</span>
        </article>
        <article class="journey-card">
          <span class="journey-card__step">02</span>
          <strong class="journey-card__title">收窄主题</strong>
          <span class="journey-card__desc">用标签把当前推荐范围收紧，避免在多个主题之间反复跳。</span>
        </article>
        <article class="journey-card">
          <span class="journey-card__step">03</span>
          <strong class="journey-card__title">导入站外候选</strong>
          <span class="journey-card__desc">看准站外内容后直接导入，不把它误当成已入库视频。</span>
        </article>
      </div>
    </section>

    <section class="panel ios-card">
      <div class="section-head">
        <div>
          <h2>推荐场景</h2>
          <p>先切学习阶段，再看当前推荐卡片和同主题扩展。</p>
        </div>
        <span class="pill">{{ activeSceneOption.label }}</span>
      </div>
      <div v-if="pageError" class="message message--error">
        <span>{{ pageError }}</span>
        <button type="button" class="panel-link" @click="reloadAll">重试</button>
      </div>
      <div class="scene-tabs">
        <button
          v-for="scene in displayScenes"
          :key="scene.value"
          type="button"
          class="scene-tab"
          :class="{ 'scene-tab--active': activeScene === scene.value }"
          @click="activateScene(scene.value)"
        >
          <span class="scene-tab__label">{{ scene.label }}</span>
          <span class="scene-tab__desc">{{ scene.description }}</span>
        </button>
      </div>
      <div v-if="activeExternalFetchBanner" class="message message--warn">
        <span>{{ activeExternalFetchBanner }}</span>
      </div>
    </section>

    <section class="panel ios-card">
      <div class="section-head">
        <div>
          <h2>标签主题</h2>
          <p>先把当前推荐里已经浮现的学习主题收口，后续站外候选也会落在这里。</p>
        </div>
        <button v-if="selectedTag" type="button" class="panel-link" @click="selectedTag = ''">清除筛选</button>
      </div>
      <div v-if="tagClusters.length === 0" class="message">当前推荐里还没有足够的标签信号。</div>
      <div v-else class="tag-grid">
        <button
          v-for="tag in tagClusters"
          :key="tag.name"
          type="button"
          class="tag-card"
          :class="{ 'tag-card--active': selectedTag === tag.name }"
          @click="toggleTag(tag.name)"
        >
          <span class="tag-card__name">{{ tag.name }}</span>
          <strong class="tag-card__count">{{ tag.count }}</strong>
          <span class="tag-card__sample">{{ tag.sample }}</span>
        </button>
      </div>
    </section>

    <section class="panel panel--compact ios-card">
      <div class="section-head">
        <div>
          <h2>当前推荐上下文</h2>
          <p>切场景、筛主题和扩展相关推荐前，先确认你现在正在看的推荐范围。</p>
        </div>
        <span class="pill">{{ filteredSceneCountLabel }}</span>
      </div>
      <div class="context-grid">
        <article class="context-card">
          <span class="context-card__label">当前场景</span>
          <strong class="context-card__value">{{ activeSceneOption.label }}</strong>
          <span class="context-card__desc">{{ selectedTagSummary }}</span>
        </article>
        <article class="context-card">
          <span class="context-card__label">相关推荐种子</span>
          <strong class="context-card__value">{{ relatedSeed ? '已选种子' : '等待选择' }}</strong>
          <span class="context-card__desc">{{ relatedSeedSummary }}</span>
        </article>
        <article class="context-card">
          <span class="context-card__label">结果构成</span>
          <strong class="context-card__value">{{ filteredSceneCountLabel }}</strong>
          <span class="context-card__desc">{{ sceneMixSummary }}</span>
        </article>
      </div>
      <div class="context-actions">
        <button
          v-if="selectedTag"
          type="button"
          class="context-action"
          @click="selectedTag = ''"
        >
          清除主题
        </button>
        <button
          v-if="relatedSeed"
          type="button"
          class="context-action"
          @click="clearRelated"
        >
          清除相关推荐
        </button>
        <button type="button" class="context-action context-action--primary" @click="go('/upload')">导入新链接</button>
      </div>
    </section>

    <section class="panel panel--compact ios-card">
      <div class="section-head">
        <div>
          <h2>来源总览</h2>
          <p>先确认这一屏推荐主要来自哪里，再决定是继续看站内内容还是导入站外候选。</p>
        </div>
      </div>
      <div class="source-grid">
        <article class="source-card">
          <span class="source-card__label">站内内容</span>
          <strong class="source-card__value">{{ internalItemCount }}</strong>
          <span class="source-card__desc">已进入视频库，可直接打开详情继续学习。</span>
        </article>
        <article class="source-card source-card--soft">
          <span class="source-card__label">站外候选</span>
          <strong class="source-card__value">{{ externalItems.length }}</strong>
          <span class="source-card__desc">点击后会带着链接进入导入学习链路。</span>
        </article>
        <article class="source-card">
          <span class="source-card__label">来源平台</span>
          <strong class="source-card__value">{{ externalSourceCount }}</strong>
          <span class="source-card__desc">{{ externalSourceSummary }}</span>
        </article>
      </div>
      <div v-if="activeExternalQuerySummary" class="message message--hint">
        本轮站外检索围绕：{{ activeExternalQuerySummary }}
      </div>
      <div v-if="activeProviderReports.length > 0" class="provider-status-list">
        <article
          v-for="provider in activeProviderReports"
          :key="`${activeScene}-${provider.provider}`"
          class="provider-status-card"
          :class="{
            'provider-status-card--failed': provider.status === 'failed',
            'provider-status-card--empty': provider.status === 'empty'
          }"
        >
          <div class="provider-status-card__top">
            <strong>{{ provider.source_label }}</strong>
            <span>{{ providerStatusText(provider) }}</span>
          </div>
          <p>{{ providerStatusDetail(provider) }}</p>
        </article>
      </div>
    </section>

    <section class="panel ios-card">
      <div class="section-head">
        <div>
          <h2>{{ activeSceneOption.label }}</h2>
          <p>{{ sceneDescriptionText }}</p>
        </div>
        <button type="button" class="panel-link" @click="refreshActiveScene" :disabled="activeSceneLoading">
          {{ activeSceneLoading ? '刷新中…' : '刷新本场景' }}
        </button>
      </div>
      <div v-if="filteredSceneExternalCount > 0" class="message message--hint">
        当前场景里已混入 {{ filteredSceneExternalCount }} 条站外候选，点击后会先进入导入学习，不会直接当作站内视频播放。
      </div>
      <div v-if="activeSceneError" class="message message--error">
        <span>{{ activeSceneError }}</span>
        <button type="button" class="panel-link" @click="refreshActiveScene">重试</button>
      </div>
      <div v-else-if="activeSceneLoading && filteredSceneItems.length === 0" class="skeleton-list">
        <div v-for="index in 3" :key="`scene-skeleton-${index}`" class="skeleton-card"></div>
      </div>
      <div v-else-if="filteredSceneItems.length === 0" class="message">
        {{ selectedTag ? `当前场景下暂时没有命中“${selectedTag}”的推荐。` : '当前场景还没有可展示的推荐项。' }}
      </div>
      <div v-else class="card-list">
        <article v-for="item in filteredSceneItems" :key="item.key" class="recommend-card">
          <div class="recommend-card__top">
            <span class="badge badge--reason">{{ item.reasonLabel }}</span>
            <span class="badge" :class="item.sourceBadgeClass">{{ item.sourceLabel }}</span>
          </div>
          <h3 class="recommend-card__title">{{ item.title }}</h3>
          <p class="recommend-card__desc">{{ item.summaryText }}</p>
          <div v-if="item.tags.length > 0" class="mini-tags">
            <button
              v-for="tag in item.tags.slice(0, 4)"
              :key="`${item.key}-${tag}`"
              type="button"
              class="mini-tag"
              @click="toggleTag(tag)"
            >
              {{ tag }}
            </button>
          </div>
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
            <button
              type="button"
              class="action-btn"
              :class="{ 'action-btn--active': item.isRelatedSeed }"
              @click.stop="loadRelatedByItem(item)"
              :disabled="!item.canLoadRelated || item.relatedButtonLoading"
            >
              {{ item.relatedButtonLabel }}
            </button>
          </div>
        </article>
      </div>
    </section>

    <section ref="relatedSectionRef" class="panel ios-card">
      <div class="section-head">
        <div>
          <h2>相关推荐</h2>
          <p>从当前视频继续扩展同主题内容，后续站外候选也会优先沿用这个区域。</p>
        </div>
        <button v-if="relatedSeed" type="button" class="panel-link" @click="clearRelated">清除</button>
      </div>
      <div v-if="!relatedSeed" class="message">先在上面的卡片里点一次“看同主题”，这里就会加载相关推荐。</div>
      <template v-else>
        <div class="seed-card">
          <span class="seed-card__label">当前种子视频</span>
          <strong class="seed-card__title">{{ relatedSeed.title }}</strong>
          <span class="seed-card__meta">{{ relatedSeed.reasonLabel }}</span>
        </div>
        <div v-if="relatedStatusMessage" class="message message--hint">
          {{ relatedStatusMessage }}
        </div>
        <div v-if="!relatedLoading && !relatedError && relatedExternalFetchFailed" class="message message--warn">
          部分站外来源未返回结果，站内相关推荐仍可使用。可检查网络后重试，或通过环境变量关闭默认站外拉取。
        </div>
        <div v-if="relatedLoading" class="skeleton-list">
          <div v-for="index in 2" :key="`related-skeleton-${index}`" class="skeleton-card skeleton-card--short"></div>
        </div>
        <div v-else-if="relatedError" class="message message--error">
          <span>{{ relatedError }}</span>
          <button type="button" class="panel-link" @click="reloadRelated">重试</button>
        </div>
        <div v-else-if="filteredRelatedItems.length === 0" class="message">
          {{ selectedTag ? `相关推荐里暂时没有命中“${selectedTag}”的内容。` : '当前还没有可展示的相关推荐。' }}
        </div>
        <div v-else class="card-list">
          <article v-for="item in filteredRelatedItems" :key="item.key" class="related-card">
            <div class="related-card__copy">
              <span class="badge badge--reason">{{ item.reasonLabel }}</span>
              <strong class="related-card__title">{{ item.title }}</strong>
              <p class="related-card__desc">{{ item.summaryText }}</p>
            </div>
            <button type="button" class="action-btn action-btn--primary" @click="openRecommendation(item)">
              {{ item.primaryActionLabel }}
            </button>
          </article>
        </div>
      </template>
    </section>

    <section class="panel ios-card">
      <div class="section-head">
        <div>
          <h2>站外候选入口</h2>
          <p>这里不是直接播放区，而是把外部内容清晰地带回现有导入学习链路。</p>
        </div>
      </div>
      <div class="message message--hint">
        站外候选只展示推荐元数据。点“导入学习”后，会把链接带到上传页，再走现有下载、处理和复盘流程。
      </div>
      <div v-if="externalItems.length > 0" class="card-list">
        <article v-for="item in externalItems" :key="item.key" class="external-card">
          <div class="recommend-card__top">
            <span class="badge badge--external">{{ item.sourceLabel }}</span>
            <span class="badge badge--reason">{{ item.reasonLabel }}</span>
          </div>
          <strong class="related-card__title">{{ item.title }}</strong>
          <p class="related-card__desc">{{ item.summaryText }}</p>
          <div v-if="item.tags.length > 0" class="mini-tags">
            <span v-for="tag in item.tags.slice(0, 3)" :key="`${item.key}-external-${tag}`" class="mini-tag">{{ tag }}</span>
          </div>
          <div class="recommend-card__meta">
            <span>{{ item.sourceLabel }}</span>
            <span v-if="item.timeText">{{ item.timeText }}</span>
            <span v-if="item.subjectText">{{ item.subjectText }}</span>
          </div>
          <div v-if="item.importHint" class="recommend-card__hint">{{ item.importHint }}</div>
          <button
            type="button"
            class="action-btn action-btn--primary"
            :disabled="item.primaryActionDisabled"
            @click="openRecommendation(item)"
          >
            {{ item.primaryActionLabel }}
          </button>
        </article>
      </div>
      <div v-else class="provider-grid">
        <button
          v-for="provider in providerShortcuts"
          :key="provider.value"
          type="button"
          class="provider-card"
          @click="openProviderUpload(provider)"
        >
          <span class="provider-card__name">{{ provider.label }}</span>
          <span class="provider-card__desc">{{ provider.description }}</span>
          <span class="provider-card__cta">去导入</span>
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getRecommendationScenes, getVideoRecommendations } from '@/api/recommendation'
import { shouldIncludeExternalRecommendationsByDefault } from '@/config'
import {
  isRecommendationPrimaryActionDisabled,
  parseRecommendationActionTarget,
  resolveRecommendationUrl,
  shouldOpenRecommendationExternalSource
} from '@/services/recommendationActions'
import { videoStatusText } from '@/services/videoStatus'

const FALLBACK_SCENES = [
  { value: 'home', label: '首页推荐', description: '适合首页首屏，优先返回当前最值得继续处理或复盘的内容。', requires_seed: false },
  { value: 'continue', label: '继续学习', description: '优先返回处理中、失败待补跑和最近进入的视频。', requires_seed: false },
  { value: 'review', label: '复盘推荐', description: '优先返回已完成且更适合整理笔记的视频。', requires_seed: false }
]

const providerShortcuts = [
  { value: 'bilibili', label: 'B站', description: '把课程或知识区链接直接送进现有导入链路。' },
  { value: 'youtube', label: 'YouTube', description: '适合导入英文课程、公开讲座和频道内容。' },
  { value: 'mooc', label: '中国大学慕课', description: '把课程页链接直接交给后端下载与处理。' }
]

const router = useRouter()
const pageLoading = ref(false)
const pageError = ref('')
const scenes = ref([])
const activeScene = ref('home')
const selectedTag = ref('')
const sceneItemsMap = ref({})
const sceneMetaMap = ref({})
const sceneErrorMap = ref({})
const sceneLoadingMap = ref({})
const relatedSeed = ref(null)
const relatedItems = ref([])
const relatedLoading = ref(false)
const relatedError = ref('')
const relatedExternalFetchFailed = ref(false)
const relatedStatusMode = ref('')
const relatedLoadingItemKey = ref('')
const relatedSectionRef = ref(null)

const go = (path) => router.push(path)
const normalizeSceneOptions = (payload) => Array.isArray(payload?.scenes) ? payload.scenes : Array.isArray(payload?.data?.scenes) ? payload.data.scenes : []
const normalizeRecommendationItems = (payload) => Array.isArray(payload?.items) ? payload.items : Array.isArray(payload?.data?.items) ? payload.data.items : []
const normalizeRecommendationSources = (payload) => Array.isArray(payload?.sources) ? payload.sources : Array.isArray(payload?.data?.sources) ? payload.data.sources : []
const normalizeExternalProviders = (payload) => Array.isArray(payload?.external_providers) ? payload.external_providers : Array.isArray(payload?.data?.external_providers) ? payload.data.external_providers : []
const normalizeExternalQuery = (payload) => payload?.external_query || payload?.data?.external_query || null
const normalizeRecommendationCount = (payload, key) => {
  const value = payload?.[key] ?? payload?.data?.[key] ?? 0
  const numeric = Number(value)
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
  externalProviders: normalizeExternalProviders(payload),
  externalQuery: normalizeExternalQuery(payload),
  internalItemCount: normalizeRecommendationCount(payload, 'internal_item_count'),
  externalItemCount: normalizeRecommendationCount(payload, 'external_item_count'),
  externalFailedProviderCount: normalizeRecommendationCount(payload, 'external_failed_provider_count'),
  externalFetchFailed: Boolean(payload?.external_fetch_failed ?? payload?.data?.external_fetch_failed ?? false)
})

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
  const tags = Array.isArray(item?.tags) ? item.tags.filter(Boolean).map((tag) => String(tag).trim()) : []
  const sourceLabel = resolveSourceLabel(item)
  const isExternal = isExternalItem(item)
  const actionLabel = String(item?.action_label || '').trim()
  const importHint = String(item?.import_hint || '').trim()
  const subjectText = String(item?.subject || '').trim()
  return {
    ...item,
    key: resolveItemKey(item, index),
    title: String(item?.title || '未命名内容'),
    tags,
    reasonLabel: String(item?.reason_label || '推荐'),
    summaryText: String(item?.reason_text || item?.summary || '从这里继续进入学习链路。'),
    statusText: item?.status ? videoStatusText(item.status) : '',
    timeText: formatTimeText(item?.upload_time || item?.updated_at || item?.created_at),
    sourceLabel,
    sourceBadgeClass: isExternal ? 'badge--external' : item?.processing_origin === 'ios_offline' ? 'badge--mint' : 'badge--soft',
    primaryActionLabel: actionLabel || (isExternal ? '导入学习' : item?.processing_origin === 'ios_offline' ? '打开本地结果' : '打开详情'),
    primaryActionDisabled: isRecommendationPrimaryActionDisabled(item, isExternal),
    canLoadRelated: !isExternal && Boolean(item?.id),
    canImport: Boolean(item?.can_import ?? false),
    importHint,
    actionTarget: String(item?.action_target || '').trim(),
    actionApi: String(item?.action_api || '').trim(),
    actionMethod: String(item?.action_method || '').trim().toUpperCase(),
    subjectText: subjectText ? `科目 · ${subjectText}` : '',
    clusterKey: String(item?.cluster_key || '').trim(),
    isRelatedSeed: resolveItemKey(item, index) === relatedLoadingItemKey.value || resolveItemKey(item, index) === relatedSeed.value?.key,
    relatedButtonLoading: resolveItemKey(item, index) === relatedLoadingItemKey.value && relatedLoading.value,
    relatedButtonLabel:
      resolveItemKey(item, index) === relatedLoadingItemKey.value && relatedLoading.value
        ? '加载中…'
        : resolveItemKey(item, index) === relatedSeed.value?.key
          ? '已显示同主题'
          : '看同主题'
  }
}

const displayScenes = computed(() => {
  const options = scenes.value.filter((scene) => !scene?.requires_seed)
  return options.length > 0 ? options : FALLBACK_SCENES
})

const activeSceneOption = computed(
  () => displayScenes.value.find((scene) => scene.value === activeScene.value) || displayScenes.value[0] || FALLBACK_SCENES[0]
)

const activeSceneItems = computed(() => (sceneItemsMap.value[activeScene.value] || []).map((item, index) => decorateItem(item, index)))

const allLoadedItems = computed(() => {
  const map = new Map()
  displayScenes.value.forEach((scene) => {
    ;(sceneItemsMap.value[scene.value] || []).forEach((item, index) => {
      const decorated = decorateItem(item, index)
      map.set(decorated.key, decorated)
    })
  })
  relatedItems.value.forEach((item, index) => {
    const decorated = decorateItem(item, index)
    map.set(decorated.key, decorated)
  })
  return Array.from(map.values())
})

const tagClusters = computed(() => {
  const bucket = new Map()
  allLoadedItems.value.forEach((item) => {
    item.tags.forEach((tag) => {
      const current = bucket.get(tag) || { name: tag, count: 0, titles: [] }
      current.count += 1
      if (current.titles.length < 2) current.titles.push(item.title)
      bucket.set(tag, current)
    })
  })
  return Array.from(bucket.values())
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
    .slice(0, 10)
    .map((item) => ({ ...item, sample: item.titles.join(' / ') }))
})

const filteredSceneItems = computed(() => !selectedTag.value ? activeSceneItems.value : activeSceneItems.value.filter((item) => item.tags.includes(selectedTag.value)))
const filteredRelatedItems = computed(() => {
  const items = relatedItems.value.map((item, index) => decorateItem(item, index))
  return !selectedTag.value ? items : items.filter((item) => item.tags.includes(selectedTag.value))
})
const activeSceneMeta = computed(() => sceneMetaMap.value[activeScene.value] || createRecommendationMeta())
const externalItems = computed(() => allLoadedItems.value.filter((item) => isExternalItem(item)))
const filteredSceneExternalCount = computed(() => filteredSceneItems.value.filter((item) => isExternalItem(item)).length)
const filteredSceneInternalCount = computed(() => filteredSceneItems.value.length - filteredSceneExternalCount.value)
const internalItemCount = computed(() => Math.max(allLoadedItems.value.length - externalItems.value.length, 0))
const externalSourceLabels = computed(() => Array.from(new Set(externalItems.value.map((item) => item.sourceLabel).filter(Boolean))))
const externalSourceCount = computed(() => externalSourceLabels.value.length)
const externalSourceSummary = computed(() => {
  if (externalSourceLabels.value.length === 0) return '当前还没有外部候选来源。'
  return externalSourceLabels.value.join(' / ')
})
const activeSceneLoading = computed(() => Boolean(sceneLoadingMap.value[activeScene.value]))
const activeSceneError = computed(() => String(sceneErrorMap.value[activeScene.value] || '').trim())
const sceneDescriptionText = computed(() => selectedTag.value ? `当前已按“${selectedTag.value}”筛选 ${activeSceneOption.value.label}。` : activeSceneOption.value.description)
const filteredSceneCountLabel = computed(() => `${filteredSceneItems.value.length} 条结果`)
const selectedTagSummary = computed(() => selectedTag.value ? `已按“${selectedTag.value}”收窄当前推荐。` : '当前未加主题筛选。')
const relatedSeedSummary = computed(() => {
  if (!relatedSeed.value?.title) return '点一次“看同主题”后，这里会固定当前种子。'
  return String(relatedSeed.value.title)
})
const relatedStatusMessage = computed(() => {
  if (!relatedSeed.value?.title) return ''
  if (relatedLoading.value) return `正在围绕《${relatedSeed.value.title}》加载同主题视频…`
  if (relatedStatusMode.value === 'local') return `已显示《${relatedSeed.value.title}》的同主题推荐；当前使用的是本地兜底结果。`
  if (filteredRelatedItems.value.length > 0) return `已为《${relatedSeed.value.title}》加载 ${filteredRelatedItems.value.length} 条同主题推荐。`
  return ''
})
const sceneMixSummary = computed(() => {
  if (filteredSceneItems.value.length === 0) return '等待当前场景返回推荐结果。'
  if (filteredSceneExternalCount.value === 0) return `当前结果以 ${filteredSceneInternalCount.value} 条站内内容为主。`
  if (filteredSceneInternalCount.value === 0) return `当前结果以 ${filteredSceneExternalCount.value} 条站外候选为主。`
  return `站内 ${filteredSceneInternalCount.value} 条，站外 ${filteredSceneExternalCount.value} 条。`
})
const activeProviderReports = computed(() => activeSceneMeta.value.externalProviders || [])
const activeExternalQuerySummary = computed(() => {
  const query = activeSceneMeta.value.externalQuery
  if (!query) return ''
  const parts = [query.subject, query.primary_topic].filter(Boolean)
  const tagText = Array.isArray(query.preferred_tags) && query.preferred_tags.length > 0 ? `优先标签：${query.preferred_tags.join('、')}` : ''
  if (tagText) parts.push(tagText)
  return parts.join(' · ')
})

const setSceneLoading = (scene, value) => { sceneLoadingMap.value = { ...sceneLoadingMap.value, [scene]: value } }
const setSceneError = (scene, value) => { sceneErrorMap.value = { ...sceneErrorMap.value, [scene]: value } }
const setSceneItems = (scene, items) => { sceneItemsMap.value = { ...sceneItemsMap.value, [scene]: items } }
const setSceneMeta = (scene, payload) => { sceneMetaMap.value = { ...sceneMetaMap.value, [scene]: buildRecommendationMeta(payload) } }
const toggleTag = (tag) => { selectedTag.value = selectedTag.value === tag ? '' : tag }
const providerStatusText = (provider) => {
  if (provider?.status === 'failed') return '抓取失败'
  if (provider?.status === 'empty') return '暂无候选'
  return `${Number(provider?.candidate_count || 0)} 条候选`
}
const activeExternalFetchBanner = computed(() => {
  if (!activeSceneMeta.value.externalFetchFailed) return ''
  return '部分站外来源未返回结果，站内推荐仍可使用。可检查网络后刷新，或通过环境变量 VITE_RECOMMENDATION_INCLUDE_EXTERNAL 控制是否默认拉取站外。'
})

const providerStatusDetail = (provider) => {
  if (provider?.status === 'failed')
    return String(provider?.error_message || '当前来源抓取失败，请检查网络或稍后刷新。')
  if (provider?.status === 'empty') return `当前已检索，但没有返回可用候选。耗时 ${Number(provider?.latency_ms || 0)} ms`
  return `本轮抓取耗时 ${Number(provider?.latency_ms || 0)} ms，可继续导入该来源内容。`
}

const scoreRelatedFallbackCandidate = (seedItem, candidate) => {
  if (!seedItem || !candidate || !candidate.id || candidate.id === seedItem.id) return -1
  if (isExternalItem(candidate)) return -1
  let score = 0
  const seedTags = new Set(seedItem.tags || [])
  const candidateTags = Array.isArray(candidate.tags) ? candidate.tags : []
  candidateTags.forEach((tag) => {
    if (seedTags.has(tag)) score += 6
  })
  if (seedItem.clusterKey && candidate.clusterKey && seedItem.clusterKey === candidate.clusterKey) score += 10
  if (seedItem.subjectText && candidate.subjectText && seedItem.subjectText === candidate.subjectText) score += 4
  if (score <= 0) return -1
  return score
}

const buildFallbackRelatedItems = (seedItem) => {
  return allLoadedItems.value
    .map((candidate) => ({ candidate, score: scoreRelatedFallbackCandidate(seedItem, candidate) }))
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 4)
    .map((entry) => entry.candidate)
}

const scrollToRelatedSection = async () => {
  await nextTick()
  relatedSectionRef.value?.scrollIntoView?.({ behavior: 'smooth', block: 'start' })
}

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

const loadScene = async (scene, { force = false } = {}) => {
  if (!force && (sceneItemsMap.value[scene] || []).length > 0) return sceneItemsMap.value[scene]
  setSceneLoading(scene, true)
  setSceneError(scene, '')
  try {
    const res = await getVideoRecommendations({
      scene,
      limit: 6,
      include_external: shouldIncludeExternalRecommendationsByDefault()
    })
    const payload = res?.data || {}
    const items = normalizeRecommendationItems(payload)
    setSceneItems(scene, items)
    setSceneMeta(scene, payload)
    return items
  } catch (error) {
    setSceneError(scene, error?.message || `${scene} 场景加载失败`)
    setSceneItems(scene, [])
    setSceneMeta(scene, createRecommendationMeta())
    return []
  } finally {
    setSceneLoading(scene, false)
  }
}

const activateScene = async (scene) => {
  activeScene.value = scene
  if ((sceneItemsMap.value[scene] || []).length === 0) await loadScene(scene)
}

const loadRelatedByItem = async (item) => {
  if (!item?.id || isExternalItem(item)) return
  relatedSeed.value = item
  relatedLoading.value = true
  relatedError.value = ''
  relatedStatusMode.value = 'api'
  relatedLoadingItemKey.value = item.key || String(item.id)
  await scrollToRelatedSection()
  try {
    const res = await getVideoRecommendations({
      scene: 'related',
      seed_video_id: item.id,
      limit: 4,
      include_external: shouldIncludeExternalRecommendationsByDefault()
    })
    const payload = res?.data || {}
    relatedExternalFetchFailed.value = Boolean(payload?.external_fetch_failed)
    const apiItems = normalizeRecommendationItems(payload)
    if (apiItems.length > 0) {
      relatedItems.value = apiItems
      relatedStatusMode.value = 'api'
    } else {
      relatedItems.value = buildFallbackRelatedItems(item)
      relatedStatusMode.value = relatedItems.value.length > 0 ? 'local' : 'api'
    }
  } catch (error) {
    relatedItems.value = buildFallbackRelatedItems(item)
    relatedExternalFetchFailed.value = false
    relatedStatusMode.value = relatedItems.value.length > 0 ? 'local' : 'error'
    relatedError.value = relatedItems.value.length > 0 ? '' : error?.message || '相关推荐加载失败'
  } finally {
    relatedLoading.value = false
    relatedLoadingItemKey.value = ''
  }
}

const reloadRelated = async () => {
  if (relatedSeed.value?.id) await loadRelatedByItem(relatedSeed.value)
}

const clearRelated = () => {
  relatedSeed.value = null
  relatedItems.value = []
  relatedError.value = ''
  relatedExternalFetchFailed.value = false
  relatedStatusMode.value = ''
  relatedLoadingItemKey.value = ''
}

const refreshActiveScene = async () => { await loadScene(activeScene.value, { force: true }) }
const openProviderUpload = (provider) => router.push({ path: '/upload', query: { mode: 'url', source: provider.label } })

const reloadAll = async () => {
  pageLoading.value = true
  pageError.value = ''
  try {
    const sceneRes = await getRecommendationScenes()
    const loadedScenes = normalizeSceneOptions(sceneRes?.data || {})
    scenes.value = loadedScenes.length > 0 ? loadedScenes : FALLBACK_SCENES
    const baseScenes = (scenes.value.length > 0 ? scenes.value : FALLBACK_SCENES).filter((scene) => !scene.requires_seed)
    const results = await Promise.all(baseScenes.map((scene) => loadScene(scene.value, { force: true })))
    const seedSource = results.flat().find((item) => item?.id)
    if (seedSource?.id) await loadRelatedByItem(decorateItem(seedSource))
    else clearRelated()
  } catch (error) {
    pageError.value = error?.message || '推荐页面加载失败'
    scenes.value = FALLBACK_SCENES
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

.panel--compact {
  gap: 14px;
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
.hero__actions,
.hero__stats,
.hero__notice {
  position: relative;
  z-index: 1;
}

.hero__eyebrow,
.badge,
.pill,
.mini-tag {
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
.pill,
.mini-tag {
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
.recommend-card__desc,
.recommend-card__meta,
.message,
.tag-card__sample,
.provider-card__desc,
.related-card__desc,
.seed-card__meta,
.context-card__desc,
.journey-card__desc,
.source-card__desc {
  color: #706781;
}

.hero__desc {
  margin-top: 10px;
  font-size: 14px;
  line-height: 1.65;
  max-width: 32rem;
}

.hero__actions,
.hero__stats,
.scene-tabs,
.tag-grid,
.card-list,
.provider-grid,
.skeleton-list,
.context-grid,
.journey-grid,
.source-grid {
  display: grid;
  gap: 12px;
}

.hero__actions,
.hero__stats,
.provider-grid,
.context-grid,
.journey-grid,
.source-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.hero__actions {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.scene-tabs {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.hero-btn,
.scene-tab,
.tag-card,
.recommend-card,
.related-card,
.external-card,
.provider-card,
.action-btn,
.context-action {
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(247, 241, 251, 0.96);
}

.hero-btn,
.action-btn,
.context-action {
  border-radius: 16px;
  padding: 13px 14px;
  font-size: 13px;
  font-weight: 800;
}

.hero-btn--primary,
.action-btn--primary,
.context-action--primary {
  border: 0;
  color: #f9fafb;
  background: linear-gradient(135deg, #5f477e, #8f73ba);
  box-shadow: 0 16px 24px rgba(95, 71, 126, 0.24);
}

.action-btn--active {
  border-color: rgba(143, 115, 186, 0.42);
  background: rgba(232, 221, 244, 0.98);
  color: var(--primary-deep);
}

.hero-btn--ghost,
.panel-link,
.provider-card__cta,
.context-action {
  color: var(--primary-deep);
}

.hero-btn--ghost {
  background: rgba(242, 235, 248, 0.94);
}

.hero-stat,
.seed-card,
.context-card,
.journey-card,
.source-card {
  display: grid;
  gap: 6px;
  border-radius: 20px;
  padding: 15px;
  background: rgba(238, 230, 246, 0.92);
  border: 1px solid rgba(17, 24, 39, 0.08);
}

.hero-stat span,
.seed-card__label,
.context-card__label,
.source-card__label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #706781;
}

.hero-stat strong,
.seed-card__title,
.context-card__value,
.source-card__value {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: #221a30;
}

.context-card__value {
  font-size: 18px;
  line-height: 1.25;
}

.context-card__desc {
  font-size: 12px;
  line-height: 1.6;
}

.hero__notice {
  display: grid;
  gap: 4px;
  padding: 14px 15px;
  border-radius: 20px;
  background: rgba(234, 224, 244, 0.92);
  border: 1px solid rgba(17, 24, 39, 0.08);
  font-size: 12px;
  line-height: 1.6;
  color: #706781;
}

.hero__notice strong {
  color: #221a30;
  font-size: 13px;
}

.journey-card__step {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 999px;
  background: var(--primary-soft);
  color: var(--primary-deep);
  font-size: 11px;
  font-weight: 800;
}

.journey-card__title {
  font-size: 15px;
  font-weight: 800;
  color: #221a30;
}

.journey-card__desc,
.source-card__desc {
  font-size: 12px;
  line-height: 1.6;
}

.source-card--soft {
  background: var(--surface-lilac);
}

.context-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.context-action {
  padding-inline: 15px;
}

.section-head,
.recommend-card__top,
.recommend-card__meta,
.recommend-card__actions,
.related-card {
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

.scene-tab,
.tag-card,
.provider-card,
.recommend-card,
.external-card {
  width: 100%;
  text-align: left;
}

.scene-tab,
.tag-card,
.provider-card,
.recommend-card,
.related-card,
.external-card {
  border-radius: 20px;
  padding: 16px;
}

.scene-tab {
  display: grid;
  gap: 8px;
}

.scene-tab--active,
.tag-card--active {
  border-color: var(--primary-soft-strong);
  background: linear-gradient(180deg, rgba(232, 221, 244, 0.98), rgba(247, 241, 251, 0.98));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.scene-tab__label,
.provider-card__name,
.recommend-card__title,
.related-card__title {
  font-size: 16px;
  font-weight: 800;
  line-height: 1.35;
  color: #221a30;
}

.scene-tab__desc,
.provider-card__desc,
.related-card__desc,
.recommend-card__desc,
.tag-card__sample {
  font-size: 12px;
  line-height: 1.6;
}

.tag-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.tag-card {
  display: grid;
  gap: 4px;
}

.tag-card__name {
  font-size: 14px;
  font-weight: 800;
  color: #221a30;
}

.tag-card__count {
  font-size: 21px;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--primary-deep);
}

.recommend-card,
.external-card {
  display: grid;
  gap: 10px;
}

.mini-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
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

.related-card__copy {
  display: grid;
  gap: 6px;
}

.provider-status-list {
  display: grid;
  gap: 10px;
}

.provider-status-card {
  display: grid;
  gap: 6px;
  border-radius: 18px;
  padding: 14px 16px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(247, 241, 251, 0.94);
}

.provider-status-card--failed {
  border-color: rgba(139, 121, 157, 0.18);
  background: var(--lilac-bg);
}

.provider-status-card--empty {
  background: rgba(236, 227, 246, 0.84);
}

.provider-status-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  color: #221a30;
}

.provider-status-card__top span,
.provider-status-card p {
  font-size: 12px;
  line-height: 1.6;
  color: #706781;
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

.skeleton-card--short {
  height: 100px;
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

  .hero__actions,
  .hero__stats,
  .scene-tabs,
  .tag-grid,
  .provider-grid,
  .context-grid,
  .journey-grid,
  .source-grid {
    grid-template-columns: 1fr;
  }

  .hero__title {
    font-size: 30px;
  }
}
</style>
