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

    <div v-else class="content">
      <section v-if="showStack" class="stack-section">
        <div class="section-head">
          <div>
            <div class="section-title">最近笔记堆叠</div>
            <div class="section-tip">已创建 {{ notes.length }} 条笔记，点击任意卡片继续编辑</div>
          </div>
        </div>

        <div class="stack-shell" :style="{ height: `${stackHeight}px` }">
          <button
            v-for="(n, index) in stackNotes"
            :key="n.id"
            class="stack-card"
            :class="{ 'stack-card--top': index === 0 }"
            :style="stackStyle(index)"
            @click="go(`/notes/${n.id}`)"
          >
            <div class="stack-card__glow"></div>
            <div class="stack-card__body">
              <div class="stack-card__meta">
                <span class="stack-card__badge">笔记 {{ stackNotes.length - index }}</span>
                <span class="stack-card__time">{{ formatTime(n.updated_at || n.created_at) }}</span>
              </div>
              <div class="stack-card__title">{{ n.title || '未命名笔记' }}</div>
              <div class="stack-card__preview">{{ previewText(n.content) }}</div>
            </div>
          </button>
        </div>
      </section>

      <div class="section-head section-head--list">
        <div class="section-title">全部笔记</div>
        <div class="section-tip">按最近更新时间排序</div>
      </div>

      <div class="list">
        <button v-for="n in notes" :key="n.id" class="card" @click="go(`/notes/${n.id}`)">
          <div class="row">
            <div class="title">{{ n.title || '未命名笔记' }}</div>
            <i class="arrow">›</i>
          </div>
          <div class="muted">{{ formatTime(n.updated_at || n.created_at) }}</div>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
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

const sortNotes = (list) => {
  return [...list].sort((a, b) => {
    const aTime = new Date(a?.updated_at || a?.created_at || 0).getTime()
    const bTime = new Date(b?.updated_at || b?.created_at || 0).getTime()
    return bTime - aTime
  })
}

const showStack = computed(() => notes.value.length >= 2)
const stackNotes = computed(() => notes.value.slice(0, 3))
const stackHeight = computed(() => 212 + Math.max(stackNotes.value.length - 1, 0) * 34)

const stackStyle = (index) => ({
  transform: `translateY(${index * 34}px) scale(${1 - index * 0.04}) rotate(${index * 1.5}deg)`,
  zIndex: stackNotes.value.length - index
})

const reload = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await getNotes()
    notes.value = sortNotes(normalizeList(res.data))
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

const previewText = (content) => {
  const text = String(content || '').replace(/\s+/g, ' ').trim()
  return text || '记录灵感、提炼重点，下一次打开时从这里继续。'
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

.content {
  display: grid;
  gap: 16px;
}

.stack-section {
  border-radius: 24px;
  padding: 16px;
  background:
    radial-gradient(circle at top left, rgba(99, 102, 241, 0.18), transparent 42%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.98));
  border: 1px solid rgba(99, 102, 241, 0.12);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.section-head--list {
  margin-top: 2px;
}

.section-title {
  font-size: 14px;
  font-weight: 900;
  color: #0f172a;
}

.section-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #64748b;
}

.stack-shell {
  position: relative;
  margin-top: 14px;
}

.stack-card {
  position: absolute;
  inset: 0;
  width: 100%;
  border: 0;
  padding: 0;
  text-align: left;
  border-radius: 22px;
  overflow: hidden;
  transform-origin: center top;
  background: transparent;
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.stack-card--top {
  box-shadow: 0 20px 36px rgba(79, 70, 229, 0.18);
}

.stack-card:active {
  transform: translateY(2px) scale(0.99);
}

.stack-card__glow {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.38), transparent 34%),
    linear-gradient(135deg, #6366f1, #8b5cf6 56%, #06b6d4);
}

.stack-card__body {
  position: relative;
  min-height: 212px;
  padding: 18px;
  color: #fff;
  display: grid;
  align-content: space-between;
  gap: 18px;
}

.stack-card__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.stack-card__badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.18);
  font-size: 11px;
  font-weight: 800;
}

.stack-card__time {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.82);
}

.stack-card__title {
  font-size: 18px;
  font-weight: 900;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.stack-card__preview {
  font-size: 13px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.92);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
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
<style scoped>
.page {
  padding-top: calc(14px + env(safe-area-inset-top));
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 5;
  padding: 12px 14px;
  border-radius: 18px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 22px rgba(24, 45, 73, 0.09);
}

.topbar h2 {
  font-size: 18px;
}

.stack-section {
  border-radius: 24px;
  border-color: rgba(31, 122, 140, 0.12);
  background:
    radial-gradient(circle at 12% 0%, rgba(31, 122, 140, 0.14), transparent 46%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(247, 251, 254, 0.98));
}

.stack-card__glow {
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.34), transparent 34%),
    linear-gradient(145deg, #1f7a8c, #3d8da0 58%, #eb8c34);
}

.card {
  border-radius: 18px;
  border-color: rgba(32, 42, 55, 0.08);
  background: linear-gradient(180deg, #ffffff, #f9fbfd);
}
</style>
