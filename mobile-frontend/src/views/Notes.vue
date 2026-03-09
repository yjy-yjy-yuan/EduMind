<template>
  <div class="page">
    <header class="topbar">
      <h2>笔记</h2>
      <div class="actions">
        <button class="link" @click="reload" :disabled="loading">{{ loading ? '…' : '刷新' }}</button>
        <button class="link" @click="go('/notes/new')">新建</button>
      </div>
    </header>

    <div v-if="error" class="alert alert--bad">
      <span>{{ error }}</span>
      <button class="link" @click="reload">重试</button>
    </div>

    <div v-else-if="loading && notes.length === 0" class="skeleton">
      <div v-for="i in 6" :key="i" class="sk-card"></div>
    </div>

    <div v-else-if="notes.length === 0" class="empty">暂无笔记。</div>

    <div v-else class="list">
      <button v-for="n in notes" :key="n.id" class="card" @click="go(`/notes/${n.id}`)">
        <div class="row">
          <div class="title">{{ n.title || '未命名笔记' }}</div>
          <i class="arrow">›</i>
        </div>
        <div class="muted">{{ formatTime(n.updated_at || n.created_at) }}</div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getNotes } from '@/api/note'

const router = useRouter()
const go = (path) => router.push(path)

const loading = ref(false)
const error = ref('')
const notes = ref([])

const normalizeList = (payload) => {
  const list = payload?.notes || payload?.items || payload?.data || payload || []
  return Array.isArray(list) ? list : []
}

const reload = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await getNotes()
    notes.value = normalizeList(res.data)
  } catch (e) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const formatTime = (t) => {
  if (!t) return ''
  try {
    const d = new Date(t)
    if (Number.isNaN(d.getTime())) return String(t)
    return d.toLocaleString()
  } catch {
    return String(t)
  }
}

onMounted(reload)
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

.actions {
  display: flex;
  gap: 10px;
}

.link {
  border: 0;
  background: transparent;
  color: var(--primary);
  font-weight: 900;
}

.alert {
  padding: 10px 12px;
  border-radius: 12px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-weight: 700;
}

.alert--bad {
  background: rgba(239, 68, 68, 0.10);
  color: #b91c1c;
}

.skeleton {
  display: grid;
  gap: 10px;
}

.sk-card {
  height: 84px;
  border-radius: var(--radius);
  background: linear-gradient(90deg, #f3f4f6, #e5e7eb, #f3f4f6);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
}

@keyframes shimmer {
  0% { background-position: 0% 0; }
  100% { background-position: 200% 0; }
}

.empty {
  color: var(--muted);
  font-size: 13px;
}

.list {
  display: grid;
  gap: 10px;
}

.card {
  border: 0;
  text-align: left;
  padding: 14px;
  border-radius: var(--radius);
  background: var(--card);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  display: grid;
  gap: 8px;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.title {
  font-size: 14px;
  font-weight: 900;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.arrow {
  color: #9ca3af;
  font-style: normal;
  font-size: 22px;
}

.muted {
  color: var(--muted);
  font-size: 12px;
}
</style>
