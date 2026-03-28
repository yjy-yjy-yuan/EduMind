import request from '@/utils/request'
import { shouldUseMockApi } from '@/config'
import {
  mockGetRecommendationScenes,
  mockGetVideoRecommendations,
  mockImportExternalRecommendation
} from '@/api/mockGateway'

export function getRecommendationScenes() {
  if (shouldUseMockApi()) return mockGetRecommendationScenes()
  return request({ url: '/api/recommendations/scenes', method: 'get' })
}

export function getVideoRecommendations(params = {}) {
  if (shouldUseMockApi()) return mockGetVideoRecommendations(params)
  return request({ url: '/api/recommendations/videos', method: 'get', params })
}

export function importExternalRecommendation(data = {}) {
  if (shouldUseMockApi()) return mockImportExternalRecommendation(data)
  return request({
    url: '/api/recommendations/import-external',
    method: 'post',
    data,
    timeout: 600000,
    retry: 0
  })
}
