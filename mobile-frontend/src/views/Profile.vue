<template>
  <div class="page">
    <header class="topbar">
      <h2>我的</h2>
      <button class="link" @click="refresh" :disabled="loading">{{ loading ? '…' : '刷新' }}</button>
    </header>

    <div class="card">
      <div class="user">
        <button class="avatar-shell avatar-trigger" type="button" @click="openAvatarPicker" :disabled="savingProfile">
          <img v-if="avatarUrl" :src="avatarUrl" alt="用户头像" class="avatar-image" />
          <div v-else class="avatar">{{ avatarText }}</div>
          <span class="avatar-badge">更换</span>
        </button>
        <div class="info">
          <div class="inline-editor inline-editor--compact">
            <input
              v-if="isEditingUsername"
              ref="usernameInput"
              v-model.trim="profileForm.username"
              class="input inline-editor__input inline-editor__input--compact"
              maxlength="64"
              placeholder="请输入用户名"
              :disabled="savingProfile"
              @keydown.enter.prevent="saveProfile"
            />
            <div v-else class="inline-editor__display inline-editor__display--compact">{{ state.user?.username || '用户' }}</div>
            <button
              class="icon-button icon-button--compact"
              type="button"
              @click="enableUsernameEditing"
              :disabled="savingProfile"
              aria-label="修改昵称"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true" class="icon-button__icon">
                <path d="M4 17.25V20h2.75l8.1-8.1-2.75-2.75-8.1 8.1zm12.71-9.04a1.003 1.003 0 0 0 0-1.42l-1.5-1.5a1.003 1.003 0 0 0-1.42 0l-1.17 1.17 2.75 2.75 1.34-1.17z" />
              </svg>
            </button>
          </div>
          <div class="email">{{ contactText }}</div>
          <div class="email">登录次数：{{ state.user?.login_count ?? 0 }}</div>
        </div>
      </div>

      <div class="profile-editor">
        <div class="card-title">资料设置</div>
        <div class="field">
          <span class="field-label">头像照片</span>
          <div class="field-help">
            {{ selectedAvatarFile ? `待上传：${selectedAvatarFile.name}` : '点击上方头像可更换照片；点击头像右侧昵称区域的修改图标后才可编辑昵称。' }}
          </div>
          <input
            ref="avatarInput"
            class="sr-only"
            type="file"
            accept="image/png,image/jpeg,image/webp,image/gif,image/heic,image/heif"
            @change="onAvatarSelected"
          />
        </div>

        <div class="row-actions">
          <button class="btn btn--small" @click="saveProfile" :disabled="savingProfile || !profileDirty">
            {{ savingProfile ? '保存中…' : '保存资料' }}
          </button>
          <button class="btn btn--ghost btn--small" @click="resetProfileForm" :disabled="savingProfile || !profileDirty">
            恢复当前值
          </button>
        </div>
      </div>

      <button class="btn" @click="go('/videos')">我的视频</button>
      <button class="btn" @click="go('/notes')">我的笔记</button>
      <button class="btn" @click="go('/design-assistant')">设计助手</button>
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
        <span class="field-label">iOS 离线识别语言/方言</span>
        <select v-model="processingForm.nativeLocale" class="input">
          <option v-for="option in NATIVE_LOCALE_OPTIONS" :key="option.value" :value="option.value">{{ option.label }}</option>
        </select>
        <div class="field-help">仅用于 iPhone 本地离线转录，不影响后端在线 Whisper 处理。</div>
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

    <div v-if="successMessage" class="alert alert--good">{{ successMessage }}</div>
    <div v-if="error" class="alert alert--bad">{{ error }}</div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getApiBaseUrl, setApiBaseUrl, withBase } from '@/config'
import { getVideoProcessingOptions } from '@/api/video'
import {
  LANGUAGE_OPTIONS,
  NATIVE_LOCALE_OPTIONS,
  PROCESSING_DEFAULTS,
  SUMMARY_STYLE_OPTIONS,
  getProcessingSettings,
  getWhisperModelOptions,
  saveProcessingSettings,
  saveWhisperModelCatalog,
  whisperModelHighlight
} from '@/services/processingSettings'
import * as authStore from '@/store/auth'

const MAX_AVATAR_SIZE = 5 * 1024 * 1024

