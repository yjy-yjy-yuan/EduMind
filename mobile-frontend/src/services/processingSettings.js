import { storageGet, storageSet } from '@/utils/storage'

const STORAGE_KEY = 'm_processing_settings'
const MODEL_CATALOG_STORAGE_KEY = 'm_whisper_model_catalog'

export const PROCESSING_DEFAULTS = Object.freeze({
  language: 'Other',
  model: 'base',
  autoGenerateSummary: true,
  autoGenerateTags: true,
  summaryStyle: 'study'
})

export const SUMMARY_STYLE_OPTIONS = Object.freeze([
  { value: 'brief', label: '简洁' },
  { value: 'study', label: '学习' },
  { value: 'detailed', label: '详细' }
])

export const WHISPER_MODEL_OPTIONS = Object.freeze([
  { value: 'tiny', label: 'tiny' },
  { value: 'base', label: 'base' },
  { value: 'small', label: 'small' },
  { value: 'medium', label: 'medium' },
  { value: 'large', label: 'large' },
  { value: 'turbo', label: 'turbo' }
])

export const WHISPER_MODEL_META = Object.freeze({
  tiny: {
    highlight: '最快，适合先验证上传和转录流程是否跑通。'
  },
  base: {
    highlight: '默认最稳，资源占用较低，适合日常使用。'
  },
  small: {
    highlight: '速度和准确率更平衡，适合作为常用升级档。'
  },
  medium: {
    highlight: '准确率更高，适合正式内容转录。'
  },
  large: {
    highlight: '效果最好，适合高质量要求场景。'
  },
  turbo: {
    highlight: '优先提速，适合想更快拿到初稿。'
  }
})

export const LANGUAGE_OPTIONS = Object.freeze([
  { value: 'Other', label: '中文/其他' },
  { value: 'English', label: '英文' }
])

const ALLOWED_LANGUAGES = new Set(LANGUAGE_OPTIONS.map((item) => item.value))
const ALLOWED_SUMMARY_STYLES = new Set(SUMMARY_STYLE_OPTIONS.map((item) => item.value))
const DEFAULT_MODEL_OPTIONS = WHISPER_MODEL_OPTIONS.map((item) => ({ ...item }))
const DEFAULT_MODEL_META = { ...WHISPER_MODEL_META }

const toBool = (value, fallback) => {
  if (typeof value === 'boolean') return value
  const text = String(value ?? '').trim().toLowerCase()
  if (!text) return fallback
  if (['1', 'true', 'yes', 'on'].includes(text)) return true
  if (['0', 'false', 'no', 'off'].includes(text)) return false
  return fallback
}

const normalizeModelCatalog = (input = {}) => {
  const raw = input || {}
  const sourceModels = Array.isArray(raw.models) ? raw.models : (Array.isArray(raw.options) ? raw.options : [])
  const normalizedModels = sourceModels
    .map((item) => ({
      value: String(item?.value || '').trim().toLowerCase(),
      label: String(item?.label || item?.value || '').trim().toLowerCase(),
      highlight: String(item?.highlight || '').trim(),
      downloaded: toBool(item?.downloaded, false)
    }))
    .filter((item) => item.value)

  const uniqueModels = []
  const seen = new Set()
  normalizedModels.forEach((item) => {
    if (seen.has(item.value)) return
    seen.add(item.value)
    uniqueModels.push(item)
  })

  const fallbackOptions = DEFAULT_MODEL_OPTIONS.map((item) => ({ ...item, downloaded: false }))
  const fallbackMeta = { ...DEFAULT_MODEL_META }
  const options = uniqueModels.length > 0 ? uniqueModels : fallbackOptions
  const meta = options.reduce((acc, item) => {
    acc[item.value] = {
      highlight: item.highlight || DEFAULT_MODEL_META[item.value]?.highlight || '适合当前视频处理场景。'
    }
    return acc
  }, {})
  const defaultModelCandidate = String(raw.default_model || raw.defaultModel || '').trim().toLowerCase()
  const optionValues = new Set(options.map((item) => item.value))
  const defaultModel = optionValues.has(defaultModelCandidate)
    ? defaultModelCandidate
    : (optionValues.has(PROCESSING_DEFAULTS.model) ? PROCESSING_DEFAULTS.model : options[0]?.value || PROCESSING_DEFAULTS.model)

  return {
    defaultModel,
    options,
    meta: Object.keys(meta).length > 0 ? meta : fallbackMeta
  }
}

