import request from '@/utils/request'
import { shouldUseMockApi } from '@/config'

const MOCK_SCREENSHOT_BASE64 =
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/axm8lEAAAAASUVORK5CYII='

let mockProjects = [
  {
    id: 'mock_proj_1',
    name: 'EduMind Mobile Design',
    slug: 'edumind-mobile-design',
    createdAt: '2026-03-26T00:00:00Z',
    updatedAt: '2026-03-26T00:00:00Z'
  }
]

const toMockResponse = (data) => Promise.resolve({ data, status: 200, headers: { 'x-edumind-ui-only': 'true' } })

export function getDesignStatus() {
  if (shouldUseMockApi()) {
    return toMockResponse({
      success: true,
      configured: false,
      provider: 'sleek',
      base_url: 'https://sleek.design'
    })
  }
  return request({ url: '/api/design/status', method: 'get' })
}

export function getDesignProjects(params = {}) {
  if (shouldUseMockApi()) {
    return toMockResponse({
      success: true,
      items: mockProjects,
      pagination: { total: mockProjects.length, limit: 50, offset: 0 }
    })
  }
  return request({ url: '/api/design/projects', method: 'get', params })
}

export function createDesignProject(name) {
  if (shouldUseMockApi()) {
    const project = {
      id: `mock_proj_${Date.now()}`,
      name: String(name || '').trim() || '未命名项目',
      slug: 'mock-project',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
    mockProjects = [project, ...mockProjects]
    return toMockResponse({ success: true, project })
  }
  return request({
    url: '/api/design/projects',
    method: 'post',
    data: { name }
  })
}

export function sendDesignMessage(projectId, payload) {
  if (shouldUseMockApi()) {
    return toMockResponse({
      success: true,
      project_id: projectId,
      run: {
        runId: `mock_run_${Date.now()}`,
        status: 'completed',
        result: {
          assistantText: `UI 模式下已根据你的描述生成“${String(payload?.message || '').trim() || '设计稿'}”示意结果。`,
          operations: [
            {
              type: 'screen_created',
              screenId: 'mock_screen_home',
              screenName: 'Home',
              componentId: 'mock_component_home'
            }
          ]
        }
      },
      screenshots: [
        {
          component_ids: ['mock_component_home'],
          mime_type: 'image/png',
          data_base64: MOCK_SCREENSHOT_BASE64
        }
      ]
    })
  }
  return request({
    url: `/api/design/projects/${projectId}/messages`,
    method: 'post',
    data: payload,
    timeout: 310000,
    retry: 0
  })
}

export function getDesignRun(projectId, runId, params = {}) {
  if (shouldUseMockApi()) {
    return sendDesignMessage(projectId, { message: `恢复 ${runId}` })
  }
  return request({
    url: `/api/design/projects/${projectId}/runs/${runId}`,
    method: 'get',
    params
  })
}

export function getDesignComponent(projectId, componentId) {
  if (shouldUseMockApi()) {
    return toMockResponse({
      success: true,
      component: {
        id: componentId,
        name: 'Mock Home',
        activeVersion: 1,
        versions: [
          {
            id: 'mock_ver_1',
            version: 1,
            code: '<!DOCTYPE html><html><body><main>UI mock component</main></body></html>'
          }
        ]
      }
    })
  }
  return request({
    url: `/api/design/projects/${projectId}/components/${componentId}`,
    method: 'get'
  })
}
