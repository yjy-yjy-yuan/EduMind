<template>
  <div class="app-shell app-surface">
    <div class="bg-decor bg-decor--left"></div>
    <div class="bg-decor bg-decor--center"></div>
    <div class="bg-decor bg-decor--right"></div>
    <main class="content" :class="{ 'content--with-tabbar': !route.meta.hideTabBar }">
      <RouterView />
    </main>
    <TabBar v-if="!route.meta.hideTabBar" />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import TabBar from '@/components/TabBar.vue'

const route = useRoute()

onMounted(async () => {
  await Promise.resolve()
})
</script>

<style scoped>
.app-shell {
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 100dvh;
  overflow-x: hidden;
  background:
    radial-gradient(circle at 18% 56%, rgba(91, 180, 255, 0.18), transparent 24%),
    radial-gradient(circle at 72% 38%, rgba(30, 100, 200, 0.16), transparent 28%);
}

.content {
  position: relative;
  z-index: 2;
  flex: 1 1 auto;
  min-height: 0;
  width: 100%;
  overflow-x: hidden;
  padding-top: env(safe-area-inset-top);
  padding-bottom: calc(14px + env(safe-area-inset-bottom));
}

.content--with-tabbar {
  padding-bottom: calc(var(--tabbar-space) + 14px);
}

.bg-decor {
  position: fixed;
  pointer-events: none;
  z-index: 0;
  filter: blur(42px) saturate(1.02);
  opacity: 0.98;
}

.bg-decor--left {
  width: 340px;
  height: 760px;
  left: -128px;
  top: 8%;
  border-radius: 999px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(246, 253, 255, 0.34) 54%, rgba(255, 255, 255, 0.08));
}

.bg-decor--center {
  width: 620px;
  height: 620px;
  left: 65%;
  top: 12%;
  border-radius: 50%;
  background:
    radial-gradient(circle at 44% 46%, rgba(30, 110, 200, 0.98), rgba(30, 120, 210, 0.82) 44%, rgba(40, 140, 220, 0.26) 70%, transparent 82%);
  transform: translateX(-50%);
}

.bg-decor--right {
  width: 760px;
  height: 760px;
  right: -280px;
  top: -180px;
  border-radius: 48%;
  background:
    radial-gradient(circle at 34% 40%, rgba(147, 197, 253, 0.78), rgba(147, 197, 253, 0.18) 62%, transparent 78%);
}

@media (max-width: 390px) {
  .bg-decor--left {
    width: 230px;
    height: 560px;
    left: -102px;
    top: 14%;
  }

  .bg-decor--center {
    width: 420px;
    height: 420px;
    left: 68%;
    top: 18%;
  }

  .bg-decor--right {
    width: 520px;
    height: 520px;
    right: -208px;
    top: -120px;
  }
}
</style>
