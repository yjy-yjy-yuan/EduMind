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
            <div class="result-group-title">视频 ID: {{ group.videoId }}</div>
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

    const open = () => emit('open', props.result)

    return {
      formatTime,
      getSimilarityColor,
      open
    }
  },
  template: `
    <div class="result-item" @click="open">
      <div class="result-time">
        {{ formatTime(result.start_time) }} - {{ formatTime(result.end_time) }}
      </div>
      <div class="result-similarity">
        <div class="similarity-bar">
          <div
            class="similarity-fill"
            :style="{ width: (result.similarity_score * 100) + '%', backgroundColor: getSimilarityColor(result.similarity_score) }"
          ></div>
        </div>
        <span class="similarity-text">{{ (result.similarity_score * 100).toFixed(0) }}%</span>
      </div>
      <div v-if="result.preview_text" class="result-preview">
        {{ result.preview_text }}
      </div>
      <div v-else class="result-preview placeholder">
        暂无文本预览
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
        const list = groups.get(result.video_id) || []
        list.push(result)
        groups.set(result.video_id, list)
      }
      return Array.from(groups.entries()).map(([videoId, items]) => ({ videoId, items }))
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
  font-size: 14px;
  font-weight: 600;
  color: #666;
}

.results-header {
  padding: 12px 0;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 12px;
}

.result-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;
}

.result-item {
  background: white;
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.result-time {
  font-size: 14px;
  font-weight: 600;
  color: #2196f3;
  margin-bottom: 8px;
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

.similarity-text {
  min-width: 40px;
  text-align: right;
  font-size: 12px;
  color: #666;
}

.result-preview {
  font-size: 13px;
  line-height: 1.4;
  color: #555;
}

.result-preview.placeholder {
  color: #aaa;
  font-style: italic;
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
