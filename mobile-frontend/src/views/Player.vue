<template>
  <div class="page">
    <header class="topbar">
      <button class="back" @click="router.back()">‹</button>
      <div class="topbar-title">播放</div>
      <div />
    </header>

    <div class="wrap">
      <div v-if="UI_ONLY_MODE" class="mock-player">
        <div class="mock-player__stage">
          <div class="mock-player__chip">UI ONLY</div>
          <div class="mock-player__play">▶</div>
          <div class="mock-player__title">{{ videoTitle }}</div>
          <div class="mock-player__desc">当前阶段仅实现播放器界面，真实播放流与字幕接口后续接入。</div>
        </div>
        <div class="mock-player__controls">
          <span>00:00</span>
          <div class="mock-player__progress"><div class="mock-player__bar"></div></div>
          <span>12:48</span>
        </div>
      </div>
      <video v-else class="video" controls playsinline>
        <source :src="streamUrl" type="video/mp4" />
        <track v-if="subtitleUrl" kind="subtitles" srclang="zh" label="中文" :src="subtitleUrl" default />
      </video>
    </div>

    <div class="tip">
      {{ UI_ONLY_MODE ? '当前为 UI-only 阶段：播放器仅展示布局和交互占位，不请求真实视频资源。' : '若无法播放，请检查流媒体与字幕接口配置。' }}
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { UI_ONLY_MODE, withBase } from '@/config'
import { getVideo } from '@/api/video'

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id)
const videoTitle = ref(`视频 ${id.value}`)

const streamUrl = computed(() => withBase(`/api/videos/${id.value}/stream`))
const subtitleUrl = computed(() => withBase(`/api/videos/${id.value}/subtitle?format=vtt`))

onMounted(async () => {
  try {
    const res = await getVideo(id.value)
    const payload = res?.data || {}
    const title = payload?.video?.title || payload?.data?.title || payload?.title
    if (title) videoTitle.value = String(title)
  } catch {
    // Keep UI placeholder title when no data is available.
  }
})
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

.mock-player {
  padding: 16px;
  background: linear-gradient(180deg, #08121a, #0f2430);
  color: #fff;
}

.mock-player__stage {
  min-height: 220px;
  border-radius: 18px;
  padding: 16px;
  display: grid;
  align-content: center;
  justify-items: center;
  text-align: center;
  gap: 10px;
  background:
    radial-gradient(circle at top right, rgba(61, 141, 160, 0.34), transparent 34%),
    linear-gradient(145deg, rgba(31, 122, 140, 0.94), rgba(11, 56, 67, 0.98));
}

.mock-player__chip {
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.08em;
}

.mock-player__play {
  width: 72px;
  height: 72px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.12);
  font-size: 28px;
  text-indent: 4px;
}

.mock-player__title {
  font-size: 18px;
  font-weight: 900;
}

.mock-player__desc {
  max-width: 260px;
  color: rgba(255, 255, 255, 0.86);
  font-size: 12px;
  line-height: 1.6;
}

.mock-player__controls {
  margin-top: 14px;
  display: grid;
  grid-template-columns: 44px 1fr 44px;
  align-items: center;
  gap: 10px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.72);
}

.mock-player__progress {
  height: 6px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.16);
}

.mock-player__bar {
  width: 34%;
  height: 100%;
  background: linear-gradient(90deg, #67e8f9, #fbbf24);
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
<style scoped>
.page {
  padding-top: calc(12px + env(safe-area-inset-top));
}

.topbar {
  padding: 10px 12px;
  border-radius: 16px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 20px rgba(24, 45, 73, 0.08);
}

.wrap {
  margin-top: 12px;
  border-radius: 20px;
  border: 1px solid rgba(32, 42, 55, 0.14);
}

.tip {
  margin-top: 14px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(31, 122, 140, 0.08);
  color: var(--primary-deep);
}
</style>
