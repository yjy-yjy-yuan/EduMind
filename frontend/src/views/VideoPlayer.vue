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
      <div 
        v-if="isQaExpanded" 
        class="qa-section qa-expanded"
        ref="qaDialog"
        :style="{ left: dialogPosition.x + 'px', top: dialogPosition.y + 'px' }"
        @mousedown="startDrag"
      >
        <div class="qa-header" @mousedown.stop="startDrag">
          <h3>智能问答</h3>
          <el-button 
            type="text" 
            @click="toggleQaExpansion"
            :icon="Close"
          >
            收起
          </el-button>
        </div>
        <div class="qa-content">
          <div class="qa-mode-switch">
            <el-radio-group v-model="qaMode" size="small">
              <el-radio-button label="video">视频内容问答</el-radio-button>
              <el-radio-button label="free">自由问答</el-radio-button>
            </el-radio-group>
          </div>
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
      <div v-else class="qa-section">
        <div class="qa-header">
          <h3>智能问答</h3>
          <el-button 
            type="text" 
            @click="toggleQaExpansion"
            :icon="FullScreen"
          >
            展开
          </el-button>
        </div>
        <div class="qa-content">
          <div class="qa-mode-switch">
            <el-radio-group v-model="qaMode" size="small">
              <el-radio-button label="video">视频内容问答</el-radio-button>
              <el-radio-button label="free">自由问答</el-radio-button>
            </el-radio-group>
          </div>
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
import { Loading, Warning, QuestionFilled, ChatLineSquare, FullScreen, Close } from '@element-plus/icons-vue'
import { getVideo, getSubtitle, askVideoQuestion, askFreeQuestion } from '@/api/video'

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
const isQaExpanded = ref(false)
const qaMode = ref('video') // 新增：问答模式
const dialogPosition = ref({ x: 0, y: 0 })
const qaDialog = ref(null)
const isDragging = ref(false)
const dragOffset = ref({ x: 0, y: 0 })

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

// 开始拖拽
const startDrag = (event) => {
  if (!isQaExpanded.value) return
  
  isDragging.value = true
  const rect = qaDialog.value.getBoundingClientRect()
  dragOffset.value = {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top
  }
  
  // 添加移动和停止拖拽事件监听
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

// 拖拽中
const onDrag = (event) => {
  if (!isDragging.value) return
  
  // 计算新位置
  const newX = event.clientX - dragOffset.value.x
  const newY = event.clientY - dragOffset.value.y
  
  // 获取窗口尺寸和对话框尺寸
  const windowWidth = window.innerWidth
  const windowHeight = window.innerHeight
  const dialogRect = qaDialog.value.getBoundingClientRect()
  
  // 限制对话框不超出窗口边界
  dialogPosition.value = {
    x: Math.min(Math.max(0, newX), windowWidth - dialogRect.width),
    y: Math.min(Math.max(0, newY), windowHeight - dialogRect.height)
  }
}

// 停止拖拽
const stopDrag = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

// 展开时初始化位置
const initDialogPosition = () => {
  if (!qaDialog.value) return
  
  const windowWidth = window.innerWidth
  const windowHeight = window.innerHeight
  const dialogRect = qaDialog.value.getBoundingClientRect()
  
  dialogPosition.value = {
    x: (windowWidth - dialogRect.width) / 2,
    y: (windowHeight - dialogRect.height) / 2
  }
}

// 监听展开状态变化
watch(isQaExpanded, (newValue) => {
  if (newValue) {
    nextTick(() => {
      initDialogPosition()
    })
  }
})

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

// 提问功能
const askQuestion = async () => {
  if (!question.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }
  
  isAsking.value = true
  try {
    const videoId = route.params.id
    let response
    
    if (qaMode.value === 'video') {
      response = await askVideoQuestion(videoId, question.value)
    } else {
      response = await askFreeQuestion(question.value)
    }

    qaHistory.value.unshift({
      question: question.value,
      answer: response.data
    })
    question.value = ''
  } catch (error) {
    ElMessage.error('提问失败，请重试')
    console.error('提问失败:', error)
  } finally {
    isAsking.value = false
  }
}

// 切换问答区域展开/收起
const toggleQaExpansion = () => {
  isQaExpanded.value = !isQaExpanded.value
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
  margin-top: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  max-height: 300px;
  overflow: hidden;
}

.qa-section.qa-expanded {
  position: fixed;
  transform: none;
  z-index: 1000;
  width: 800px;
  max-height: 600px;
  background: #1a1a1a;
  color: #ffffff;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
  cursor: move;
}

.qa-section.qa-expanded .qa-header {
  background: #2a2a2a;
  border-bottom: 1px solid #3a3a3a;
  padding: 15px 20px;
}

.qa-section.qa-expanded h3 {
  color: #ffffff;
  font-size: 18px;
}

.qa-section.qa-expanded .qa-content {
  background: #1a1a1a;
}

.qa-section.qa-expanded .qa-item {
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
}

.qa-section.qa-expanded .qa-text {
  color: #ffffff;
}

.qa-section.qa-expanded .el-input__inner,
.qa-section.qa-expanded .el-textarea__inner {
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  color: #ffffff;
}

.qa-section.qa-expanded .el-button--text {
  color: #ffffff;
}

.qa-section.qa-expanded::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: -1;
}

.qa-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  border-bottom: 1px solid #eee;
}

.qa-content {
  padding: 20px;
  height: calc(100% - 50px);
  overflow-y: auto;
}

.qa-input {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.qa-history {
  height: calc(100% - 80px);
  overflow-y: auto;
}

.qa-item {
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 4px;
  background: #f5f7fa;
}

.question, .answer {
  display: flex;
  align-items: start;
  gap: 8px;
  margin-bottom: 8px;
}

.qa-icon {
  font-size: 16px;
  color: #409eff;
}

.qa-text {
  flex: 1;
  line-height: 1.5;
  word-break: break-word;
}

.qa-mode-switch {
  margin-bottom: 10px;
  text-align: center;
}

.qa-mode-switch .el-radio-group {
  width: 100%;
  display: flex;
  justify-content: center;
}

.qa-mode-switch .el-radio-button {
  flex: 1;
  max-width: 150px;
}

/* 添加遮罩层 */
.qa-section.qa-expanded::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: -1;
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

.full-subtitle::-webkit-scrollbar-track,
.qa-history::-webkit-scrollbar-track {
  background: #f5f7fa;
}

.full-subtitle::-webkit-scrollbar-thumb,
.qa-history::-webkit-scrollbar-thumb {
  background-color: #dcdfe6;
  border-radius: 3px;
}

.full-subtitle::-webkit-scrollbar-thumb:hover,
.qa-history::-webkit-scrollbar-thumb:hover {
  background-color: #5a5a5a;
}

.qa-section.qa-expanded ::-webkit-scrollbar {
  width: 8px;
}

.qa-section.qa-expanded ::-webkit-scrollbar-track {
  background: #2a2a2a;
}

.qa-section.qa-expanded ::-webkit-scrollbar-thumb {
  background-color: #4a4a4a;
  border-radius: 4px;
}

.qa-section.qa-expanded ::-webkit-scrollbar-thumb:hover {
  background-color: #5a5a5a;
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
