<template>
  <div class="search-page">
    <div class="search-header">
      <div class="search-bar-container">
        <input
          v-model="query"
          type="text"
          class="search-input"
          :placeholder="searchInputPlaceholder"
          :disabled="isSearching"
          @keyup.enter="handleSearch"
        />
        <button v-if="query.trim() || hasSearched" class="clear-btn" @click="clearSearch">
          ✕
        </button>
        <button class="search-btn" :disabled="!query.trim() || isSearching" @click="handleSearch">
          {{ isSearching ? searchCopySearching : searchCopySearchButton }}
        </button>
      </div>

      <div v-if="!isLockedToAllScope" class="search-scope">
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
          <input v-model="searchScope" type="radio" :value="defaultSearchScope" name="scope" />
          <span>{{ searchCopyAllScopeHint }}</span>
        </label>
      </div>
      <div v-else class="search-scope-locked">
        <span class="search-scope-locked__text">{{ searchCopyAllScopeHint }}</span>
        <span class="search-scope-locked__badge">{{ searchCopyScopeLockedBadge }}</span>
      </div>
    </div>

    <div class="search-results-container">
      <div v-if="!hasSearched" class="search-state empty-state">
        <div class="empty-icon">🔍</div>
        <p>{{ isLockedToAllScope ? searchCopyEmptyStateScopeAll : searchCopyEmptyStateGeneric }}</p>
      </div>

      <div v-else-if="isSearching" class="search-state loading-state">
        <div class="spinner"></div>
        <p>{{ searchCopySearching }}</p>
      </div>

      <div v-else-if="error" class="search-state error-state">
        <div class="error-icon">⚠️</div>
        <p>{{ error }}</p>
        <button class="retry-btn" @click="handleSearch">{{ searchCopyRetry }}</button>
      </div>

      <div v-else-if="results.length === 0" class="search-state empty-result">
        <template v-if="indexEmptyHint">
          <div class="empty-icon">📂</div>
          <p class="empty-primary">{{ indexEmptyHint }}</p>
          <p class="empty-guide">{{ searchCopyNoIndexGuide }}</p>
          <div class="empty-actions">
            <button type="button" class="link-btn" @click="router.push('/upload')">去上传</button>
            <button type="button" class="link-btn" @click="router.push('/videos')">视频库</button>
            <button v-if="hasCurrentVideoContext" type="button" class="link-btn" @click="goCurrentVideo">
              当前视频详情
            </button>
          </div>
        </template>
        <template v-else>
          <div class="empty-icon">😕</div>
          <p>{{ noResultsText }}</p>
        </template>
      </div>

      <div v-else class="results-list">
        <div class="results-header">
          <p>{{ resultsHeaderText }}</p>
        </div>

        <template v-if="searchScope === defaultSearchScope">
          <div v-for="group in groupedResults" :key="group.videoId" class="result-group">
            <div class="result-group-title">{{ group.videoTitle }}</div>
            <button
              v-for="result in group.items"
              :key="result.chunk_id"
              type="button"
              class="result-item"
              @click="handleResultClick(result)"
            >
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
                <span class="play-hint">👉 {{ searchCopyPlayHint }}</span>
              </div>
            </button>
          </div>
        </template>

        <template v-else>
          <button
            v-for="result in results"
            :key="result.chunk_id"
            type="button"
            class="result-item"
            @click="handleResultClick(result)"
          >
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
              <span class="play-hint">👉 {{ searchCopyPlayHint }}</span>
            </div>
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { semanticSearch } from '@/api/search'
import {
  DEFAULT_SEARCH_LIMIT,
  DEFAULT_SEARCH_SCOPE,
  DEFAULT_SEARCH_THRESHOLD,
  SEARCH_COPY_ALL_SCOPE_HINT,
  SEARCH_COPY_CURRENT_VIDEO_LABEL_FALLBACK,
  SEARCH_COPY_CURRENT_VIDEO_LABEL_NO_CONTEXT,
  SEARCH_COPY_CURRENT_VIDEO_LABEL_PREFIX,
  SEARCH_COPY_EMPTY_STATE_GENERIC,
  SEARCH_COPY_EMPTY_STATE_SCOPE_ALL,
  SEARCH_COPY_NO_INDEX_GUIDE,
  SEARCH_COPY_NO_RESULTS_TEMPLATE,
  SEARCH_COPY_PAGE_INPUT_PLACEHOLDER_ALL,
  SEARCH_COPY_PAGE_INPUT_PLACEHOLDER_CURRENT,
  SEARCH_COPY_PLAY_HINT,
  SEARCH_COPY_PREVIEW_FALLBACK,
  SEARCH_COPY_RETRY,
  SEARCH_COPY_RESULTS_HEADER_ALL,
  SEARCH_COPY_RESULTS_HEADER_CURRENT,
  SEARCH_COPY_SCOPE_LOCKED_BADGE,
  SEARCH_COPY_SEARCHING,
  SEARCH_COPY_SEARCH_BUTTON,
  SEARCH_ROUTE_PREFILL_QUERY,
  SEARCH_ROUTE_SCOPE_QUERY
} from '@/config/searchDefaults'
import { storageGet, storageRemove, storageSet } from '@/utils/storage'

