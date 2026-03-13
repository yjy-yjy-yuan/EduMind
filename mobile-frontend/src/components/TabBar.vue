<template>
  <nav class="tabbar-wrap safe-bottom" aria-label="底部导航">
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
  padding: 0 12px calc(10px + env(safe-area-inset-bottom));
}

.tabbar {
  height: 66px;
  padding: 8px;
  display: flex;
  align-items: stretch;
  gap: 8px;
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(16px);
}

.tab {
  flex: 1;
  text-decoration: none;
  color: var(--muted);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
}

.icon {
  width: 20px;
  height: 20px;
  fill: currentColor;
}

.label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.tab.active {
  color: var(--primary);
  background: var(--tap);
}

.tab--upload {
  color: var(--primary-deep);
}

.upload-dot {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #8be3c2, #8fd6dd);
  box-shadow: 0 5px 12px rgba(31, 157, 116, 0.28);
}

.icon--upload {
  width: 15px;
  height: 15px;
  fill: #0f5f45;
}

@media (min-width: 700px) {
  .tabbar-wrap {
    max-width: 560px;
    margin: 0 auto;
  }
}
</style>
