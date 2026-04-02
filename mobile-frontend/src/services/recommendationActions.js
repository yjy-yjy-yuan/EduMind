const ABSOLUTE_HTTP_URL_RE = /^https?:\/\//i

export const resolveRecommendationUrl = (item) =>
  String(item?.external_url || item?.target_url || item?.source_url || item?.link || item?.url || '').trim()

export const parseRecommendationActionTarget = (target) => {
  const text = String(target || '').trim()
  if (!text || !text.startsWith('/')) return null
  const [path, search = ''] = text.split('?')
  if (!search) return { path }
  const query = {}
  new URLSearchParams(search).forEach((value, key) => {
    query[key] = value
  })
  return { path, query }
}

export const isAbsoluteHttpUrl = (value) => ABSOLUTE_HTTP_URL_RE.test(String(value || '').trim())

export const shouldOpenRecommendationExternalSource = (item) => {
  const actionType = String(item?.action_type || item?.actionType || '').trim().toLowerCase()
  const actionTarget = String(item?.action_target || item?.actionTarget || '').trim()
  const fallbackUrl = resolveRecommendationUrl(item)
  if (actionType === 'open_external_source') {
    return isAbsoluteHttpUrl(actionTarget) || isAbsoluteHttpUrl(fallbackUrl)
  }
  return item?.can_import === false && (isAbsoluteHttpUrl(actionTarget) || isAbsoluteHttpUrl(fallbackUrl))
}

export const isRecommendationPrimaryActionDisabled = (item, isExternal) => {
  if (!isExternal) return false
  if (shouldOpenRecommendationExternalSource(item)) return false
  return !Boolean(resolveRecommendationUrl(item))
}
