<template>
  <div class="search-page">
    <div class="search-header">
      <div class="search-bar-container">
        <input
          v-model="query"
          type="text"
          class="search-input"
          placeholder="输入搜索关键词..."
          :disabled="isSearching"
          @keyup.enter="handleSearch"
        />
        <button v-if="query.trim() || hasSearched" class="clear-btn" @click="clearSearch">
          ✕
        </button>
        <button class="search-btn" :disabled="!query.trim() || isSearching" @click="handleSearch">
          {{ isSearching ? '搜索中...' : '搜索' }}
        </button>
      </div>

      <div class="search-scope">
        <label class="scope-option">
          <input
            v-model="searchScope"
            type="radio"
            value="current"
            name="scope"
            :disabled="!hasCurrentVideoContext"
          />
          <span>{{ currentVideoLabel }}</span>
        </label>
        <label class="scope-option">
          <input v-model="searchScope" type="radio" value="all" name="scope" />
          <span>所有视频</span>
        </label>
      </div>
    </div>

    <div class="search-results-container">
      <div v-if="!hasSearched" class="search-state empty-state">
        <div class="empty-icon">🔍</div>
        <p>输入关键词开始搜索</p>
      </div>

      <div v-else-if="isSearching" class="search-state loading-state">
        <div class="spinner"></div>
        <p>搜索中...</p>
      </div>

      <div v-else-if="error" class="search-state error-state">
        <div class="error-icon">⚠️</div>
        <p>{{ error }}</p>
        <button class="retry-btn" @click="handleSearch">重试</button>
      </div>

      <div v-else-if="results.length === 0" class="search-state empty-result">
        <div class="empty-icon">😕</div>
        <p>未找到与“{{ query }}”相关的内容</p>
      </div>

      <div v-else class="results-list">
        <div class="results-header">
          <p>{{ searchScope === 'current' ? `搜索结果（${results.length} 条）` : `跨视频搜索结果（${results.length} 条）` }}</p>
        </div>

        <template v-if="searchScope === 'all'">
          <div v-for="group in groupedResults" :key="group.videoId" class="result-group">
            <div class="result-group-title">{{ group.videoTitle }}</div>
            <ResultCard
              v-for="result in group.items"
              :key="result.chunk_id"
              :result="result"
              @open="handleResultClick"
            />
          </div>
        </template>

        <template v-else>
          <ResultCard v-for="result in results" :key="result.chunk_id" :result="result" @open="handleResultClick" />
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, defineComponent, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { semanticSearch } from '@/api/search'

const ResultCard = defineComponent({
  name: 'SearchResultCard',
  props: {
    result: {
      type: Object,
      required: true
    }
  },
  emits: ['open'],
  setup(props, { emit }) {
    const formatTime = (seconds) => {
      const total = Math.max(0, Math.round(Number(seconds || 0)))
      const minutes = Math.floor(total / 60)
      const remain = total % 60
      return `${String(minutes).padStart(2, '0')}:${String(remain).padStart(2, '0')}`
    }

    const getSimilarityColor = (similarity) => {
      if (similarity >= 0.7) return '#4CAF50'
      if (similarity >= 0.5) return '#FFC107'
      return '#FF6B6B'
    }

    const getSimilarityPercentage = (similarity) => {
      return Math.round(similarity * 100)
    }

    const getVideoTitle = (result) => {
      return result.video_title || `视频 ID: ${result.video_id}`
    }

    const getPreviewText = (result) => {
      if (result.preview_text && result.preview_text.trim()) {
        return result.preview_text
      }
      return '（暂无文本预览）'
    }

    const open = () => emit('open', props.result)

    return {
      formatTime,
      getSimilarityColor,
      getSimilarityPercentage,
      getVideoTitle,
      getPreviewText,
      open
    }
  },
  template: `
    <div class="result-item" @click="open">
      <div class="result-header">
        <div class="result-video-title">{{ getVideoTitle(result) }}</div>
        <div class="result-similarity-percentage">
          <span class="percentage-text">{{ getSimilarityPercentage(result.similarity_score) }}% 相关</span>
        </div>
      </div>

      <div class="result-meta">
        <div class="result-time">
          <span class="time-label">⏱️</span>
          <span class="time-range">{{ formatTime(result.start_time) }} - {{ formatTime(result.end_time) }}</span>
        </div>
      </div>

      <div class="result-similarity">
        <div class="similarity-bar">
          <div
            class="similarity-fill"
            :style="{ width: (result.similarity_score * 100) + '%', backgroundColor: getSimilarityColor(result.similarity_score) }"
          ></div>
        </div>
      </div>

      <div :class="['result-preview', { placeholder: !result.preview_text || !result.preview_text.trim() }]">
        {{ getPreviewText(result) }}
      </div>

      <div class="result-cta">
        <span class="play-hint">👉 点击播放此片段</span>
      </div>
    </div>
  `
})

