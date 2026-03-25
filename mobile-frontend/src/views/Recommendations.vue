<template>
  <div class="ios-page recommendations-page">
    <header class="hero ios-card">
      <div class="hero__copy">
        <p class="hero__eyebrow">推荐学习</p>
        <h1 class="hero__title gradient-text">先看站内主题，再接回站外导入</h1>
        <p class="hero__desc">继续学习、复盘推荐、相关推荐和站外导入入口都收在这里，避免推荐链路散在多个页面。</p>
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
    </header>

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
          </div>
          <div class="recommend-card__actions">
            <button type="button" class="action-btn action-btn--primary" @click="openRecommendation(item)">
              {{ item.primaryActionLabel }}
            </button>
            <button type="button" class="action-btn" @click="loadRelatedByItem(item)" :disabled="!item.canLoadRelated">
              看同主题
            </button>
          </div>
        </article>
      </div>
    </section>

    <section class="panel ios-card">
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
          <p>当前先把 UI 和导入动线搭好。等后端接入 RSS / 抓取后，这里会直接展示真实外部推荐卡片。</p>
        </div>
      </div>
      <div v-if="externalItems.length > 0" class="card-list">
        <article v-for="item in externalItems" :key="item.key" class="external-card">
          <span class="badge badge--external">{{ item.sourceLabel }}</span>
          <strong class="related-card__title">{{ item.title }}</strong>
          <p class="related-card__desc">{{ item.summaryText }}</p>
          <button type="button" class="action-btn action-btn--primary" @click="openRecommendation(item)">导入学习</button>
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
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getRecommendationScenes, getVideoRecommendations } from '@/api/recommendation'
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
const sceneErrorMap = ref({})
const sceneLoadingMap = ref({})
const relatedSeed = ref(null)
const relatedItems = ref([])
const relatedLoading = ref(false)
const relatedError = ref('')

const go = (path) => router.push(path)
const normalizeSceneOptions = (payload) => Array.isArray(payload?.scenes) ? payload.scenes : Array.isArray(payload?.data?.scenes) ? payload.data.scenes : []
const normalizeRecommendationItems = (payload) => Array.isArray(payload?.items) ? payload.items : Array.isArray(payload?.data?.items) ? payload.data.items : []

const formatTimeText = (rawValue) => {
  if (!rawValue) return ''
  const date = new Date(rawValue)
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleString()
}

