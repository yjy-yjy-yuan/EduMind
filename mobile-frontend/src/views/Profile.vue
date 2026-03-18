<template>
  <div class="page">
    <header class="topbar">
      <h2>我的</h2>
      <button class="link" @click="refresh" :disabled="loading">{{ loading ? '…' : '刷新' }}</button>
    </header>

    <div class="card">
      <div class="user">
        <div class="avatar">{{ avatarText }}</div>
        <div class="info">
          <div class="username">{{ state.user?.username || '用户' }}</div>
          <div class="email">{{ state.user?.email || '—' }}</div>
        </div>
      </div>

      <button class="btn" @click="go('/videos')">我的视频</button>
      <button class="btn" @click="go('/notes')">我的笔记</button>
      <button class="danger" @click="doLogout" :disabled="loading">退出登录</button>
    </div>

    <div class="card card--muted">
      <div class="card-title">处理设置</div>
      <p class="muted" style="margin: 0 0 8px; font-size: 12px;">这些设置会用于新上传视频、详情页重新处理，以及失败任务重试。</p>
      <label class="field">
        <span class="field-label">识别语言</span>
        <select v-model="processingForm.language" class="input">
          <option v-for="option in LANGUAGE_OPTIONS" :key="option.value" :value="option.value">{{ option.label }}</option>
        </select>
      </label>
      <label class="field">
        <span class="field-label">Whisper 模型</span>
        <select v-model="processingForm.model" class="input">
          <option v-for="option in whisperModelOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
        </select>
        <div class="field-help">当前优势：{{ currentModelHighlight }}</div>
      </label>
      <label class="field">
        <span class="field-label">摘要风格</span>
        <select v-model="processingForm.summaryStyle" class="input">
          <option v-for="option in SUMMARY_STYLE_OPTIONS" :key="option.value" :value="option.value">{{ option.label }}</option>
        </select>
      </label>
      <label class="toggle">
        <input v-model="processingForm.autoGenerateSummary" type="checkbox" />
        <span>处理完成后自动生成摘要</span>
      </label>
      <label class="toggle">
        <input v-model="processingForm.autoGenerateTags" type="checkbox" />
        <span>处理完成后自动提取标签</span>
      </label>
      <div class="row-actions">
        <button class="btn btn--small" @click="saveProcessing" :disabled="savingProcessing">
          {{ savingProcessing ? '已保存' : '保存处理设置' }}
        </button>
        <button class="btn btn--ghost btn--small" @click="resetProcessingDefaults">恢复默认</button>
      </div>
    </div>

    <div class="card card--muted">
      <div class="card-title">开发设置</div>
      <p class="muted" style="margin: 0 0 8px; font-size: 12px;">真机默认会优先使用原生注入的后端地址。若你修改了后端地址或端口，可在此覆盖当前值（例如 {{ suggestedApiBase }}）。</p>
      <input v-model.trim="apiBaseInput" class="input" :placeholder="apiBasePlaceholder" style="margin-bottom: 8px;" />
      <button class="btn btn--small" @click="saveApiBase" :disabled="saving">{{ saving ? '已保存' : '保存后端地址' }}</button>
    </div>

    <div v-if="error" class="alert alert--bad">{{ error }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getApiBaseUrl, setApiBaseUrl } from '@/config'
import { getVideoProcessingOptions } from '@/api/video'
import {
  LANGUAGE_OPTIONS,
  PROCESSING_DEFAULTS,
  SUMMARY_STYLE_OPTIONS,
  getProcessingSettings,
  getWhisperModelOptions,
  saveProcessingSettings,
  saveWhisperModelCatalog,
  whisperModelHighlight
} from '@/services/processingSettings'
import * as authStore from '@/store/auth'

const router = useRouter()
const apiBaseInput = ref(getApiBaseUrl())
const saving = ref(false)
const savingProcessing = ref(false)
const processingForm = ref(getProcessingSettings())
const whisperModelOptions = ref(getWhisperModelOptions())
const state = computed(() => authStore.getState())
const loading = ref(false)
const error = ref('')

const avatarText = computed(() => String(state.value.user?.username || 'U').slice(0, 1).toUpperCase())
const currentModelHighlight = computed(() => whisperModelHighlight(processingForm.value.model))
const suggestedApiBase = computed(() => {
  try {
    const nativeValue = window.__edumindNativeConfig?.apiBaseUrl
    return apiBaseInput.value || getApiBaseUrl() || (nativeValue ? String(nativeValue).trim() : '') || 'http://<Mac主机名>.local:<后端端口>'
  } catch {
    return apiBaseInput.value || getApiBaseUrl() || 'http://<Mac主机名>.local:<后端端口>'
  }
})
const apiBasePlaceholder = computed(() => suggestedApiBase.value || 'http://<Mac主机名>.local:<后端端口>')
const go = (path) => router.push(path)

