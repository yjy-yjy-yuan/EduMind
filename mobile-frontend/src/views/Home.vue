<template>
  <div class="page">
    <header class="hero">
      <div class="title">视频智能伴学</div>
      <div class="subtitle">移动端</div>
    </header>

    <button class="guide-dock" @click="go('/guide')" aria-label="打开使用指南">
      <span class="guide-dock__icon">?</span>
      <span class="guide-dock__text">指南</span>
    </button>

    <section class="grid">
      <button class="card" @click="go('/videos')">
        <div class="card-title">视频</div>
        <div class="card-desc">查看与处理进度</div>
      </button>
      <button class="card" @click="go('/upload')">
        <div class="card-title">上传</div>
        <div class="card-desc">本地/链接上传</div>
      </button>
      <button class="card" @click="go('/notes')">
        <div class="card-title">笔记</div>
        <div class="card-desc">记录与整理</div>
      </button>
      <button class="card" @click="go('/qa')">
        <div class="card-title">问答</div>
        <div class="card-desc">AI 辅助学习</div>
      </button>
      <button class="card" @click="go('/knowledge')">
        <div class="card-title">知识点</div>
        <div class="card-desc">概念与关系总览</div>
      </button>
      <button class="card" @click="go('/learning-path')">
        <div class="card-title">路径</div>
        <div class="card-desc">学习规划建议</div>
      </button>
    </section>

    <section class="section">
      <div class="section-head">
        <h3>最近视频</h3>
        <button class="link" @click="reload" :disabled="loading">{{ loading ? '加载中…' : '刷新' }}</button>
      </div>

      <div v-if="error" class="alert alert--bad">
        <span>{{ error }}</span>
        <button class="link" @click="reload">重试</button>
      </div>

      <div v-else-if="loading" class="skeleton">
        <div v-for="i in 3" :key="i" class="sk-item"></div>
      </div>

      <div v-else-if="videos.length === 0" class="empty">暂无视频，去上传一个吧。</div>

      <div v-else class="list">
        <button v-for="v in videos" :key="v.id" class="item" @click="go(`/videos/${v.id}`)">
          <div class="item-title">{{ v.title || '未命名视频' }}</div>
          <span class="badge" :class="badgeClass(v.status)">{{ statusText(v.status) }}</span>
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getVideoList } from '@/api/video'

const router = useRouter()
const go = (path) => router.push(path)

const loading = ref(false)
const error = ref('')
const videos = ref([])

const normalizeList = (payload) => {
  const list = payload?.videos || payload?.items || payload?.data || payload || []
  return Array.isArray(list) ? list : []
}

const reload = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await getVideoList(1, 3)
    videos.value = normalizeList(res.data)
  } catch (e) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const statusText = (status) => {
  const map = {
    uploaded: '已上传',
    pending: '排队中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
    downloading: '下载中',
    processed: '已完成'
  }
  return map[status] || (status || '未知')
}

const badgeClass = (status) => {
  if (status === 'completed' || status === 'processed') return 'ok'
  if (status === 'failed') return 'bad'
  if (['processing', 'pending', 'downloading'].includes(status)) return 'warn'
  return 'info'
}

onMounted(reload)
</script>

<style scoped>
.page {
  max-width: 520px;
  margin: 0 auto;
  padding: 16px 16px 0;
}

.hero {
  padding: 14px;
  border-radius: var(--radius);
  color: #fff;
  background: linear-gradient(135deg, #667eea, #764ba2);
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.25);
}

.title {
  font-size: 18px;
  font-weight: 900;
}

.subtitle {
  margin-top: 6px;
  font-size: 12px;
  opacity: 0.9;
}

.grid {
  margin-top: 14px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.guide-dock {
  position: fixed;
  left: 10px;
  top: calc(92px + env(safe-area-inset-top));
  z-index: 50;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  box-shadow: var(--shadow-sm);
  border-radius: 999px;
  padding: 10px 12px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.guide-dock__icon {
  height: 22px;
  width: 22px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: rgba(79, 70, 229, 0.12);
  color: var(--primary);
  font-weight: 900;
  line-height: 1;
}

.guide-dock__text {
  font-weight: 900;
  font-size: 12px;
  color: var(--text);
}

.card {
  border: 0;
  text-align: left;
  padding: 14px;
  border-radius: var(--radius);
  background: var(--card);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
}

.card-title {
  font-weight: 900;
}

.card-desc {
  margin-top: 6px;
  font-size: 12px;
  color: var(--muted);
}

.section {
  margin-top: 14px;
  background: var(--card);
  border-radius: var(--radius);
  padding: 14px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-head h3 {
  margin: 0;
  font-size: 14px;
}

.link {
  border: 0;
  background: transparent;
  color: var(--primary);
  font-weight: 800;
}

.alert {
  margin-top: 12px;
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
  margin-top: 12px;
  display: grid;
  gap: 10px;
}

.sk-item {
  height: 46px;
  border-radius: 12px;
  background: linear-gradient(90deg, #f3f4f6, #e5e7eb, #f3f4f6);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
}

@keyframes shimmer {
  0% { background-position: 0% 0; }
  100% { background-position: 200% 0; }
}

.empty {
  margin-top: 12px;
  color: var(--muted);
  font-size: 13px;
}

.list {
  margin-top: 12px;
  display: grid;
  gap: 10px;
}

.item {
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  text-align: left;
}

.item-title {
  font-size: 13px;
  font-weight: 800;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  white-space: nowrap;
}

.badge.ok { background: rgba(34, 197, 94, 0.12); color: #15803d; }
.badge.warn { background: rgba(245, 158, 11, 0.14); color: #92400e; }
.badge.bad { background: rgba(239, 68, 68, 0.12); color: #b91c1c; }
.badge.info { background: rgba(99, 102, 241, 0.12); color: #3730a3; }
</style>