const router = useRouter()
const apiBaseInput = ref(getApiBaseUrl())
const avatarInput = ref(null)
const usernameInput = ref(null)
const saving = ref(false)
const savingProcessing = ref(false)
const savingProfile = ref(false)
const isEditingUsername = ref(false)
const processingForm = ref(getProcessingSettings())
const whisperModelOptions = ref(getWhisperModelOptions())
const loading = ref(false)
const error = ref('')
const successMessage = ref('')
const selectedAvatarFile = ref(null)
const avatarPreviewUrl = ref('')
const profileForm = ref({ username: '' })
const state = computed(() => authStore.getState())

let avatarObjectUrl = ''

const displayedUsername = computed(() => String(profileForm.value.username || state.value.user?.username || '用户').trim() || '用户')
const avatarText = computed(() => displayedUsername.value.slice(0, 1).toUpperCase())
const contactText = computed(() => state.value.user?.email || state.value.user?.phone || '—')
const currentModelHighlight = computed(() => whisperModelHighlight(processingForm.value.model))
const avatarUrl = computed(() => {
  const value = String(avatarPreviewUrl.value || state.value.user?.avatar || '').trim()
  if (!value) return ''
  if (/^(data:|blob:|https?:\/\/)/i.test(value) || value.startsWith('//')) return value
  if (value.startsWith('/')) return withBase(value)
  return value
})
const profileDirty = computed(() => {
  const nextUsername = String(profileForm.value.username || '').trim()
  const currentUsername = String(state.value.user?.username || '').trim()
  return nextUsername !== currentUsername || Boolean(selectedAvatarFile.value)
})
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

const parseErrorMessage = (e, fallback) => e?.response?.data?.detail || e?.message || fallback

const syncProfileForm = () => {
  profileForm.value = {
    username: state.value.user?.username || ''
  }
}

const clearAvatarSelection = () => {
  if (avatarObjectUrl) {
    URL.revokeObjectURL(avatarObjectUrl)
    avatarObjectUrl = ''
  }
  avatarPreviewUrl.value = ''
  selectedAvatarFile.value = null
  if (avatarInput.value) avatarInput.value.value = ''
}

const refresh = async () => {
  loading.value = true
  error.value = ''
  successMessage.value = ''
  try {
    const res = await authStore.fetchMe()
    if (res?.success) syncProfileForm()
  } catch (e) {
    error.value = parseErrorMessage(e, '刷新失败')
  } finally {
    loading.value = false
  }
}

const doLogout = async () => {
  loading.value = true
  error.value = ''
  successMessage.value = ''
  try {
    await authStore.logout()
    clearAvatarSelection()
    router.replace('/login')
  } catch (e) {
    error.value = parseErrorMessage(e, '退出失败')
  } finally {
    loading.value = false
  }
}

const openAvatarPicker = () => {
  if (savingProfile.value) return
  avatarInput.value?.click()
}

const enableUsernameEditing = async () => {
  if (savingProfile.value) return
  isEditingUsername.value = true
  error.value = ''
  successMessage.value = ''
  await nextTick()
  usernameInput.value?.focus()
  usernameInput.value?.select?.()
}

const onAvatarSelected = (event) => {
  const file = event?.target?.files?.[0]
  if (!file) return

  error.value = ''
  successMessage.value = ''

  if (!String(file.type || '').startsWith('image/')) {
    error.value = '请选择图片格式的头像文件'
    if (avatarInput.value) avatarInput.value.value = ''
    return
  }
  if (Number(file.size || 0) > MAX_AVATAR_SIZE) {
    error.value = '头像大小不能超过 5MB'
    if (avatarInput.value) avatarInput.value.value = ''
    return
  }

  clearAvatarSelection()
  selectedAvatarFile.value = file
  avatarObjectUrl = URL.createObjectURL(file)
  avatarPreviewUrl.value = avatarObjectUrl
}

const resetProfileForm = () => {
  error.value = ''
  successMessage.value = ''
  isEditingUsername.value = false
  syncProfileForm()
  clearAvatarSelection()
}

