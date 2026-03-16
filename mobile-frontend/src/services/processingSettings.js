import { storageGet, storageSet } from '@/utils/storage'

const STORAGE_KEY = 'm_processing_settings'

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
  { value: 'turbo', label: 'turbo' }
])

export const LANGUAGE_OPTIONS = Object.freeze([
  { value: 'Other', label: '中文/其他' },
  { value: 'English', label: '英文' }
])

const ALLOWED_MODELS = new Set(WHISPER_MODEL_OPTIONS.map((item) => item.value))
const ALLOWED_LANGUAGES = new Set(LANGUAGE_OPTIONS.map((item) => item.value))
const ALLOWED_SUMMARY_STYLES = new Set(SUMMARY_STYLE_OPTIONS.map((item) => item.value))

const toBool = (value, fallback) => {
  if (typeof value === 'boolean') return value
  const text = String(value ?? '').trim().toLowerCase()
  if (!text) return fallback
  if (['1', 'true', 'yes', 'on'].includes(text)) return true
  if (['0', 'false', 'no', 'off'].includes(text)) return false
  return fallback
}

export const normalizeProcessingSettings = (input = {}) => {
  const raw = input || {}
  const next = {
    language: ALLOWED_LANGUAGES.has(String(raw.language || '').trim()) ? String(raw.language).trim() : PROCESSING_DEFAULTS.language,
    model: ALLOWED_MODELS.has(String(raw.model || '').trim()) ? String(raw.model).trim() : PROCESSING_DEFAULTS.model,
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
export const whisperModelLabel = (value) => WHISPER_MODEL_OPTIONS.find((item) => item.value === value)?.label || 'base'
export const languageLabel = (value) => LANGUAGE_OPTIONS.find((item) => item.value === value)?.label || '中文/其他'
