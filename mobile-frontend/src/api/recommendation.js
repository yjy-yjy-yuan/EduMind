import request from '@/utils/request'
import { shouldUseMockApi } from '@/config'
import { mockGetRecommendationScenes, mockGetVideoRecommendations } from '@/api/mockGateway'

export function getRecommendationScenes() {
  if (shouldUseMockApi()) return mockGetRecommendationScenes()
  return request({ url: '/api/recommendations/scenes', method: 'get' })
}

export function getVideoRecommendations(params = {}) {
  if (shouldUseMockApi()) return mockGetVideoRecommendations(params)
  return request({ url: '/api/recommendations/videos', method: 'get', params })
}
