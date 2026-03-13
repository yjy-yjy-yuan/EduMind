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
  overflow: hidden;
}

.content {
  position: relative;
  z-index: 2;
  min-height: 100vh;
  overflow: auto;
  padding-bottom: calc(82px + env(safe-area-inset-bottom));
}

.bg-decor {
  position: fixed;
  pointer-events: none;
  z-index: 0;
}

.bg-decor--left {
  width: 220px;
  height: 220px;
  left: -70px;
  top: 18%;
  border-radius: 44px;
  background: linear-gradient(135deg, rgba(105, 212, 171, 0.33), rgba(96, 193, 201, 0.22));
  transform: rotate(-16deg);
}

.bg-decor--right {
  width: 250px;
  height: 250px;
  right: -96px;
  top: 58%;
  border-radius: 56px;
  background: linear-gradient(135deg, rgba(255, 194, 121, 0.22), rgba(105, 212, 171, 0.25));
  transform: rotate(18deg);
}
</style>