const resolvePrimaryUrl = (item) => String(item?.external_url || item?.target_url || item?.source_url || item?.link || item?.url || '').trim()
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
  return {
    ...item,
    key: resolveItemKey(item, index),
    title: String(item?.title || '未命名内容'),
    tags,
    reasonLabel: String(item?.reason_label || '推荐'),
    summaryText: String(item?.reason_text || item?.summary || '从这里继续进入学习链路。'),
    statusText: item?.status ? videoStatusText(item.status) : '',
    timeText: formatTimeText(item?.upload_time || item?.updated_at || item?.created_at),
    sourceLabel: resolveSourceLabel(item),
    sourceBadgeClass: isExternalItem(item) ? 'badge--external' : item?.processing_origin === 'ios_offline' ? 'badge--mint' : 'badge--soft',
    primaryActionLabel: isExternalItem(item) ? '导入学习' : item?.processing_origin === 'ios_offline' ? '打开本地结果' : '打开详情',
    canLoadRelated: Boolean(item?.id)
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
const externalItems = computed(() => allLoadedItems.value.filter((item) => isExternalItem(item)))
const activeSceneLoading = computed(() => Boolean(sceneLoadingMap.value[activeScene.value]))
const activeSceneError = computed(() => String(sceneErrorMap.value[activeScene.value] || '').trim())
const sceneDescriptionText = computed(() => selectedTag.value ? `当前已按“${selectedTag.value}”筛选 ${activeSceneOption.value.label}。` : activeSceneOption.value.description)

const setSceneLoading = (scene, value) => { sceneLoadingMap.value = { ...sceneLoadingMap.value, [scene]: value } }
const setSceneError = (scene, value) => { sceneErrorMap.value = { ...sceneErrorMap.value, [scene]: value } }
const setSceneItems = (scene, items) => { sceneItemsMap.value = { ...sceneItemsMap.value, [scene]: items } }
const toggleTag = (tag) => { selectedTag.value = selectedTag.value === tag ? '' : tag }

const openRecommendation = (item) => {
  if (isExternalItem(item)) {
    const url = resolvePrimaryUrl(item)
    if (!url) return
    router.push({ path: '/upload', query: { mode: 'url', url, source: item.sourceLabel || '站外推荐' } })
    return
  }
  if (item.processing_origin === 'ios_offline' && item.task_id) {
    router.push(`/local-transcripts/${item.task_id}`)
    return
  }
  if (item.id) router.push(`/videos/${item.id}`)
}

const loadScene = async (scene, { force = false } = {}) => {
  if (!force && (sceneItemsMap.value[scene] || []).length > 0) return sceneItemsMap.value[scene]
  setSceneLoading(scene, true)
  setSceneError(scene, '')
  try {
    const res = await getVideoRecommendations({ scene, limit: 6, include_external: true })
    const items = normalizeRecommendationItems(res?.data || {})
    setSceneItems(scene, items)
    return items
  } catch (error) {
    setSceneError(scene, error?.message || `${scene} 场景加载失败`)
    setSceneItems(scene, [])
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
  if (!item?.id) return
  relatedSeed.value = item
  relatedLoading.value = true
  relatedError.value = ''
  try {
    const res = await getVideoRecommendations({ scene: 'related', seed_video_id: item.id, limit: 4, include_external: true })
    relatedItems.value = normalizeRecommendationItems(res?.data || {})
  } catch (error) {
    relatedItems.value = []
    relatedError.value = error?.message || '相关推荐加载失败'
  } finally {
    relatedLoading.value = false
  }
}

const reloadRelated = async () => {
  if (relatedSeed.value?.id) await loadRelatedByItem(relatedSeed.value)
}

const clearRelated = () => {
  relatedSeed.value = null
  relatedItems.value = []
  relatedError.value = ''
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
.recommendations-page { display: grid; gap: 14px; padding-top: calc(16px + env(safe-area-inset-top)); }
.hero,.panel { display: grid; gap: 14px; padding: 18px; border-radius: 24px; border: 1px solid rgba(24, 45, 73, 0.08); background: rgba(255, 255, 255, 0.76); box-shadow: 0 12px 28px rgba(24, 45, 73, 0.08); }
.hero { background: linear-gradient(155deg, rgba(255, 255, 255, 0.97) 0%, rgba(243, 251, 253, 0.92) 62%, rgba(231, 245, 249, 0.86) 100%); }
.hero__eyebrow,.badge,.pill,.mini-tag { display: inline-flex; align-items: center; border-radius: 999px; font-size: 11px; font-weight: 800; }
.hero__eyebrow,.badge--soft,.pill,.mini-tag { padding: 4px 10px; background: rgba(31, 122, 140, 0.12); color: var(--primary-deep); }
.badge--reason { padding: 4px 10px; background: rgba(14, 99, 122, 0.12); color: #11556a; }
.badge--external { padding: 4px 10px; background: rgba(235, 140, 52, 0.16); color: #8f4f12; }
.badge--mint { padding: 4px 10px; background: rgba(31, 176, 135, 0.14); color: #0d7253; }
.hero__title { margin-top: 8px; font-size: 30px; line-height: 1.08; }
.hero__desc,.section-head p,.recommend-card__desc,.recommend-card__meta,.message,.tag-card__sample,.provider-card__desc,.related-card__desc,.seed-card__meta { color: var(--muted); }
.hero__desc { margin-top: 8px; font-size: 14px; line-height: 1.6; }
.hero__actions,.hero__stats,.scene-tabs,.tag-grid,.card-list,.provider-grid,.skeleton-list { display: grid; gap: 10px; }
.hero__actions,.hero__stats,.provider-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.hero__actions { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.hero-btn,.scene-tab,.tag-card,.recommend-card,.related-card,.external-card,.provider-card,.action-btn { border: 1px solid rgba(24, 45, 73, 0.08); background: rgba(255, 255, 255, 0.92); }
.hero-btn,.action-btn { border-radius: 14px; padding: 12px; font-size: 13px; font-weight: 900; }
.hero-btn--primary,.action-btn--primary { border: 0; color: #f6feff; background: linear-gradient(135deg, #145b66, #1f7a8c); box-shadow: 0 8px 16px rgba(31, 122, 140, 0.2); }
.hero-btn--ghost,.panel-link,.provider-card__cta { color: var(--primary-deep); }
.hero-stat,.seed-card { display: grid; gap: 4px; border-radius: 16px; padding: 12px 14px; background: rgba(255, 255, 255, 0.74); border: 1px solid rgba(24, 45, 73, 0.08); }
.hero-stat span,.seed-card__label { font-size: 12px; font-weight: 700; color: var(--muted); }
.hero-stat strong,.seed-card__title { font-size: 22px; font-weight: 900; color: var(--text); }
.section-head,.recommend-card__top,.recommend-card__meta,.recommend-card__actions,.related-card { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.section-head h2 { margin: 0; font-size: 18px; }
.section-head p { margin-top: 4px; font-size: 13px; line-height: 1.55; }
.panel-link { border: 0; background: transparent; font-size: 13px; font-weight: 800; }
.scene-tab,.tag-card,.provider-card,.recommend-card,.external-card { width: 100%; text-align: left; }
.scene-tab,.tag-card,.provider-card,.recommend-card,.related-card,.external-card { border-radius: 18px; padding: 14px; }
.scene-tab { display: grid; gap: 6px; }
.scene-tab--active,.tag-card--active { border-color: rgba(31, 122, 140, 0.24); background: linear-gradient(180deg, rgba(231, 247, 250, 0.92), rgba(255, 255, 255, 0.92)); }
.scene-tab__label,.provider-card__name,.recommend-card__title,.related-card__title { font-size: 16px; font-weight: 900; color: #1f2a37; }
.scene-tab__desc,.provider-card__desc,.related-card__desc,.recommend-card__desc,.tag-card__sample { font-size: 12px; line-height: 1.55; }
.tag-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.tag-card { display: grid; gap: 4px; }
.tag-card__name { font-size: 14px; font-weight: 900; color: #1f2a37; }
.tag-card__count { font-size: 20px; font-weight: 900; color: var(--primary-deep); }
.recommend-card,.external-card { display: grid; gap: 10px; }
.mini-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.recommend-card__meta { font-size: 12px; }
.related-card__copy { display: grid; gap: 6px; }
.message { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 14px 15px; border-radius: 16px; background: rgba(255, 255, 255, 0.8); border: 1px dashed rgba(24, 45, 73, 0.12); font-size: 13px; line-height: 1.55; }
.message--error { color: var(--bad-text); background: rgba(255, 244, 244, 0.92); border-style: solid; border-color: rgba(214, 69, 69, 0.16); }
.skeleton-card { height: 132px; border-radius: 18px; background: linear-gradient(90deg, rgba(240, 248, 250, 0.95), rgba(255, 255, 255, 0.95), rgba(240, 248, 250, 0.95)); background-size: 200% 100%; animation: shimmer 1.4s linear infinite; }
.skeleton-card--short { height: 100px; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
@media (max-width: 720px) { .hero__actions,.hero__stats,.tag-grid,.provider-grid { grid-template-columns: 1fr; } }
</style>
