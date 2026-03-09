<template>
  <div class="page">
    <header class="topbar">
      <h2>学习路径</h2>
      <button class="link" @click="refresh">刷新</button>
    </header>

    <div class="card">
      <div class="card-title">推荐路径（布局）</div>
      <div class="muted">该页仅实现移动端固定布局；推荐数据由移动应用后端通过接口提供。</div>
    </div>

    <div class="list">
      <div class="step" v-for="(s, i) in steps" :key="i">
        <div class="badge">{{ i + 1 }}</div>
        <div class="content">
          <div class="title">{{ s.title }}</div>
          <div class="muted">{{ s.desc }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const steps = ref([
  { title: '上传学习视频', desc: '导入课程视频，等待字幕/摘要/标签生成。' },
  { title: '观看与提问', desc: '边看边问，快速澄清知识点与疑惑。' },
  { title: '记录笔记', desc: '把关键结论整理成笔记，便于复习。' },
  { title: '知识点总览', desc: '汇总本次学习的核心概念与关系。' }
])

const refresh = () => {
  // 占位：后续接入移动端后端推荐结果
}
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
  gap: 8px;
}

.card-title {
  font-weight: 900;
  font-size: 13px;
}

.muted {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.6;
}

.list {
  margin-top: 12px;
  display: grid;
  gap: 10px;
}

.step {
  background: var(--card);
  border-radius: var(--radius);
  padding: 12px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  display: grid;
  grid-template-columns: 32px 1fr;
  gap: 10px;
}

.badge {
  height: 28px;
  width: 28px;
  border-radius: 10px;
  background: rgba(79, 70, 229, 0.10);
  color: var(--primary);
  display: grid;
  place-items: center;
  font-weight: 900;
}

.title {
  font-weight: 900;
  font-size: 13px;
}
</style>
