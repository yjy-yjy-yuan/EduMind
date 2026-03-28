<template>
  <nav class="tabbar-wrap" aria-label="底部导航">
    <div class="tabbar-shell">
      <div class="tabbar ios-card">
      <RouterLink to="/" class="tab" :class="{ active: isActive('/') }">
        <svg viewBox="0 0 24 24" aria-hidden="true" class="icon">
          <path d="M3 10.4L12 3l9 7.4v9.6a1 1 0 0 1-1 1h-5.8v-6.4h-4.4V21H4a1 1 0 0 1-1-1z" />
        </svg>
        <span class="label">首页</span>
      </RouterLink>

      <RouterLink to="/videos" class="tab" :class="{ active: isActive('/videos') }">
        <svg viewBox="0 0 24 24" aria-hidden="true" class="icon">
          <path d="M4 5h12a2 2 0 0 1 2 2v2.2l2.8-2a1 1 0 0 1 1.6.8v8a1 1 0 0 1-1.6.8L18 14.8V17a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z" />
        </svg>
        <span class="label">视频</span>
      </RouterLink>

      <RouterLink to="/upload" class="tab tab--upload" :class="{ active: isActive('/upload') }">
        <span class="upload-dot">
          <svg viewBox="0 0 24 24" aria-hidden="true" class="icon icon--upload">
            <path d="M11 6.4V15h2V6.4l2.8 2.8 1.4-1.4L12 2.6 6.8 7.8l1.4 1.4zM5 18h14v2H5z" />
          </svg>
        </span>
        <span class="label">上传</span>
      </RouterLink>

      <RouterLink to="/notes" class="tab" :class="{ active: isActive('/notes') }">
        <svg viewBox="0 0 24 24" aria-hidden="true" class="icon">
          <path d="M6 3h9.8L21 8.2V19a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zm8 1.8V9h4.2" />
        </svg>
        <span class="label">笔记</span>
      </RouterLink>

      <RouterLink to="/profile" class="tab" :class="{ active: isActive('/profile') }">
        <svg viewBox="0 0 24 24" aria-hidden="true" class="icon">
          <path d="M12 12.6a4.3 4.3 0 1 0-4.3-4.3 4.3 4.3 0 0 0 4.3 4.3zm0 2.2c-4.4 0-8 2.2-8 4.8V21h16v-1.4c0-2.6-3.6-4.8-8-4.8z" />
        </svg>
        <span class="label">我的</span>
      </RouterLink>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
const isActive = (prefix) => {
  const path = String(route.path || '')
  return path === prefix || (prefix !== '/' && path.startsWith(`${prefix}/`))
}
</script>

<style scoped>
.tabbar-wrap {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  padding: 0 0 var(--tabbar-shell-gap);
  background: transparent;
  border-top: 0;
  pointer-events: none;
}

.tabbar-shell {
  width: min(100%, 620px);
  margin: 0 auto;
  padding: 0 clamp(12px, 4vw, 18px);
  box-sizing: border-box;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  pointer-events: none;
}

.tabbar {
  min-height: var(--tabbar-card-height);
  padding: 10px 12px calc(10px + env(safe-area-inset-bottom));
  display: flex;
  align-items: stretch;
  gap: 6px;
  background: linear-gradient(180deg, rgba(245, 238, 250, 0.98), rgba(237, 227, 246, 0.98));
  border: 1px solid rgba(95, 71, 126, 0.12);
  box-shadow:
    0 16px 28px rgba(95, 71, 126, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.72);
  border-radius: 28px;
  overflow: hidden;
  pointer-events: auto;
}

.tab {
  flex: 1;
  text-decoration: none;
  color: #6f6185;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  min-width: 0;
  padding: 2px 0;
}

.icon {
  width: 18px;
  height: 18px;
  fill: currentColor;
}

.label {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.tab.active {
  color: var(--primary-deep);
  background: linear-gradient(180deg, rgba(236, 227, 246, 0.98), rgba(247, 241, 251, 0.98));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.tab--upload {
  color: #6d5a86;
}

.upload-dot {
  width: 30px;
  height: 30px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #6a4b9b, #9b82c7);
  box-shadow: 0 12px 18px rgba(106, 75, 155, 0.26);
}

.icon--upload {
  width: 15px;
  height: 15px;
  fill: #f8fafc;
}

@media (min-width: 700px) {
  .tabbar-wrap {
    padding-left: 0;
    padding-right: 0;
  }
}
</style>