const saveProfile = async () => {
  const nextUsername = String(profileForm.value.username || '').trim()
  if (!nextUsername) {
    error.value = '用户名不能为空'
    return
  }

  savingProfile.value = true
  error.value = ''
  successMessage.value = ''

  try {
    if (nextUsername !== String(state.value.user?.username || '').trim()) {
      await authStore.updateProfile({ username: nextUsername })
    }

    if (selectedAvatarFile.value) {
      await authStore.uploadAvatar(selectedAvatarFile.value)
    }

    isEditingUsername.value = false
    syncProfileForm()
    clearAvatarSelection()
    successMessage.value = '资料已保存'
  } catch (e) {
    error.value = parseErrorMessage(e, '资料保存失败')
  } finally {
    savingProfile.value = false
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
  syncProfileForm()
  refreshWhisperModelOptions()
  refresh()
})

onBeforeUnmount(() => {
  clearAvatarSelection()
})
</script>

<style scoped>
.page {
  max-width: 520px;
  margin: 0 auto;
  padding: calc(14px + env(safe-area-inset-top)) 16px 0;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding: 12px 14px;
  border-radius: 18px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: rgba(242, 235, 248, 0.92);
  box-shadow: 0 10px 22px rgba(101, 87, 117, 0.09);
}

.topbar h2 {
  margin: 0;
  font-size: 18px;
}

.link {
  border: 0;
  background: transparent;
  color: var(--primary);
  font-weight: 900;
}

.card {
  margin-top: 12px;
  display: grid;
  gap: 10px;
  border-radius: 24px;
  padding: 16px;
  background: linear-gradient(180deg, rgba(242, 235, 248, 0.98), rgba(242, 235, 248, 0.95));
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
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
  align-items: center;
}

.row-actions--profile {
  justify-content: space-between;
}

.user {
  display: flex;
  gap: 10px;
  align-items: center;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.avatar-shell {
  position: relative;
  height: 72px;
  width: 72px;
  border-radius: 22px;
  overflow: hidden;
  background: rgba(139, 121, 157, 0.08);
  flex: 0 0 auto;
  padding: 0;
  border: 0;
}

.avatar-trigger {
  cursor: pointer;
}

.avatar-trigger:disabled {
  cursor: default;
  opacity: 0.7;
}

.avatar {
  height: 100%;
  width: 100%;
  display: grid;
  place-items: center;
  border-radius: 22px;
  background: linear-gradient(145deg, #8b799d, #a48eb5);
  color: #fff;
  font-size: 26px;
  font-weight: 900;
}

.avatar-image {
  display: block;
  height: 100%;
  width: 100%;
  object-fit: cover;
}

.avatar-badge {
  position: absolute;
  right: 6px;
  bottom: 6px;
  border-radius: 999px;
  padding: 2px 7px;
  background: rgba(17, 24, 39, 0.78);
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.info {
  min-width: 0;
  flex: 1;
  display: grid;
  gap: 6px;
}

.username {
  font-weight: 900;
  font-size: 16px;
}

.email {
  font-size: 12px;
  color: var(--muted);
}

.profile-editor {
  display: grid;
  gap: 10px;
}

.inline-editor {
  display: flex;
  align-items: center;
  gap: 8px;
}

.inline-editor--compact {
  align-items: stretch;
}

.inline-editor__input {
  flex: 1;
}

.inline-editor__display {
  flex: 1;
  min-height: 46px;
  border-radius: 14px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: #fff;
  padding: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
}

.inline-editor__input--compact,
.inline-editor__display--compact {
  min-height: 34px;
  padding: 6px 10px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 800;
}

.icon-button {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  border: 1px solid rgba(139, 121, 157, 0.18);
  background: rgba(139, 121, 157, 0.08);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #8b799d;
  flex: 0 0 auto;
}

.icon-button--compact {
  width: 34px;
  height: 34px;
  border-radius: 10px;
}

.icon-button__icon {
  width: 18px;
  height: 18px;
  fill: currentColor;
}

.btn {
  border-radius: 16px;
  padding: 12px;
  font-weight: 900;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: #fff;
}

.btn--small {
  padding: 8px 12px;
  font-size: 13px;
}

.btn--ghost {
  background: transparent;
}

.danger {
  border: 0;
  border-radius: 16px;
  padding: 12px;
  font-weight: 900;
  background: var(--lilac-bg);
  color: var(--lilac-text);
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

.alert--good {
  background: var(--ok-bg);
  color: var(--ok-text);
}

.alert--bad {
  background: var(--lilac-bg);
  color: var(--lilac-text);
}

.muted {
  color: var(--muted);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
