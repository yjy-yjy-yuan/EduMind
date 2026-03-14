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

    <div v-if="error" class="alert alert--bad">{{ error }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as authStore from '@/store/auth'

const router = useRouter()
const state = computed(() => authStore.getState())
const loading = ref(false)
const error = ref('')

const avatarText = computed(() => String(state.value.user?.username || 'U').slice(0, 1).toUpperCase())
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

onMounted(() => {
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
