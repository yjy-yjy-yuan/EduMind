<template>
  <div class="page">
    <header class="topbar">
      <h2>学习路径</h2>
      <button class="link" @click="refresh">刷新</button>
    </header>

    <div class="list">
      <div class="step" v-for="(s, i) in steps" :key="i">
        <div class="badge">{{ i + 1 }}</div>
        <div class="content">
          <div class="title">{{ s.title }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'


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
  padding-top: 14px;
}

.topbar {
  padding: 12px 14px;
  border-radius: 18px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: rgba(235, 245, 255, 0.92);
  box-shadow: 0 10px 22px rgba(30, 90, 168, 0.09);
}

.topbar h2 {
  font-size: 18px;
}

.step {
  border-radius: 20px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: linear-gradient(180deg, #ffffff, rgba(235, 245, 255, 0.5));
}

.badge {
  background: rgba(91, 143, 217, 0.16);
  color: var(--primary-deep);
}
</style>
