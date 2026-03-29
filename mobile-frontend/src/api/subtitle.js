import request from '@/utils/request'
import { shouldUseMockApi } from '@/config'
import { mockGetMergedVideoSubtitles, mockGetVideoSubtitles } from '@/api/mockGateway'

export function getVideoSubtitles(videoId) {
  if (shouldUseMockApi()) return mockGetVideoSubtitles(videoId)
  return request({ url: `/api/subtitles/videos/${videoId}/subtitles`, method: 'get' })
}

export function getMergedVideoSubtitles(videoId, { forceRefresh = false } = {}) {
  if (shouldUseMockApi()) return mockGetMergedVideoSubtitles(videoId)
  return request({
    url: `/api/subtitles/videos/${videoId}/subtitles/semantic-merged`,
    method: 'get',
    params: {
      force_refresh: forceRefresh
    }
  })
}

export async function getSubtitleContext(videoId, { preferMerged = true, forceRefresh = false } = {}) {
  if (preferMerged) {
    try {
      return await getMergedVideoSubtitles(videoId, { forceRefresh })
    } catch (error) {
      return getVideoSubtitles(videoId)
    }
  }
  return getVideoSubtitles(videoId)
}
