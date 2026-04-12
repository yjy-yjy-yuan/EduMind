<template>
  <div class="vd-rec-panel">
    <div class="vd-rec-panel__head">
      <p class="vd-rec-panel__intro">
        基于当前视频，从学习库与可信来源为你延伸相关内容。以下为实时推荐结果，不含自动生成的长摘要片段。
      </p>
      <button type="button" class="vd-rec-panel__refresh" :disabled="loading" @click="load(true)">
        {{ loading ? '加载中…' : '刷新推荐' }}
      </button>
    </div>

    <div v-if="loading && items.length === 0" class="vd-rec-panel__skeleton" aria-busy="true">
      <div v-for="n in 4" :key="`sk-${n}`" class="vd-rec-panel__sk-line"></div>
    </div>

    <template v-else>
      <div v-if="actionError" class="vd-rec-panel__banner">{{ actionError }}</div>

      <div v-if="loadError" class="vd-rec-panel__state vd-rec-panel__state--err">
        <span>{{ loadError }}</span>
        <button type="button" class="vd-rec-panel__retry" @click="load(true)">重试</button>
      </div>

      <div v-else-if="items.length === 0" class="vd-rec-panel__state">
        <p class="vd-rec-panel__empty-title">暂无可延伸推荐</p>
        <p class="vd-rec-panel__empty-desc">
          可先完成本视频的转写与摘要，或稍后在网络稳定时重试。推荐仅展示真实可跳转的学习条目，不会用占位内容凑数。
        </p>
      </div>

      <div v-else class="vd-rec-panel__list">
      <VideoDetailRecommendCard
        v-for="(row, index) in items"
        :key="row.key"
        :item="row"
        @open="onOpenCard"
        @primary="onPrimary"
      />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getVideoRecommendations } from '@/api/recommendation'
import {
  decorateRecommendationListItem,
  normalizeRecommendationItems,
  resolveRecommendationNavigation
} from '@/services/recommendationPresentation'
import { emitVideoDetailTelemetry } from '@/services/videoDetailTelemetry'
import VideoDetailRecommendCard from '@/components/videoDetail/VideoDetailRecommendCard.vue'

const props = defineProps({
  seedVideoId: { type: Number, required: true },
  visible: { type: Boolean, default: false }
})

const router = useRouter()
const loading = ref(false)
const loadError = ref('')
const actionError = ref('')
const items = ref([])
const loadedOnce = ref(false)

const load = async (isRefresh = false) => {
  if (!props.seedVideoId || props.seedVideoId <= 0) return
  loading.value = true
  loadError.value = ''
  actionError.value = ''
  try {
    const res = await getVideoRecommendations({
      scene: 'related',
      seed_video_id: props.seedVideoId,
      exclude_video_ids: String(props.seedVideoId),
      limit: 8,
      include_external: true
    })
    const raw = normalizeRecommendationItems(res?.data || {})
    items.value = raw.map((item, index) => decorateRecommendationListItem(item, index))
    if (isRefresh) {
      emitVideoDetailTelemetry('video_detail_recommend_refresh', { seed_video_id: props.seedVideoId, count: items.value.length })
    }
  } catch (e) {
    loadError.value = e?.message || '推荐加载失败'
    items.value = []
  } finally {
    loading.value = false
    loadedOnce.value = true
  }
}

watch(
  () => props.visible,
  (v) => {
    if (v && !loadedOnce.value) {
      emitVideoDetailTelemetry('video_detail_recommend_expose', { seed_video_id: props.seedVideoId })
      load(false)
    }
  },
  { immediate: true }
)

watch(
  () => props.seedVideoId,
  () => {
    loadedOnce.value = false
    items.value = []
    loadError.value = ''
    actionError.value = ''
    if (props.visible) {
      emitVideoDetailTelemetry('video_detail_recommend_expose', { seed_video_id: props.seedVideoId })
      load(false)
    }
  }
)

const navigateItem = (item) => {
  actionError.value = ''
  const nav = resolveRecommendationNavigation(item)
  if (nav.type === 'route') {
    if (typeof nav.location === 'string') router.push(nav.location)
    else router.push(nav.location)
    return
  }
  if (nav.type === 'external' && nav.url) {
    window.location.assign(nav.url)
    return
  }
  actionError.value = nav.message || '无法打开该内容'
}

const onOpenCard = (item) => {
  emitVideoDetailTelemetry('video_detail_recommend_card_click', {
    seed_video_id: props.seedVideoId,
    target_id: item?.id,
    item_key: item?.key,
    is_external: item?.isExternal
  })
  navigateItem(item)
}

const onPrimary = (item) => {
  emitVideoDetailTelemetry('video_detail_recommend_primary_click', {
    seed_video_id: props.seedVideoId,
    target_id: item?.id,
    item_key: item?.key
  })
  navigateItem(item)
}
</script>

<style scoped>
.vd-rec-panel {
  display: grid;
  gap: 14px;
  padding-bottom: 24px;
}

.vd-rec-panel__head {
  display: grid;
  gap: 10px;
}

.vd-rec-panel__intro {
  margin: 0;
  font-size: 12px;
  line-height: 1.55;
  color: #64748b;
  font-weight: 600;
}

.vd-rec-panel__refresh {
  justify-self: start;
  border: 1px solid rgba(95, 71, 126, 0.25);
  background: rgba(255, 255, 255, 0.9);
  color: #5f477e;
  border-radius: 12px;
  padding: 8px 14px;
  font-weight: 800;
  font-size: 12px;
}

.vd-rec-panel__refresh:disabled {
  opacity: 0.5;
}

.vd-rec-panel__list {
  display: grid;
  gap: 12px;
}

.vd-rec-panel__skeleton {
  display: grid;
  gap: 12px;
}

.vd-rec-panel__sk-line {
  height: 96px;
  border-radius: 16px;
  background: linear-gradient(90deg, #f3f4f6, #e5e7eb, #f3f4f6);
  background-size: 200% 100%;
  animation: vd-shimmer 1.2s infinite;
}

@keyframes vd-shimmer {
  0% {
    background-position: 0% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.vd-rec-panel__state {
  padding: 20px 14px;
  border-radius: 16px;
  background: rgba(241, 245, 249, 0.9);
  border: 1px solid rgba(32, 42, 55, 0.06);
  color: #475569;
  font-size: 13px;
  line-height: 1.6;
  font-weight: 600;
}

.vd-rec-panel__state--err {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-start;
}

.vd-rec-panel__empty-title {
  margin: 0 0 8px;
  font-weight: 900;
  color: #0f172a;
}

.vd-rec-panel__empty-desc {
  margin: 0;
  font-size: 12px;
  color: #64748b;
  font-weight: 600;
}

.vd-rec-panel__retry {
  border: 0;
  background: linear-gradient(135deg, #8b799d, #6b5b84);
  color: #fff;
  border-radius: 12px;
  padding: 8px 16px;
  font-weight: 800;
  font-size: 12px;
}

.vd-rec-panel__banner {
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(254, 226, 226, 0.9);
  color: #991b1b;
  font-size: 12px;
  font-weight: 700;
}
</style>
