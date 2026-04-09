import request from '@/utils/request'
import { DEFAULT_SEARCH_LIMIT, DEFAULT_SEARCH_THRESHOLD } from '@/config/searchDefaults'

/**
 * 语义搜索
 * @param {Object} params
 * @param {string} params.query 搜索查询文本
 * @param {number[]|null} params.video_ids 视频 ID 列表，null 时搜索全部
 * @param {number} params.limit 返回结果数上限
 * @param {number} params.threshold 相似度阈值（0-1）
 * @returns {Promise<{query, results, total_time_ms, message}>}
 */
export function semanticSearch(params) {
  return request({
    url: '/api/search/semantic/search',
    method: 'post',
    data: {
      query: params.query,
      video_ids: params.video_ids ?? null,
      limit: params.limit ?? DEFAULT_SEARCH_LIMIT,
      threshold: params.threshold ?? DEFAULT_SEARCH_THRESHOLD
    },
    timeout: 30000 // 搜索可能耗时较长
  })
}

/**
 * 手动触发视频索引构建
 * @param {number} videoId 视频 ID
 * @returns {Promise}
 */
export function buildVideoIndex(videoId) {
  return request({
    url: `/api/search/videos/${videoId}/index`,
    method: 'post',
    timeout: 60000 // 索引可能耗时较长
  })
}

/**
 * 查询视频索引状态
 * @param {number} videoId 视频 ID
 * @returns {Promise}
 */
export function getVideoIndexStatus(videoId) {
  return request({
    url: `/api/search/videos/${videoId}/index/status`,
    method: 'get'
  })
}

export default {
  semanticSearch,
  buildVideoIndex,
  getVideoIndexStatus
}
