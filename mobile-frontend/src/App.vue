<template>
  <div class="app-shell">
    <div class="bg-decor bg-decor--left"></div>
    <div class="bg-decor bg-decor--right"></div>
    <main class="content">
      <RouterView />
    </main>
    <TabBar v-if="!route.meta.hideTabBar" />
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import TabBar from '@/components/TabBar.vue'

const route = useRoute()
</script>

<style scoped>
.app-shell {
  position: relative;
  min-height: 100vh;
  overflow-x: hidden;
}

.content {
  position: relative;
  z-index: 2;
  min-height: 100vh;
  overflow: auto;
  padding-bottom: calc(92px + env(safe-area-inset-bottom));
}

.bg-decor {
  position: fixed;
  pointer-events: none;
  z-index: 0;
  filter: saturate(1.05);
}

.bg-decor--left {
  width: 260px;
  height: 260px;
  left: -88px;
  top: 12%;
  border-radius: 76px;
  background: linear-gradient(140deg, rgba(31, 122, 140, 0.24), rgba(31, 122, 140, 0.08));
  transform: rotate(-20deg);
}

.bg-decor--right {
  width: 280px;
  height: 280px;
  right: -118px;
  top: 58%;
  border-radius: 84px;
  background: linear-gradient(140deg, rgba(235, 140, 52, 0.22), rgba(235, 140, 52, 0.08));
  transform: rotate(16deg);
}
</style>
