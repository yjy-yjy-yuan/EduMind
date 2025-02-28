<template>
  <div class="video-player">
    <div class="video-container">
      <!-- 视频播放器 -->
      <video
        ref="videoPlayer"
        class="video-element"
        :src="videoUrl"
        controls
        @timeupdate="onTimeUpdate"
        @loadedmetadata="onVideoLoaded"
      >
        <track
          v-if="subtitleUrl"
          kind="subtitles"
          srclang="zh"
          label="中文"
          :src="subtitleUrl"
          default
        >
      </video>
      
      <!-- 字幕显示区域 -->
      <div class="subtitle-container" v-if="currentSubtitle">
        <p class="subtitle-text">{{ currentSubtitle }}</p>
      </div>
    </div>
    
    <!-- 视频信息 -->
    <div class="video-info">
      <h2>{{ video.title || video.filename }}</h2>
      <div class="info-grid">
        <div class="info-item">
          <span class="label">时长：</span>
          <span>{{ formatDuration(video.duration) }}</span>
        </div>
        <div class="info-item">
          <span class="label">分辨率：</span>
          <span>{{ video.width }}x{{ video.height }}</span>
        </div>
        <div class="info-item">
          <span class="label">帧率：</span>
          <span>{{ video.fps }} FPS</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { getVideo } from '@/api/video'

export default {
  name: 'VideoPlayer',
  setup() {
    const route = useRoute()
    const videoPlayer = ref(null)
    const video = ref({})
    const currentSubtitle = ref('')
    const subtitles = ref([])
    
    // 计算属性
    const videoUrl = computed(() => {
      if (!video.value || !video.value.id) return ''
      return `/api/videos/${video.value.id}/stream`
    })
    
    const subtitleUrl = computed(() => {
      if (!video.value || !video.value.id || !video.value.subtitle_filepath) return ''
      return `/api/videos/${video.value.id}/subtitle`
    })
    
    // 方法
    const loadVideo = async () => {
      try {
        const response = await getVideo(route.params.id)
        if (response.data) {
          video.value = response.data
          console.log('加载视频成功:', video.value)
        }
      } catch (error) {
        console.error('加载视频失败:', error)
      }
    }
    
    const loadSubtitles = async () => {
      if (!video.value.subtitle_filepath) return
      try {
        const response = await fetch(subtitleUrl.value)
        const text = await response.text()
        subtitles.value = parseSRT(text)
      } catch (error) {
        console.error('加载字幕失败:', error)
      }
    }
    
    const onTimeUpdate = () => {
      if (!videoPlayer.value || subtitles.value.length === 0) return
      const currentTime = videoPlayer.value.currentTime
      const subtitle = findSubtitle(currentTime)
      currentSubtitle.value = subtitle ? subtitle.text : ''
    }
    
    const onVideoLoaded = () => {
      console.log('视频加载完成')
    }
    
    const findSubtitle = (time) => {
      return subtitles.value.find(sub => 
        time >= sub.start && time <= sub.end
      )
    }
    
    const parseSRT = (srtText) => {
      const subtitles = []
      const blocks = srtText.trim().split('\n\n')
      
      blocks.forEach(block => {
        const lines = block.split('\n')
        if (lines.length < 3) return
        
        const times = lines[1].split(' --> ')
        const start = timeToSeconds(times[0])
        const end = timeToSeconds(times[1])
        const text = lines.slice(2).join('\n')
        
        subtitles.push({ start, end, text })
      })
      
      return subtitles
    }
    
    const timeToSeconds = (timeStr) => {
      const [time, ms] = timeStr.split(',')
      const [hours, minutes, seconds] = time.split(':')
      return parseInt(hours) * 3600 + 
             parseInt(minutes) * 60 + 
             parseInt(seconds) + 
             parseInt(ms) / 1000
    }
    
    const formatDuration = (seconds) => {
      if (!seconds) return '00:00'
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      const secs = Math.floor(seconds % 60)
      
      if (hours > 0) {
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
      }
      return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    
    // 生命周期钩子
    onMounted(async () => {
      await loadVideo()
      await loadSubtitles()
    })
    
    // 监听视频变化
    watch(() => video.value, async (newVideo) => {
      if (newVideo.subtitle_filepath) {
        await loadSubtitles()
      }
    }, { deep: true })
    
    return {
      videoPlayer,
      video,
      currentSubtitle,
      videoUrl,
      subtitleUrl,
      onTimeUpdate,
      onVideoLoaded,
      formatDuration
    }
  }
}
</script>

<style scoped>
.video-player {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.video-container {
  position: relative;
  width: 100%;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.video-element {
  width: 100%;
  height: auto;
  max-height: 70vh;
}

.subtitle-container {
  position: absolute;
  bottom: 60px;
  left: 0;
  right: 0;
  text-align: center;
  padding: 10px;
  z-index: 1;
}

.subtitle-text {
  display: inline-block;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 1.2em;
  max-width: 80%;
  margin: 0 auto;
}

.video-info {
  margin-top: 20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-top: 15px;
}

.info-item {
  display: flex;
  align-items: center;
}

.label {
  font-weight: bold;
  margin-right: 10px;
  color: #666;
}
</style>
