<template>
  <nav class="tabbar-wrap safe-bottom" aria-label="底部导航">
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
  padding: 0 12px calc(10px + env(safe-area-inset-bottom));
}

.tabbar-shell {
  width: min(100%, 560px);
  margin: 0 auto;
  padding: 6px;
  border-radius: 30px;
  background: linear-gradient(180deg, rgba(247, 239, 232, 0.72), rgba(240, 232, 245, 0.38));
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
}

.tabbar {
  height: 74px;
  padding: 10px;
  display: flex;
  align-items: stretch;
  gap: 8px;
  background: rgba(251, 245, 239, 0.94);
  border-color: rgba(17, 24, 39, 0.08);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
  border-radius: 24px;
}

.tab {
  flex: 1;
  text-decoration: none;
  color: #7c7088;
  border-radius: 18px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  min-width: 0;
}

.icon {
  width: 20px;
  height: 20px;
  fill: currentColor;
}

.label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.tab.active {
  color: var(--primary-deep);
  background: linear-gradient(180deg, var(--surface-lilac), rgba(251, 245, 239, 0.98));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.tab--upload {
  color: #756884;
}

.upload-dot {
  width: 34px;
  height: 34px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #766587, #9a87ab);
  box-shadow: 0 12px 18px rgba(118, 101, 135, 0.22);
}

.icon--upload {
  width: 17px;
  height: 17px;
  fill: #f8fafc;
}

@media (min-width: 700px) {
  .tabbar-wrap {
    padding-left: 0;
    padding-right: 0;
  }
}
</style>
