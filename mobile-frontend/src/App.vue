<template>
  <div class="app-shell app-surface">
    <div class="bg-decor bg-decor--left"></div>
    <div class="bg-decor bg-decor--center"></div>
    <div class="bg-decor bg-decor--right"></div>
    <main class="content">
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
  min-height: 100dvh;
  overflow-x: hidden;
  background:
    radial-gradient(circle at 18% 56%, rgba(91, 228, 255, 0.16), transparent 24%),
    radial-gradient(circle at 72% 38%, rgba(6, 128, 170, 0.16), transparent 28%);
}

.content {
  position: relative;
  z-index: 2;
  min-height: 100dvh;
  width: 100%;
  overflow-x: hidden;
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
    radial-gradient(circle at 44% 46%, rgba(12, 136, 177, 0.98), rgba(15, 141, 183, 0.82) 44%, rgba(20, 152, 192, 0.26) 70%, transparent 82%);
  transform: translateX(-50%);
}

.bg-decor--right {
  width: 760px;
  height: 760px;
  right: -280px;
  top: -180px;
  border-radius: 48%;
  background:
    radial-gradient(circle at 34% 40%, rgba(152, 233, 251, 0.78), rgba(152, 233, 251, 0.18) 62%, transparent 78%);
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
