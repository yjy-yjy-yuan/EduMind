<template>
  <nav class="tabbar safe-bottom">
    <RouterLink to="/" class="tab" :class="{ active: isActive('/') }">
      <span class="icon">🏠</span>
      <span class="label">首页</span>
    </RouterLink>
    <RouterLink to="/videos" class="tab" :class="{ active: isActive('/videos') }">
      <span class="icon">🎬</span>
      <span class="label">视频</span>
    </RouterLink>
    <RouterLink to="/upload" class="tab tab--primary" :class="{ active: isActive('/upload') }">
      <span class="icon">➕</span>
      <span class="label">上传</span>
    </RouterLink>
    <RouterLink to="/notes" class="tab" :class="{ active: isActive('/notes') }">
      <span class="icon">📝</span>
      <span class="label">笔记</span>
    </RouterLink>
    <RouterLink to="/profile" class="tab" :class="{ active: isActive('/profile') }">
      <span class="icon">👤</span>
      <span class="label">我的</span>
    </RouterLink>
  </nav>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
const isActive = (prefix) => {
  const p = String(route.path || '')
  return p === prefix || (prefix !== '/' && p.startsWith(`${prefix}/`))
}
</script>

<style scoped>
.tabbar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  height: calc(64px + env(safe-area-inset-bottom));
  padding: 8px 10px calc(8px + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.92);
  border-top: 1px solid var(--border);
  display: flex;
  gap: 10px;
  z-index: 1000;
  backdrop-filter: blur(10px);
  box-shadow: 0 -10px 30px rgba(17, 24, 39, 0.06);
}

.tab {
  flex: 1;
  text-decoration: none;
  color: var(--muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border-radius: var(--radius-sm);
  padding: 8px 0;
}

.icon {
  font-size: 18px;
  line-height: 1;
}

.label {
  font-size: 12px;
  font-weight: 700;
}

.tab.active {
  color: var(--primary);
  background: rgba(79, 70, 229, 0.08);
}

.tab--primary {
  color: #fff;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.tab--primary.active {
  color: #fff;
}
</style>
