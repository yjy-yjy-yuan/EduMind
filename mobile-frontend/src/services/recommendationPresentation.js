/**
 * 推荐列表展示与导航（与后端 contract 对齐：不依赖 summary/reason_text/tags 做展示）。
 * 供 Recommendations / VideoDetail 等复用，字段映射变更时只改此文件。
 */
import {
  isRecommendationPrimaryActionDisabled,
  parseRecommendationActionTarget,
  resolveRecommendationUrl,
  shouldOpenRecommendationExternalSource
} from '@/services/recommendationActions'
import { videoStatusText } from '@/services/videoStatus'

export const normalizeRecommendationItems = (payload) =>
  Array.isArray(payload?.items) ? payload.items : Array.isArray(payload?.data?.items) ? payload.data.items : []

export const resolvePrimaryUrl = (item) => resolveRecommendationUrl(item)

export const resolveItemKey = (item, index = 0) =>
  String(item?.id || item?.video_id || resolvePrimaryUrl(item) || `item-${index}`)

export const isExternalItem = (item) => {
  const itemType = String(item?.item_type || item?.content_type || item?.origin_type || '').trim().toLowerCase()
  if (item?.is_external === true) return true
  if (['external', 'external_candidate', 'candidate'].includes(itemType)) return true
  return !item?.id && Boolean(resolvePrimaryUrl(item))
}

export const resolveSourceLabel = (item) => {
  const explicit = String(item?.source_label || item?.source_platform_label || item?.external_source_label || item?.platform_label || '').trim()
  if (explicit) return explicit
  if (isExternalItem(item)) return '站外候选'
  return String(item?.upload_source_label || '站内视频')
}

export const formatRecommendationTime = (rawValue) => {
  if (!rawValue) return ''
  const date = new Date(rawValue)
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleString()
}

/**
 * 将 API item 转为卡片展示模型（不读取 summary/reason_text/tags 作为正文）。
 */
export const decorateRecommendationListItem = (item, index = 0) => {
  const tags = Array.isArray(item?.tags) ? item.tags.filter(Boolean).map((tag) => String(tag).trim()) : []
  const sourceLabel = resolveSourceLabel(item)
  const isExternal = isExternalItem(item)
  const actionLabel = String(item?.action_label || '').trim()
  const importHint = String(item?.import_hint || '').trim()
  const subjectText = String(item?.subject || '').trim()
  return {
    ...item,
    key: resolveItemKey(item, index),
    title: String(item?.title || '未命名内容'),
    tags,
    reasonLabel: String(item?.reason_label || '推荐'),
    statusText: item?.status ? videoStatusText(item.status) : '',
    timeText: formatRecommendationTime(item?.upload_time || item?.updated_at || item?.created_at),
    sourceLabel,
    sourceBadgeClass: isExternal ? 'badge--external' : 'badge--soft',
    primaryActionLabel: actionLabel || (isExternal ? '导入学习' : '打开详情'),
    primaryActionDisabled: isRecommendationPrimaryActionDisabled(item, isExternal),
    canImport: Boolean(item?.can_import ?? false),
    importHint,
    actionTarget: String(item?.action_target || '').trim(),
    actionApi: String(item?.action_api || '').trim(),
    actionMethod: String(item?.action_method || '').trim().toUpperCase(),
    subjectText: subjectText ? `科目 · ${subjectText}` : '',
    clusterKey: String(item?.cluster_key || '').trim(),
    /** @type {boolean} */
    isExternal
  }
}

/**
 * 解析推荐项的路由或站外打开（与 Recommendations.vue 行为一致）。
 * @returns {{ type: 'route', location } | { type: 'external', url } | { type: 'none', message?: string }}
 */
export const resolveRecommendationNavigation = (item) => {
  const actionLocation = parseRecommendationActionTarget(item?.actionTarget || item?.action_target)
  if (actionLocation) return { type: 'route', location: actionLocation }

  if (isExternalItem(item) && !shouldOpenRecommendationExternalSource(item)) {
    const url = resolvePrimaryUrl(item)
    if (!url) return { type: 'none', message: item?.import_hint || '当前站外候选暂不可直接导入。' }
    return {
      type: 'route',
      location: { path: '/upload', query: { mode: 'url', url, source: resolveSourceLabel(item) || '站外推荐' } }
    }
  }

  if (item.id) return { type: 'route', location: `/videos/${item.id}` }

  if (shouldOpenRecommendationExternalSource(item)) {
    const externalTarget = String(item?.actionTarget || item?.action_target || '').trim() || resolvePrimaryUrl(item)
    if (externalTarget) return { type: 'external', url: externalTarget }
  }

  return { type: 'none', message: '当前推荐项缺少可用的跳转动作。' }
}
