<template>
  <div class="page">
    <header class="topbar">
      <h2>学习路径</h2>
      <button class="link" @click="refresh">刷新</button>
    </header>

    <div class="card">
      <div class="card-title">推荐路径（布局）</div>
      <div class="muted">当前仅实现页面布局与步骤卡片；推荐结果后续通过预留接口接入。</div>
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
  { title: '复盘学习结果', desc: '结合摘要、标签和笔记确认下一步学习重点。' }
])

const refresh = () => {
  // 占位：后续接入学习路径推荐接口
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
<style scoped>
.page {
  padding-top: calc(14px + env(safe-area-inset-top));
}

.topbar {
  padding: 12px 14px;
  border-radius: 18px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: rgba(251, 245, 239, 0.92);
  box-shadow: 0 10px 22px rgba(101, 87, 117, 0.09);
}

.topbar h2 {
  font-size: 18px;
}

.card,
.step {
  border-radius: 20px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: linear-gradient(180deg, #ffffff, #f7f0ea);
}

.badge {
  background: rgba(139, 121, 157, 0.16);
  color: var(--primary-deep);
}
</style>