export const getWhisperModelCatalog = () => {
  try {
    const raw = storageGet(MODEL_CATALOG_STORAGE_KEY)
    return normalizeModelCatalog(raw ? JSON.parse(raw) : {})
  } catch {
    return normalizeModelCatalog({})
  }
}

export const saveWhisperModelCatalog = (input = {}) => {
  const normalized = normalizeModelCatalog(input)
  storageSet(MODEL_CATALOG_STORAGE_KEY, JSON.stringify(normalized))
  return normalized
}

export const getWhisperModelOptions = () => getWhisperModelCatalog().options

const isAllowedModel = (value) => {
  const allowedModels = new Set(getWhisperModelOptions().map((item) => item.value))
  return allowedModels.has(String(value || '').trim().toLowerCase())
}

export const normalizeProcessingSettings = (input = {}) => {
  const raw = input || {}
  const modelCatalog = getWhisperModelCatalog()
  const next = {
    language: ALLOWED_LANGUAGES.has(String(raw.language || '').trim()) ? String(raw.language).trim() : PROCESSING_DEFAULTS.language,
    model: isAllowedModel(raw.model)
      ? String(raw.model).trim().toLowerCase()
      : modelCatalog.defaultModel,
    autoGenerateSummary: toBool(raw.autoGenerateSummary, PROCESSING_DEFAULTS.autoGenerateSummary),
    autoGenerateTags: toBool(raw.autoGenerateTags, PROCESSING_DEFAULTS.autoGenerateTags),
    summaryStyle: ALLOWED_SUMMARY_STYLES.has(String(raw.summaryStyle || '').trim()) ? String(raw.summaryStyle).trim() : PROCESSING_DEFAULTS.summaryStyle
  }

  if (next.autoGenerateTags) next.autoGenerateSummary = true
  return next
}

export const getProcessingSettings = () => {
  try {
    const raw = storageGet(STORAGE_KEY)
    return normalizeProcessingSettings(raw ? JSON.parse(raw) : PROCESSING_DEFAULTS)
  } catch {
    return { ...PROCESSING_DEFAULTS }
  }
}

export const saveProcessingSettings = (input = {}) => {
  const next = normalizeProcessingSettings(input)
  storageSet(STORAGE_KEY, JSON.stringify(next))
  return next
}

export const buildProcessPayload = (input = {}) => {
  const next = normalizeProcessingSettings(input)
  return {
    language: next.language,
    model: next.model,
    auto_generate_summary: next.autoGenerateSummary,
    auto_generate_tags: next.autoGenerateTags,
    summary_style: next.summaryStyle
  }
}

export const appendProcessingSettingsToFormData = (formData, input = {}) => {
  const payload = buildProcessPayload(input)
  Object.entries(payload).forEach(([key, value]) => {
    formData.append(key, String(value))
  })
  return formData
}

export const summaryStyleLabel = (value) => SUMMARY_STYLE_OPTIONS.find((item) => item.value === value)?.label || '学习'
export const whisperModelLabel = (value) => {
  const normalized = String(value || '').trim().toLowerCase()
  return getWhisperModelOptions().find((item) => item.value === normalized)?.label || 'base'
}
export const whisperModelHighlight = (value) => {
  const normalized = String(value || '').trim().toLowerCase()
  return getWhisperModelCatalog().meta[normalized]?.highlight || '适合当前视频处理场景。'
}
export const languageLabel = (value) => LANGUAGE_OPTIONS.find((item) => item.value === value)?.label || '中文/其他'