export default {
  name: 'SearchPage',
  components: { ResultCard },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const query = ref('')
    const results = ref([])
    const isSearching = ref(false)
    const error = ref('')
    const hasSearched = ref(false)

    const currentVideoId = computed(() => {
      const raw = route.query.videoId ?? route.params.videoId ?? route.params.id
      if (raw == null) return null
      const parsed = Number.parseInt(String(raw), 10)
      return Number.isFinite(parsed) ? parsed : null
    })
    const currentVideoTitle = computed(() => String(route.query.videoTitle || '').trim())
    const hasCurrentVideoContext = computed(() => currentVideoId.value !== null)
    const currentVideoLabel = computed(() => {
      if (!hasCurrentVideoContext.value) return '当前视频（需从详情页进入）'
      return currentVideoTitle.value ? `当前视频：${currentVideoTitle.value}` : '当前视频'
    })
    const searchScope = ref(hasCurrentVideoContext.value ? 'current' : 'all')

    const videoIds = computed(() => {
      if (searchScope.value === 'current' && currentVideoId.value !== null) {
        return [currentVideoId.value]
      }
      return null
    })

    const groupedResults = computed(() => {
      const groups = new Map()
      for (const result of results.value) {
        const videoId = result.video_id
        const list = groups.get(videoId) || []
        list.push(result)
        groups.set(videoId, list)
      }
      return Array.from(groups.entries()).map(([videoId, items]) => {
        const videoTitle = items[0]?.video_title || `视频 ID: ${videoId}`
        return { videoId, videoTitle, items }
      })
    })

    const clearSearch = () => {
      query.value = ''
      results.value = []
      error.value = ''
      hasSearched.value = false
    }

    const handleSearch = async () => {
      if (!query.value.trim()) return

      if (searchScope.value === 'current' && !hasCurrentVideoContext.value) {
        error.value = '当前页面没有视频上下文，请切换到“所有视频”，或从视频详情页进入搜索。'
        hasSearched.value = true
        results.value = []
        return
      }

      isSearching.value = true
      error.value = ''
      hasSearched.value = true

      try {
        const res = await semanticSearch({
          query: query.value.trim(),
          video_ids: videoIds.value,
          limit: 20,
          threshold: 0.5
        })
        results.value = Array.isArray(res.data?.results) ? res.data.results : []
      } catch (err) {
        error.value = err?.response?.data?.detail || err?.message || '搜索失败，请稍后重试'
        results.value = []
      } finally {
        isSearching.value = false
      }
    }

    const handleResultClick = (result) => {
      router.push({
        path: `/player/${result.video_id}`,
        query: { start: String(Math.floor(Number(result.start_time || 0))) }
      })
    }

    return {
      currentVideoLabel,
      error,
      groupedResults,
      handleResultClick,
      handleSearch,
      hasCurrentVideoContext,
      hasSearched,
      isSearching,
      query,
      results,
      searchScope,
      clearSearch
    }
  }
}
</script>

<style scoped>
.search-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}

.search-header {
  padding: 16px;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-bottom: 1px solid #e0e0e0;
}

.search-bar-container {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  align-items: center;
}

.search-input {
  flex: 1;
  min-height: 44px;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  background: #f9f9f9;
  box-sizing: border-box;
}

.search-input:focus {
  outline: none;
  border-color: #2196f3;
  background: white;
}

.clear-btn,
.search-btn,
.retry-btn {
  min-width: 44px;
  min-height: 44px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.clear-btn {
  width: 44px;
  background: #e0e0e0;
  font-size: 18px;
}

.search-btn,
.retry-btn {
  padding: 0 16px;
  background: #2196f3;
  color: white;
  font-size: 14px;
  font-weight: 500;
}

.search-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.search-scope {
  display: flex;
  gap: 20px;
}

.scope-option {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.search-results-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.search-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
}

.empty-icon,
.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.loading-state {
  gap: 16px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f0f0f0;
  border-top-color: #2196f3;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.results-list {
  width: 100%;
}

.results-header,
.result-group-title {
  font-size: 13px;
  font-weight: 600;
}

.results-header {
  color: #666;
  padding: 12px 0;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 12px;
}

.result-group-title {
  color: #1976d2;
  padding-left: 4px;
  word-break: break-word;
}

.result-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.result-item {
  background: white;
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: box-shadow 0.2s ease;
}

.result-item:active {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}

.result-video-title {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: #1976d2;
  word-break: break-word;
}

.result-similarity-percentage {
  flex-shrink: 0;
  min-width: 60px;
  text-align: right;
}

.percentage-text {
  font-size: 13px;
  font-weight: 600;
  color: #4CAF50;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;
}

.result-time {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #666;
}

.time-label {
  font-size: 13px;
}

.time-range {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  font-weight: 500;
  color: #2196f3;
}

.result-similarity {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.similarity-bar {
  flex: 1;
  height: 6px;
  background: #e0e0e0;
  border-radius: 3px;
  overflow: hidden;
}

.similarity-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.result-preview {
  font-size: 13px;
  line-height: 1.5;
  color: #555;
  margin-bottom: 8px;
  max-height: 60px;
  overflow-y: auto;
  word-break: break-word;
  white-space: pre-wrap;
}

.result-preview.placeholder {
  color: #aaa;
  font-style: italic;
}

.result-cta {
  display: flex;
  justify-content: flex-end;
  margin-top: 6px;
}

.play-hint {
  font-size: 12px;
  color: #2196f3;
  font-weight: 500;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 600px) {
  .search-header,
  .search-results-container {
    padding: 12px;
  }

  .search-bar-container {
    gap: 6px;
    margin-bottom: 12px;
  }
}
</style>
