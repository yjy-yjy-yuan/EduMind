<template>
  <div class="video-player-container">
    <div class="left-section">
      <div class="video-wrapper">
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
            <source v-if="videoUrl" :src="videoUrl" type="video/mp4" />
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
        <div class="video-info-bar">
          <div class="video-info">
            <h3>{{ videoTitle }}</h3>
            <div class="video-details" v-if="video">
              <p>时长：{{ formatDuration(video?.duration) }}</p>
              <p>分辨率：{{ video?.width }} x {{ video?.height }}</p>
              <p>帧率：{{ video?.fps }} FPS</p>
            </div>
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
      </div>
      <div class="qa-section">
        <h3>智能问答</h3>
        <div class="qa-content">
          <div class="qa-input">
            <el-input v-model="question" placeholder="请输入问题" type="textarea" />
            <el-button type="primary" @click="askQuestion" :loading="isAsking">提问</el-button>
          </div>
          <div class="qa-history">
            <ul>
              <li v-for="(item, index) in qaHistory" :key="index" class="qa-item">
                <div class="question">
                  <el-icon class="qa-icon"><QuestionFilled /></el-icon>
                  <span class="qa-text">{{ item.question }}</span>
                </div>
                <div class="answer">
                  <el-icon class="qa-icon"><ChatLineSquare /></el-icon>
                  <span class="qa-text">{{ item.answer }}</span>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
    <div class="subtitle-section">
      <div class="subtitle-mode-switch">
        <el-radio-group v-model="subtitleMode" size="small">
          <el-radio-button label="realtime">实时字幕</el-radio-button>
          <el-radio-button label="full">全部字幕</el-radio-button>
        </el-radio-group>
      </div>
      <!-- 实时字幕显示 -->
      <div v-if="subtitleMode === 'realtime'" class="subtitle-display">
        <h3>实时字幕</h3>
        <div class="subtitle-content" v-if="currentSubtitle">
          {{ currentSubtitle }}
        </div>
        <div class="subtitle-placeholder" v-else>
          字幕将在视频播放时显示...
        </div>
      </div>
      <!-- 全部字幕显示 -->
      <div v-else class="subtitle-display full-subtitle">
        <h3>全部字幕</h3>
        <div class="subtitle-content" v-if="fullSubtitles.length">
          <div v-for="(sub, index) in fullSubtitles" :key="index" class="subtitle-item"
               :class="{ 'current': isCurrentSubtitle(sub) }">
            <span class="subtitle-time">{{ sub.startTime }} - {{ sub.endTime }}</span>
            <p class="subtitle-text">{{ sub.text }}</p>
          </div>
        </div>
        <div class="subtitle-placeholder" v-else>
          正在加载字幕...
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, Warning, QuestionFilled, ChatLineSquare } from '@element-plus/icons-vue'
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
const subtitleMode = ref('realtime')
const fullSubtitles = ref([])

// 问答相关的响应式变量
const question = ref('')
const isAsking = ref(false)
const qaHistory = ref([])

// 计算属性
const videoUrl = computed(() => {
  if (!video.value?.id) return ''
  const url = `${baseUrl}/api/videos/${video.value.id}/stream`
  console.log('生成视频URL:', url)
  return url
})

const videoTitle = computed(() => {
  return video.value?.title || video.value?.filename || '加载中...'
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
    const videoElement = videoPlayer.value
    console.log('视频信息:', {
      duration: videoElement.duration,
      width: videoElement.videoWidth,
      height: videoElement.videoHeight,
      readyState: videoElement.readyState,
      networkState: videoElement.networkState,
      error: videoElement.error
    })
    
    // 设置视频属性
    videoElement.crossOrigin = 'anonymous'
    videoElement.preload = 'auto'
    
    // 如果视频已经可以播放，更新loading状态
    if (videoElement.readyState >= 3) {
      loading.value = false
    }
  }
}