const refresh = async () => {
  loading.value = true
  error.value = ''
  try {
    await authStore.fetchMe()
  } catch (e) {
    error.value = e?.message || '刷新失败'
  } finally {
    loading.value = false
  }
}

const doLogout = async () => {
  loading.value = true
  error.value = ''
  try {
    await authStore.logout()
    router.replace('/login')
  } catch (e) {
    error.value = e?.message || '退出失败'
  } finally {
    loading.value = false
  }
}

const saveApiBase = () => {
  const url = apiBaseInput.value
  setApiBaseUrl(url || '')
  saving.value = true
  setTimeout(() => { saving.value = false }, 1500)
}

const saveProcessing = () => {
  processingForm.value = saveProcessingSettings(processingForm.value)
  savingProcessing.value = true
  setTimeout(() => { savingProcessing.value = false }, 1500)
}

const refreshWhisperModelOptions = async () => {
  try {
    const res = await getVideoProcessingOptions()
    const catalog = saveWhisperModelCatalog(res?.data || {})
    whisperModelOptions.value = catalog.options
    processingForm.value = saveProcessingSettings(processingForm.value)
  } catch {
    whisperModelOptions.value = getWhisperModelOptions()
    processingForm.value = saveProcessingSettings(processingForm.value)
  }
}

const resetProcessingDefaults = () => {
  processingForm.value = saveProcessingSettings(PROCESSING_DEFAULTS)
  savingProcessing.value = true
  setTimeout(() => { savingProcessing.value = false }, 1500)
}

watch(
  () => processingForm.value.autoGenerateTags,
  (enabled) => {
    if (enabled) processingForm.value.autoGenerateSummary = true
  }
)

watch(
  () => processingForm.value.autoGenerateSummary,
  (enabled) => {
    if (!enabled) processingForm.value.autoGenerateTags = false
  }
)

onMounted(() => {
  apiBaseInput.value = getApiBaseUrl()
  processingForm.value = getProcessingSettings()
  refreshWhisperModelOptions()
  refresh()
})
</script>

<style scoped>
.page {
  max-width: 520px;
  margin: 0 auto;
  padding: 16px 16px 0;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.topbar h2 {
  margin: 0;
  font-size: 16px;
}

.link {
  border: 0;
  background: transparent;
  color: var(--primary);
  font-weight: 900;
}

.card {
  background: var(--card);
  border-radius: var(--radius);
  padding: 14px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  display: grid;
  gap: 10px;
}

.card--muted {
  background: rgba(0, 0, 0, 0.03);
  border-color: rgba(0, 0, 0, 0.06);
}

.card-title {
  font-weight: 700;
  font-size: 14px;
  margin-bottom: 4px;
}

.btn--small {
  padding: 8px 12px;
  font-size: 13px;
}

.btn--ghost {
  background: transparent;
}

.field {
  display: grid;
  gap: 6px;
}

.field-label {
  font-size: 12px;
  color: var(--muted);
  font-weight: 700;
}

.field-help {
  font-size: 12px;
  line-height: 1.55;
  color: var(--muted);
  overflow-wrap: anywhere;
  word-break: break-word;
}

.input {
  width: 100%;
  border-radius: 14px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: #fff;
  padding: 12px;
  font: inherit;
}

.toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  font-weight: 700;
}

.toggle input {
  width: 18px;
  height: 18px;
}

.row-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.user {
  display: flex;
  gap: 10px;
  align-items: center;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.avatar {
  height: 42px;
  width: 42px;
  border-radius: 14px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 900;
}

.username {
  font-weight: 900;
}

.email {
  font-size: 12px;
  color: var(--muted);
}

.btn {
  border-radius: 14px;
  padding: 12px;
  font-weight: 900;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: #fff;
}

.danger {
  border: 0;
  border-radius: 14px;
  padding: 12px;
  font-weight: 900;
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
}

.danger:disabled {
  opacity: 0.6;
}

.alert {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  font-weight: 800;
}

.alert--bad { background: rgba(239, 68, 68, 0.12); color: #b91c1c; }
</style>
<style scoped>
.page {
  padding-top: calc(14px + env(safe-area-inset-top));
}

.topbar {
  padding: 12px 14px;
  border-radius: 18px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 22px rgba(24, 45, 73, 0.09);
}

.topbar h2 {
  font-size: 18px;
}

.card {
  margin-top: 12px;
  border-radius: 24px;
  padding: 16px;
  background: linear-gradient(180deg, #ffffff, #f8fbfd);
}

.avatar {
  border-radius: 16px;
  background: linear-gradient(145deg, #1f7a8c, #3d8da0);
}

.btn {
  border-radius: 16px;
}

.danger {
  border-radius: 16px;
}
</style>
