<template>
  <div class="app">
    <div class="content">
      <RouterView />
    </div>
    <TabBar v-if="!route.meta.hideTabBar" />
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import TabBar from '@/components/TabBar.vue'

const route = useRoute()
</script>

<style scoped>
.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.content {
  flex: 1;
  overflow: auto;
  padding-bottom: calc(64px + env(safe-area-inset-bottom));
}
</style>