const onVideoError = (error) => {
  console.error('视频播放错误:', error)
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
    const { data } = await getVideo(route.params.id)
    video.value = data
    console.log('加载视频信息成功:', data)
    
    // 重置视频元素
    if (videoPlayer.value) {
      videoPlayer.value.load()
    }
    
    // 加载字幕
    if (data?.id) {
      await loadSubtitles()
    }
  } catch (error) {
    console.error('加载视频失败:', error)
    videoError.value = true
    ElMessage.error('加载视频失败，请重试')
  } finally {
    loading.value = false
  }
}

// 加载字幕
const loadSubtitles = async () => {
  try {
    // 先加载SRT格式字幕用于全部字幕显示
    const srtResponse = await getSubtitle(route.params.id, 'srt', false)
    if (srtResponse.data) {
      const reader = new FileReader()
      reader.onload = () => {
        fullSubtitles.value = parseSrtContent(reader.result)
      }
      reader.readAsText(new Blob([srtResponse.data]))
    }

    // 加载VTT格式字幕用于视频播放
    const vttResponse = await getSubtitle(route.params.id, 'vtt', false)
    if (vttResponse.data) {
      if (subtitleTrackUrl.value) {
        URL.revokeObjectURL(subtitleTrackUrl.value)
      }
      const blob = new Blob([vttResponse.data], { type: 'text/vtt' })
      subtitleTrackUrl.value = URL.createObjectURL(blob)
      
      // 确保字幕轨道被正确设置
      await nextTick()
      if (videoPlayer.value && videoPlayer.value.textTracks.length > 0) {
        const track = videoPlayer.value.textTracks[0]
        track.mode = showSubtitles.value ? 'showing' : 'hidden'
        
        // 监听字幕变化
        track.oncuechange = () => {
          if (track.activeCues && track.activeCues.length > 0) {
            currentSubtitle.value = track.activeCues[0].text
          } else {
            currentSubtitle.value = ''
          }
        }
      }
    }
    console.log('字幕加载成功')
  } catch (error) {
    console.error('加载字幕失败:', error)
    ElMessage.error('加载字幕失败')
  }
}

// 解析SRT字幕内容
const parseSrtContent = (content) => {
  try {
    if (!content || typeof content !== 'string') {
      console.error('字幕内容无效:', content)
      return []
    }
    
    const subtitles = []
    const blocks = content.trim().split('\n\n')
    
    blocks.forEach(block => {
      const lines = block.split('\n')
      if (lines.length >= 3) {
        const timeMatch = lines[1].match(/(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})/)
        if (timeMatch) {
          subtitles.push({
            startTime: timeMatch[1].replace(',', '.'),
            endTime: timeMatch[2].replace(',', '.'),
            text: lines.slice(2).join('\n')
          })
        }
      }
    })
    
    return subtitles
  } catch (error) {
    console.error('解析字幕内容失败:', error)
    return []
  }
}

// 时间格式转换为秒
const timeToSeconds = (timeStr) => {
  try {
    const [time, ms] = timeStr.split(',')
    const [hours, minutes, seconds] = time.split(':')
    return parseInt(hours) * 3600 + parseInt(minutes) * 60 + parseInt(seconds) + parseInt(ms) / 1000
  } catch (error) {
    console.error('时间格式转换失败:', error)
    return 0
  }
}

// 判断是否为当前播放的字幕
const isCurrentSubtitle = (sub) => {
  if (!videoPlayer.value) return false
  const currentTime = videoPlayer.value.currentTime
  const startTime = timeToSeconds(sub.startTime)
  const endTime = timeToSeconds(sub.endTime)
  return currentTime >= startTime && currentTime <= endTime
}

// 切换字幕显示
const toggleSubtitles = () => {
  if (videoPlayer.value && videoPlayer.value.textTracks.length > 0) {
    const track = videoPlayer.value.textTracks[0]
    track.mode = showSubtitles.value ? 'showing' : 'hidden'
  }
}

// 组件卸载时清理资源
onUnmounted(() => {
  if (subtitleTrackUrl.value) {
    URL.revokeObjectURL(subtitleTrackUrl.value)
  }
})

// 组件挂载时加载视频
onMounted(async () => {
  if (route.params.id) {
    await loadVideo()
  }
})

// 监听路由变化
watch(() => route.params.id, async (newId) => {
  if (newId) {
    await loadVideo()
  }
}, { immediate: true })

