<template>
  <div class="video-player-container">
    <div class="video-section">
      <div v-if="loading" class="loading-overlay">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <span>视频加载中...</span>
      </div>
      <div v-if="videoError" class="error-overlay">
        <el-icon class="error-icon"><Warning /></el-icon>
        <span>视频加载失败，请刷新页面重试</span>
        <el-button type="primary" size="small" @click="retryLoading">重试</el-button>
      </div>
      <video
        ref="videoPlayer"
        class="video-element"
        controls
        controlslist="nodownload"
        @loadedmetadata="onVideoLoaded"
        @error="onVideoError"
        @waiting="onVideoWaiting"
        @playing="onVideoPlaying"
        @canplay="onVideoCanPlay"
        @loadstart="() => console.log('开始加载视频')"
        @progress="() => console.log('视频加载进度更新')"
        @stalled="() => console.log('视频加载停滞')"
        @suspend="() => console.log('视频加载暂停')"
        crossorigin="anonymous"
        preload="auto"
      >
        <source :src="videoUrl" type="video/mp4" />
        <track
          v-if="subtitleTrackUrl"
          kind="subtitles"
          srclang="zh"
          label="中文"
          :src="subtitleTrackUrl"
          default
        />
        您的浏览器不支持 HTML5 视频播放
      </video>
    </div>
    
    <div class="subtitle-section">
      <div class="subtitle-display">
        <h3>实时字幕</h3>
        <div class="subtitle-content" v-if="currentSubtitle">
          {{ currentSubtitle }}
        </div>
        <div class="subtitle-placeholder" v-else>
          字幕将在视频播放时显示...
        </div>
      </div>
    </div>
    
    <div class="info-section">
      <h2>{{ videoTitle }}</h2>
      <div class="video-info-details" v-if="video">
        <p>时长：{{ formatDuration(video.duration) }}</p>
        <p>分辨率：{{ video.width }} x {{ video.height }}</p>
        <p>帧率：{{ video.fps }} FPS</p>
      </div>
      <div class="subtitle-controls">
        <div class="subtitle-toggle">
          <el-switch
            v-model="showSubtitles"
            active-text="显示字幕"
            inactive-text="隐藏字幕"
            @change="toggleSubtitles"
          />
        </div>
        <div class="subtitle-download">
          <el-button-group>
            <el-button @click="downloadSubtitle('srt', true)">下载SRT字幕</el-button>
            <el-button @click="downloadSubtitle('vtt', true)">下载VTT字幕</el-button>
            <el-button @click="downloadSubtitle('txt', true)">下载TXT字幕</el-button>
          </el-button-group>
        </div>
      </div>
    </div>
    
    <div class="qa-section">
      <h3>智能问答</h3>
      <div class="qa-placeholder">
        智能问答功能开发中...
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, Warning } from '@element-plus/icons-vue'
import { getVideo, getSubtitle } from '@/api/video'

// 从环境变量获取API基础URL
const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

const route = useRoute()
const videoPlayer = ref(null)
const video = ref(null)
const subtitleTrackUrl = ref(null)
const loading = ref(false)
const showSubtitles = ref(true)
const currentSubtitle = ref('')
const videoError = ref(false)
const retryCount = ref(0)

// 计算属性
const videoUrl = computed(() => {
  if (!video.value?.id) return ''
  const url = `${baseUrl}/api/videos/${video.value.id}/stream`
  console.log('生成视频URL:', url)
  return url
})

const videoTitle = computed(() => {
  return video.value?.title || video.value?.filename || ''
})

