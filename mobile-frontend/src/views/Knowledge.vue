<template>
  <div class="page">
    <header class="topbar">
      <h2>知识点总览</h2>
      <button class="link" @click="refresh">刷新</button>
    </header>

    <div class="card">
      <div class="row">
        <input class="input" v-model.trim="keyword" placeholder="搜索知识点…" />
        <button class="btn" @click="refresh">搜索</button>
      </div>
      <div class="muted">该页仅实现移动端固定布局；数据由移动应用后端通过接口提供。</div>
    </div>

    <div class="list">
      <div v-if="items.length === 0" class="empty">暂无知识点数据。</div>
      <div v-else class="item" v-for="(it, i) in items" :key="i">
        <div class="title">{{ it.title }}</div>
        <div class="muted">{{ it.desc }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const keyword = ref('')
const items = ref([])

const refresh = () => {
  // 占位：后续接入移动后端查询接口
  items.value = []
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
  gap: 10px;
}

.row {
  display: grid;
  grid-template-columns: 1fr 84px;
  gap: 10px;
}

.input {
  width: 100%;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 12px;
  padding: 12px 12px;
  outline: none;
}

.btn {
  border-radius: 12px;
  padding: 12px 10px;
  font-weight: 900;
  border: 0;
  color: #fff;
  background: linear-gradient(135deg, #667eea, #764ba2);
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

.empty {
  color: var(--muted);
  font-size: 13px;
}

.item {
  background: var(--card);
  border-radius: var(--radius);
  padding: 14px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  display: grid;
  gap: 8px;
}

.title {
  font-weight: 900;
  font-size: 13px;
}
</style>