// 下载字幕
const downloadSubtitle = async (format, isDownload = false) => {
  try {
    const response = await getSubtitle(route.params.id, format, isDownload)
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 使用视频文件名作为字幕文件名
    const videoFileName = video.value?.filename || 'subtitle'
    const baseName = videoFileName.replace(/\.[^/.]+$/, '') // 移除文件扩展名
    link.download = `${baseName}.${format}`
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success(`${format.toUpperCase()}字幕下载成功`)
  } catch (error) {
    console.error('下载字幕失败:', error)
    ElMessage.error('下载字幕失败')
  }
}

// 提问功能（预留）
const askQuestion = async () => {
  if (!question.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }
  
  isAsking.value = true
  try {
    // TODO: 调用后端API进行问答
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    qaHistory.value.unshift({
      question: question.value,
      answer: '智能问答功能正在开发中...'
    })
    question.value = ''
  } catch (error) {
    ElMessage.error('提问失败，请重试')
  } finally {
    isAsking.value = false
  }
}

// 重试加载
const retryLoading = async () => {
  if (retryCount.value >= 3) {
    ElMessage.error('重试次数过多，请刷新页面')
    return
  }
  
  retryCount.value++
  console.log(`第${retryCount.value}次重试加载视频`)
  await loadVideo()
}
</script>

<style scoped>
.video-player-container {
  display: flex;
  gap: 20px;
  padding: 20px;
  height: 100vh;
  background-color: #f5f7fa;
}

.left-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 50%;
}

.video-wrapper {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.video-section {
  position: relative;
  width: 100%;
  background-color: #000;
  overflow: hidden;
}

.video-element {
  width: 100%;
  display: block;
}

.video-info-bar {
  padding: 15px;
  border-top: 1px solid #eee;
}

.video-info {
  margin-bottom: 15px;
}

.video-info h3 {
  margin: 0 0 10px 0;
  font-size: 16px;
  color: #333;
}

.video-details {
  display: flex;
  gap: 15px;
  font-size: 13px;
  color: #666;
}

.subtitle-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
}

.qa-section {
  flex: 1;
  background-color: #fff;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.qa-section h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #333;
}

.qa-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.qa-input {
  display: flex;
  gap: 10px;
}

.qa-input .el-textarea {
  flex: 1;
}

.qa-history {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 6px;
}

.qa-item {
  margin-bottom: 15px;
  padding: 10px;
  background-color: #fff;
  border-radius: 6px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.question, .answer {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.qa-icon {
  font-weight: bold;
  color: #409eff;
}

.qa-text {
  flex: 1;
  color: #333;
}

.subtitle-section {
  flex: 1;
  background-color: #fff;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.subtitle-mode-switch {
  margin-bottom: 15px;
  text-align: center;
}

.subtitle-display {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.full-subtitle {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 6px;
}

.subtitle-content {
  height: 100%;
  overflow-y: auto;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 6px;
}

.subtitle-item {
  padding: 12px;
  margin: 8px 0;
  border-radius: 6px;
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.subtitle-item.current {
  background-color: #ecf5ff;
  border-left: 3px solid #409eff;
}

.subtitle-time {
  font-size: 12px;
  color: #909399;
  display: block;
  margin-bottom: 4px;
}

.subtitle-text {
  margin: 4px 0 0;
  color: #333;
  font-size: 14px;
  line-height: 1.6;
}

.subtitle-placeholder {
  color: #909399;
  text-align: center;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 6px;
  margin: 10px 0;
}

/* 美化滚动条 */
.full-subtitle::-webkit-scrollbar,
.qa-history::-webkit-scrollbar {
  width: 6px;
}

.full-subtitle::-webkit-scrollbar-thumb,
.qa-history::-webkit-scrollbar-thumb {
  background-color: #dcdfe6;
  border-radius: 3px;
}

.full-subtitle::-webkit-scrollbar-track,
.qa-history::-webkit-scrollbar-track {
  background-color: #f5f7fa;
}

.loading-overlay,
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
  background-color: rgba(0, 0, 0, 0.7);
  color: #fff;
  gap: 10px;
}
</style>