// 格式化视频时长
const formatDuration = (seconds) => {
  if (!seconds) return '00:00'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  return h > 0
    ? `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
    : `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

// 视频事件处理
const onVideoLoaded = () => {
  console.log('视频元数据加载完成')
  if (videoPlayer.value) {
    console.log('视频信息:', {
      duration: videoPlayer.value.duration,
      width: videoPlayer.value.videoWidth,
      height: videoPlayer.value.videoHeight,
      readyState: videoPlayer.value.readyState,
      networkState: videoPlayer.value.networkState,
      error: videoPlayer.value.error
    })
  }
  loading.value = false
}

const onVideoError = (error) => {
  console.error('视频播放错误:', {
    error: videoPlayer.value?.error,
    errorCode: videoPlayer.value?.error?.code,
    errorMessage: videoPlayer.value?.error?.message,
    networkState: videoPlayer.value?.networkState,
    readyState: videoPlayer.value?.readyState
  })
  videoError.value = true
  loading.value = false
  ElMessage.error('视频播放失败，请重试')
}

const onVideoWaiting = () => {
  console.log('视频缓冲中...')
  loading.value = true
}

const onVideoPlaying = () => {
  console.log('视频开始播放')
  loading.value = false
  videoError.value = false
}

const onVideoCanPlay = () => {
  console.log('视频可以播放')
  loading.value = false
}

// 加载视频信息
const loadVideo = async () => {
  try {
    loading.value = true
    videoError.value = false
    console.log('开始加载视频')
    const { data } = await getVideo(route.params.id)
    if (!data) {
      throw new Error('视频数据为空')
    }
    video.value = data
    console.log('加载视频信息成功:', data)
    
    // 重置视频元素
    if (videoPlayer.value) {
      console.log('重置视频元素')
      videoPlayer.value.load()
    }
    
    // 加载字幕
    if (data.id && data.subtitle_filepath) {
      await loadSubtitles()
    } else {
      console.log('视频ID不存在或没有字幕文件，跳过加载字幕')
    }
    
    return true
  } catch (error) {
    console.error('加载视频失败:', error)
    ElMessage.error('加载视频失败：' + (error.response?.data?.error || error.message))
    videoError.value = true
    return false
  } finally {
    loading.value = false
  }
}

// 加载字幕
const loadSubtitles = async () => {
  if (!video.value?.id) {
    console.log('视频ID不存在，跳过加载字幕')
    return
  }

  try {
    console.log('正在加载字幕...')
    const response = await getSubtitle(video.value.id, 'vtt')
    const blob = new Blob([response.data], { type: 'text/vtt' })
    
    if (subtitleTrackUrl.value) {
      URL.revokeObjectURL(subtitleTrackUrl.value)
    }
    subtitleTrackUrl.value = URL.createObjectURL(blob)
    
    await nextTick()
    
    const tracks = videoPlayer.value?.textTracks
    if (tracks && tracks.length > 0) {
      tracks[0].mode = showSubtitles.value ? 'showing' : 'hidden'
      // 监听字幕更新事件
      tracks[0].oncuechange = () => {
        const activeCues = tracks[0].activeCues
        if (activeCues && activeCues.length > 0) {
          currentSubtitle.value = activeCues[0].text
        } else {
          currentSubtitle.value = ''
        }
      }
    }
    
    console.log('VTT字幕加载成功')
  } catch (error) {
    console.error('加载字幕失败:', error)
    ElMessage.error('加载字幕失败：' + error.message)
  }
}

// 下载字幕
const downloadSubtitle = async (format, isDownload = false) => {
  if (!video.value?.id) {
    ElMessage.error('视频ID不存在')
    return
  }

  try {
    const response = await getSubtitle(video.value.id, format, isDownload)
    const url = URL.createObjectURL(response.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `${video.value.filename.replace(/\.[^/.]+$/, '')}.${format}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载字幕失败:', error)
    ElMessage.error('下载字幕失败：' + error.message)
  }
}

// 切换字幕显示
const toggleSubtitles = () => {
  const tracks = videoPlayer.value?.textTracks
  if (tracks && tracks.length > 0) {
    tracks[0].mode = showSubtitles.value ? 'showing' : 'hidden'
  }
}

// 重试加载
const retryLoading = async () => {
  if (retryCount.value >= 3) {
    ElMessage.error('重试次数过多，请刷新页面')
    return
  }
  
  videoError.value = false
  loading.value = true
  retryCount.value++
  
  try {
    await loadVideo()
    if (videoPlayer.value) {
      videoPlayer.value.load()
    }
  } catch (error) {
    console.error('重试加载失败:', error)
    videoError.value = true
  } finally {
    loading.value = false
  }
}

// 监听视频ID变化
watch(() => route.params.id, async (newId) => {
  if (newId) {
    await loadVideo()
  }
}, { immediate: true })

// 组件卸载时清理资源
onUnmounted(() => {
  if (subtitleTrackUrl.value) {
    URL.revokeObjectURL(subtitleTrackUrl.value)
  }
})
</script>

<style scoped>
.video-player-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 20px;
  padding: 20px;
  height: calc(100vh - 64px);
  width: 100%;
  box-sizing: border-box;
}

.video-section {
  position: relative;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  width: 100%;
  height: 100%;
}

.video-element {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.subtitle-section {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
  overflow-y: auto;
  height: 100%;
  box-sizing: border-box;
}

.subtitle-display {
  height: 100%;
}

.subtitle-content {
  font-size: 1.2em;
  line-height: 1.5;
  margin-top: 10px;
  padding: 10px;
  background: white;
  border-radius: 4px;
  min-height: 60px;
}

.subtitle-placeholder {
  color: #909399;
  text-align: center;
  margin-top: 20px;
}

.info-section {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
  overflow-y: auto;
  height: 100%;
  box-sizing: border-box;
}

.video-info-details {
  margin: 15px 0;
}

.video-info-details p {
  margin: 5px 0;
  color: #606266;
}

.subtitle-controls {
  margin-top: 20px;
}

.subtitle-toggle {
  margin-bottom: 15px;
}

.qa-section {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
  height: 100%;
  box-sizing: border-box;
}

.qa-placeholder {
  color: #909399;
  text-align: center;
  margin-top: 20px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  z-index: 10;
}

.loading-icon {
  font-size: 32px;
  margin-bottom: 10px;
  animation: spin 1s linear infinite;
}

.error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 0, 0, 0.7);
  color: white;
  z-index: 10;
}

.error-icon {
  font-size: 32px;
  margin-bottom: 10px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 字幕样式 */
::cue {
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  font-size: 20px;
  line-height: 1.5;
  padding: 4px 8px;
  border-radius: 4px;
}

@media (max-width: 768px) {
  .video-player-container {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
    height: auto;
    gap: 10px;
  }
  
  .video-section,
  .subtitle-section,
  .info-section,
  .qa-section {
    height: auto;
    min-height: 200px;
  }
  
  ::cue {
    font-size: 16px;
  }
}
</style>