const SEARCH_STATE_KEY_PREFIX = 'm_search_state'

const parseJSON = (text, fallback = null) => {
  if (!text) return fallback
  try {
    return JSON.parse(text)
  } catch {
    return fallback
  }
}

export default {
  name: 'SearchPage',
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
    const scopeQuery = computed(() =>
      String(route.query[SEARCH_ROUTE_SCOPE_QUERY] ?? '').toLowerCase()
    )
    const isLockedToAllScope = computed(() => scopeQuery.value === DEFAULT_SEARCH_SCOPE)
    const currentVideoTitle = computed(() => String(route.query.videoTitle || '').trim())
    const hasCurrentVideoContext = computed(() => currentVideoId.value !== null)
    const currentVideoLabel = computed(() => {
      if (!hasCurrentVideoContext.value) return SEARCH_COPY_CURRENT_VIDEO_LABEL_NO_CONTEXT
      return currentVideoTitle.value
        ? `${SEARCH_COPY_CURRENT_VIDEO_LABEL_PREFIX}${currentVideoTitle.value}`
        : SEARCH_COPY_CURRENT_VIDEO_LABEL_FALLBACK
    })
    const initialSearchScope = () => {
      if (scopeQuery.value === DEFAULT_SEARCH_SCOPE) return DEFAULT_SEARCH_SCOPE
      if (scopeQuery.value === 'current' && hasCurrentVideoContext.value) return 'current'
      return hasCurrentVideoContext.value ? 'current' : DEFAULT_SEARCH_SCOPE
    }
    const searchScope = ref(initialSearchScope())
    const indexEmptyHint = ref('')
    const searchStateKey = computed(() => {
      if (currentVideoId.value !== null) {
        return `${SEARCH_STATE_KEY_PREFIX}:video:${currentVideoId.value}`
      }
      return `${SEARCH_STATE_KEY_PREFIX}:all`
    })

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
    const searchInputPlaceholder = computed(() =>
      searchScope.value === DEFAULT_SEARCH_SCOPE
        ? SEARCH_COPY_PAGE_INPUT_PLACEHOLDER_ALL
        : SEARCH_COPY_PAGE_INPUT_PLACEHOLDER_CURRENT
    )
    const resultsHeaderText = computed(() => {
      const label =
        searchScope.value === 'current' ? SEARCH_COPY_RESULTS_HEADER_CURRENT : SEARCH_COPY_RESULTS_HEADER_ALL
      return `${label}（${results.value.length} 条）`
    })
    const noResultsText = computed(() =>
      SEARCH_COPY_NO_RESULTS_TEMPLATE.replace('{query}', query.value)
    )

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

    const getSimilarityPercentage = (similarity) => Math.round(Number(similarity || 0) * 100)

    const getVideoTitle = (result) => result.video_title || `视频 ID: ${result.video_id}`

    const getPreviewText = (result) => {
      if (result.preview_text && result.preview_text.trim()) {
        return result.preview_text
      }
      return SEARCH_COPY_PREVIEW_FALLBACK
    }

    const persistSearchState = () => {
      const payload = {
        query: query.value,
        results: Array.isArray(results.value) ? results.value : [],
        error: error.value,
        hasSearched: hasSearched.value,
        searchScope: searchScope.value
      }
      storageSet(searchStateKey.value, JSON.stringify(payload))
    }

    const applyRoutePrefill = () => {
      const pre = String(route.query[SEARCH_ROUTE_PREFILL_QUERY] || '').trim()
      if (pre) {
        query.value = pre
      }
    }

    const restoreSearchState = () => {
      const cached = parseJSON(storageGet(searchStateKey.value), null)
      if (!cached || typeof cached !== 'object') {
        applyRoutePrefill()
        return
      }

      query.value = typeof cached.query === 'string' ? cached.query : ''
      results.value = Array.isArray(cached.results) ? cached.results : []
      error.value = typeof cached.error === 'string' ? cached.error : ''
      hasSearched.value = Boolean(cached.hasSearched)

      if (scopeQuery.value === DEFAULT_SEARCH_SCOPE) {
        searchScope.value = DEFAULT_SEARCH_SCOPE
      } else {
        const nextScope =
          cached.searchScope === 'current' && hasCurrentVideoContext.value ? 'current' : DEFAULT_SEARCH_SCOPE
        searchScope.value = nextScope
      }
      applyRoutePrefill()
    }

    const clearSearch = () => {
      query.value = ''
      results.value = []
      error.value = ''
      hasSearched.value = false
      indexEmptyHint.value = ''
      storageRemove(searchStateKey.value)
    }

    const goCurrentVideo = () => {
      if (currentVideoId.value !== null) {
        router.push(`/videos/${currentVideoId.value}`)
      }
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
      indexEmptyHint.value = ''

      try {
        const res = await semanticSearch({
          query: query.value.trim(),
          video_ids: videoIds.value,
          limit: DEFAULT_SEARCH_LIMIT,
          threshold: DEFAULT_SEARCH_THRESHOLD
        })
        const payload = res?.data ?? res ?? {}
        results.value = Array.isArray(payload.results) ? payload.results : []
        const msg = typeof payload.message === 'string' ? payload.message.trim() : ''
        indexEmptyHint.value = results.value.length === 0 && msg ? msg : ''
      } catch (err) {
        const status = err?.response?.status
        const detail = err?.response?.data?.detail
        if (status === 503) {
          error.value =
            typeof detail === 'string' && detail.trim()
              ? detail
              : '语义搜索功能未启用，请在后端开启 SEARCH_ENABLED 后重试'
        } else {
          error.value = detail || err?.message || '搜索失败，请稍后重试'
        }
        results.value = []
        indexEmptyHint.value = ''
      } finally {
        isSearching.value = false
        persistSearchState()
      }
    }

    const handleResultClick = (result) => {
      persistSearchState()
      router.push({
        path: `/player/${result.video_id}`,
        query: { start: String(Math.floor(Number(result.start_time || 0))) }
      })
    }

    watch(searchStateKey, () => {
      restoreSearchState()
    }, { immediate: true })

    watch(
      () => route.query[SEARCH_ROUTE_PREFILL_QUERY],
      () => {
        applyRoutePrefill()
      }
    )

    watch(
      () => scopeQuery.value,
      (s) => {
        if (s === DEFAULT_SEARCH_SCOPE) {
          searchScope.value = DEFAULT_SEARCH_SCOPE
        }
      },
      { immediate: true }
    )

    watch(searchScope, (next) => {
      if (isLockedToAllScope.value && next !== DEFAULT_SEARCH_SCOPE) {
        searchScope.value = DEFAULT_SEARCH_SCOPE
        return
      }
      if (next === 'current' && !hasCurrentVideoContext.value) {
        searchScope.value = DEFAULT_SEARCH_SCOPE
        return
      }
      persistSearchState()
    })

    return {
      defaultSearchScope: DEFAULT_SEARCH_SCOPE,
      currentVideoLabel,
      goCurrentVideo,
      indexEmptyHint,
      isLockedToAllScope,
      router,
      searchCopyAllScopeHint: SEARCH_COPY_ALL_SCOPE_HINT,
      searchCopyEmptyStateGeneric: SEARCH_COPY_EMPTY_STATE_GENERIC,
      searchCopyEmptyStateScopeAll: SEARCH_COPY_EMPTY_STATE_SCOPE_ALL,
      searchCopyNoIndexGuide: SEARCH_COPY_NO_INDEX_GUIDE,
      searchCopyPlayHint: SEARCH_COPY_PLAY_HINT,
      searchCopyRetry: SEARCH_COPY_RETRY,
      searchCopyScopeLockedBadge: SEARCH_COPY_SCOPE_LOCKED_BADGE,
      searchCopySearching: SEARCH_COPY_SEARCHING,
      searchCopySearchButton: SEARCH_COPY_SEARCH_BUTTON,
      searchInputPlaceholder,
      noResultsText,
      resultsHeaderText,
      error,
      formatTime,
      getPreviewText,
      getSimilarityColor,
      getSimilarityPercentage,
      getVideoTitle,
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

.search-scope-locked {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  padding: 10px 12px;
  border-radius: 10px;
  background: #e3f2fd;
  border: 1px solid #90caf9;
}

.search-scope-locked__text {
  font-size: 14px;
  font-weight: 600;
  color: #1565c0;
}

.search-scope-locked__badge {
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
  background: #1976d2;
  color: #fff;
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

.empty-primary {
  margin: 0 0 8px;
  text-align: center;
  color: #555;
  font-size: 15px;
  line-height: 1.5;
  max-width: 22rem;
}

.empty-guide {
  margin: 0 0 16px;
  text-align: center;
  color: #888;
  font-size: 13px;
  line-height: 1.55;
  max-width: 22rem;
}

.empty-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  align-items: center;
}

.link-btn {
  min-height: 40px;
  padding: 8px 14px;
  border: 1px solid #2196f3;
  border-radius: 8px;
  background: white;
  color: #1976d2;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.link-btn:active {
  background: #e3f2fd;
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
  display: block;
  width: 100%;
  text-align: left;
  border: none;
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
