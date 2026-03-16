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
      <div class="card-title">开发设置</div>
      <p class="muted" style="margin: 0 0 8px; font-size: 12px;">真机默认会优先使用原生注入的后端地址。若你修改了后端地址或端口，可在此覆盖当前值（例如 {{ suggestedApiBase }}）。</p>
      <input v-model.trim="apiBaseInput" class="input" :placeholder="apiBasePlaceholder" style="margin-bottom: 8px;" />
      <button class="btn btn--small" @click="saveApiBase" :disabled="saving">{{ saving ? '已保存' : '保存后端地址' }}</button>
    </div>

    <div v-if="error" class="alert alert--bad">{{ error }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getApiBaseUrl, setApiBaseUrl } from '@/config'
import * as authStore from '@/store/auth'

const router = useRouter()
const apiBaseInput = ref(getApiBaseUrl())
const saving = ref(false)
const state = computed(() => authStore.getState())
const loading = ref(false)
const error = ref('')

const avatarText = computed(() => String(state.value.user?.username || 'U').slice(0, 1).toUpperCase())
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

onMounted(() => {
  apiBaseInput.value = getApiBaseUrl()
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
