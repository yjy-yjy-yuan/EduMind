<template>
  <div class="page">
    <header class="topbar">
      <button class="back" @click="router.back()">‹</button>
      <div class="topbar-title">播放</div>
      <div />
    </header>

    <div class="wrap">
      <video class="video" controls playsinline>
        <source :src="streamUrl" type="video/mp4" />
        <track v-if="subtitleUrl" kind="subtitles" srclang="zh" label="中文" :src="subtitleUrl" default />
      </video>
    </div>

    <div class="tip">若无法播放，请确认移动应用后端是否提供 `/api/videos/:id/stream` 与跨域/鉴权配置。</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { withBase } from '@/config'

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id)

const streamUrl = computed(() => withBase(`/api/videos/${id.value}/stream`))
const subtitleUrl = computed(() => withBase(`/api/videos/${id.value}/subtitle?format=vtt`))
</script>

<style scoped>
.page {
  max-width: 720px;
  margin: 0 auto;
  padding: 16px;
}

.topbar {
  display: grid;
  grid-template-columns: 40px 1fr 40px;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.topbar-title {
  text-align: center;
  font-weight: 900;
}

.back {
  border: 0;
  background: var(--card);
  border-radius: 12px;
  height: 36px;
  width: 40px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  font-size: 22px;
  line-height: 1;
}

.wrap {
  border-radius: var(--radius);
  overflow: hidden;
  background: #000;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
}

.video {
  width: 100%;
  height: auto;
  display: block;
}

.tip {
  margin-top: 12px;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}
</style>
