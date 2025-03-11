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
            <source v-if="generateVideoUrl" :src="generateVideoUrl" type="video/mp4" />
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
      </div>
      <div 
        v-if="isQaExpanded" 
        class="qa-section qa-expanded"
        ref="qaDialog"
      >
        <div class="qa-header">
          <h3>智能问答</h3>
          <div class="qa-header-actions">
            <el-button 
              type="text" 
              @click="clearChat"
              size="small"
            >
              清空记录
            </el-button>
            <el-button 
              type="text" 
              @click="toggleQaExpand"
              :icon="Close"
              size="small"
            >
              收起
            </el-button>
          </div>
        </div>
        <div class="qa-content">
          <div class="qa-mode-switch">
            <el-radio-group v-model="qaMode" size="small">
              <el-radio-button label="video">基于视频内容</el-radio-button>
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
          <div class="qa-header-actions">
            <el-button 
              type="text" 
              @click="clearChat"
              size="small"
            >
              清空记录
            </el-button>
            <el-button 
              type="text" 
              @click="toggleQaExpand"
              :icon="FullScreen"
              size="small"
            >
              展开
            </el-button>
          </div>
        </div>
        <div class="qa-content">
          <div class="qa-mode-switch">
            <el-radio-group v-model="qaMode" size="small">
              <el-radio-button label="video">基于视频内容</el-radio-button>
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
      <div class="video-info-section">
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
      <div class="subtitle-display-container">
        <div class="subtitle-mode-switch">
          <el-radio-group v-model="subtitleMode" size="small">
            <el-radio-button label="realtime">实时字幕</el-radio-button>
            <el-radio-button label="full">全部字幕</el-radio-button>
          </el-radio-group>
        </div>
        <div class="subtitle-display">
          <template v-if="subtitleMode === 'realtime'">
            <div class="subtitle-content" v-if="currentSubtitle">
              {{ currentSubtitle }}
            </div>
            <div class="subtitle-placeholder" v-else>
              字幕将在视频播放时显示...
            </div>
          </template>
          <template v-else>
            <div class="subtitle-display full-subtitle">
              <div class="subtitle-content" v-if="fullSubtitles.length">
                <div v-for="(sub, index) in fullSubtitles" :key="index" class="subtitle-item"
                     :class="{ 'current': isCurrentSubtitle(sub) }">
                  <span class="subtitle-time">{{ formatTimeMMSS(sub.startTime) }} - {{ formatTimeMMSS(sub.endTime) }}</span>
                  <p class="subtitle-text">{{ sub.text }}</p>
                </div>
              </div>
              <div class="subtitle-placeholder" v-else>
                正在加载字幕...
              </div>
            </div>
          </template>
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
import { getVideo, getSubtitle } from '@/api/video'
import { sendChatMessage, getChatHistory, clearChatHistory } from '@/api/chat'

// 从环境变量获取API基础URL
const baseUrl = '' // 使用相对路径，让 Vite 代理正常工作

const route = useRoute()
const videoPlayer = ref(null)
const qaDialog = ref(null)
const loading = ref(true)
const videoError = ref(false)
const video = ref(null)
const videoTitle = ref('视频播放器')
const showSubtitles = ref(true)
const subtitleTrackUrl = ref(null)
const subtitleMode = ref('realtime')
const currentSubtitle = ref('')
const fullSubtitles = ref([])
const isQaExpanded = ref(false)
const qaMode = ref('free') // 默认为自由问答模式
const question = ref('')
const freeQaHistory = ref([])
const videoQaHistory = ref([])
const qaHistory = computed({
  get: () => {
    return qaMode.value === 'free' ? freeQaHistory.value : videoQaHistory.value
  },
  set: (newValue) => {
    if (qaMode.value === 'free') {
      freeQaHistory.value = newValue
    } else {
      videoQaHistory.value = newValue
    }
  }
})
const isAsking = ref(false)
const chatLoading = ref(false)

// 视频相关计算属性
const generateVideoUrl = computed(() => {
  if (!video.value) return null
  return `${baseUrl}/api/videos/${route.params.id}/stream`
})

// 组件挂载时加载视频
onMounted(async () => {
  await loadVideo()
  await loadSubtitles()
  // 初始加载聊天历史
  await loadChatHistory()
})

// 监听问答模式变化，加载对应的历史记录（如果尚未加载）
watch(qaMode, async (newMode) => {
  // 检查当前模式的历史记录是否已经加载
  const currentHistory = newMode === 'free' ? freeQaHistory : videoQaHistory
  
  // 只有当当前模式的历史记录为空时才加载
  if (currentHistory.value.length === 0) {
    await loadChatHistory()
  }
})

// 加载聊天历史
const loadChatHistory = async () => {
  try {
    chatLoading.value = true
    // 根据当前模式加载对应的历史记录
    const history = await getChatHistory(qaMode.value)
    
    // 转换历史记录格式
    if (history && history.length > 0) {
      // 重新构建问答历史，将连续的用户问题和助手回答配对
      const formattedHistory = []
      for (let i = 0; i < history.length; i += 2) {
        if (i + 1 < history.length && history[i].role === 'user' && history[i + 1].role === 'assistant') {
          formattedHistory.push({
            question: history[i].content,
            answer: history[i + 1].content
          })
        } else if (history[i].role === 'user') {
          // 如果只有用户问题没有回答
          formattedHistory.push({
            question: history[i].content,
            answer: '(无回答)'
          })
        }
      }
      
      // 直接设置对应模式的历史记录
      if (qaMode.value === 'free') {
        freeQaHistory.value = formattedHistory
      } else {
        videoQaHistory.value = formattedHistory
      }
    }
  } catch (error) {
    console.error('加载聊天历史失败:', error)
    // 不显示错误消息，只在控制台记录
  } finally {
    chatLoading.value = false
  }
}

// 加载视频信息
const loadVideo = async () => {
  try {
    loading.value = true
    videoError.value = false
    
    try {
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
    } catch (apiError) {
      console.error('API调用失败:', apiError)
      videoError.value = true
      ElMessage.error('无法连接到服务器，请检查后端服务是否正常运行')
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
    try {
      const srtResponse = await getSubtitle(route.params.id, 'srt', false)
      if (srtResponse.data) {
        const reader = new FileReader()
        reader.onload = () => {
          fullSubtitles.value = parseSrtContent(reader.result)
        }
        reader.readAsText(new Blob([srtResponse.data]))
      }
    } catch (srtError) {
      console.error('加载SRT字幕失败:', srtError)
      // 不显示错误消息，继续尝试加载VTT字幕
    }

    // 加载VTT格式字幕用于视频播放
    try {
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
    } catch (vttError) {
      console.error('加载VTT字幕失败:', vttError)
      // 不显示错误消息，避免多个错误提示
    }
    
    console.log('字幕加载成功')
  } catch (error) {
    console.error('加载字幕失败:', error)
    // 不显示错误消息，避免影响用户体验
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

// 格式化时间为分:秒格式
const formatTimeMMSS = (timeStr) => {
  try {
    const [time] = timeStr.split('.')
    const [hours, minutes, seconds] = time.split(':')
    const totalSeconds = parseInt(hours) * 3600 + parseInt(minutes) * 60 + parseInt(seconds)
    const mm = Math.floor(totalSeconds / 60)
    const ss = totalSeconds % 60
    return `${mm.toString().padStart(2, '0')}:${ss.toString().padStart(2, '0')}`
  } catch (error) {
    console.error('时间格式转换失败:', error)
    return '00:00'
  }
}

// 时间格式转换为秒
const timeToSeconds = (timeStr) => {
  try {
    const [time] = timeStr.split('.')
    const [hours, minutes, seconds] = time.split(':')
    return parseInt(hours) * 3600 + parseInt(minutes) * 60 + parseInt(seconds)
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
  
  // 检查是否是因为后端服务不可用导致的错误
  if (videoPlayer.value && videoPlayer.value.error) {
    const errorCode = videoPlayer.value.error.code;
    if (errorCode === 2 || errorCode === 4) { // MEDIA_ERR_NETWORK 或 MEDIA_ERR_SRC_NOT_SUPPORTED
      ElMessage.error('无法加载视频，请检查网络连接或后端服务是否正常运行')
    } else {
      ElMessage.error('视频播放失败，请重试')
    }
  } else {
    ElMessage.error('视频播放失败，请重试')
  }
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

// 切换字幕显示
const toggleSubtitles = () => {
  if (videoPlayer.value && videoPlayer.value.textTracks.length > 0) {
    const track = videoPlayer.value.textTracks[0]
    track.mode = showSubtitles.value ? 'showing' : 'hidden'
  }
}

// 展开逻辑
const toggleQaExpand = () => {
  isQaExpanded.value = !isQaExpanded.value
  
  // 展开时需要设置位置
  if (isQaExpanded.value) {
    nextTick(() => {
      const qaSection = qaDialog.value
      if (!qaSection) return
      
      // 获取未展开时的位置
      const rect = qaSection.getBoundingClientRect()
      
      // 设置展开后的位置，保持原位置的中心点
      qaSection.style.position = 'fixed'
      qaSection.style.top = `${rect.top}px`
      qaSection.style.left = `${rect.left}px`
      qaSection.style.transform = 'translate(0, 0)' // 重置可能的transform
    })
  }
}

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
  const userQuestion = question.value
  
  try {
    // 获取当前模式的历史记录数组
    const currentHistory = qaMode.value === 'free' ? freeQaHistory : videoQaHistory
    
    // 添加用户问题到历史记录
    currentHistory.value.unshift({
      question: userQuestion,
      answer: '正在思考中...'
    })
    
    // 清空输入框
    question.value = ''
    
    // 调用API发送问题
    let answer = ''
    try {
      // 根据当前模式发送问题
      const currentMode = qaMode.value
      const currentVideoId = currentMode === 'video' ? route.params.id : null
      
      await sendChatMessage(userQuestion, {
        mode: currentMode,
        videoId: currentVideoId,
        onData: (data) => {
          // 更新最新回答
          answer = data
          currentHistory.value[0].answer = answer
        },
        onError: (error) => {
          console.error(`提问失败: ${error}`)
          currentHistory.value[0].answer = '抱歉，我暂时无法回答这个问题，请稍后再试。'
          
          // 如果是视频模式失败，提示用户
          if (currentMode === 'video') {
            ElMessage.warning('基于视频内容的问答失败，可能是字幕文件问题或视频内容不相关')
          }
        },
        onComplete: () => {
          console.log('回答完成')
          // 移除重新加载历史记录的代码，保留当前历史
          // setTimeout(() => loadChatHistory(), 500)
        }
      })
    } catch (apiError) {
      console.error('API调用失败:', apiError)
      currentHistory.value[0].answer = '抱歉，服务器连接失败，请检查网络连接或稍后再试。'
    }
  } catch (error) {
    console.error('提问失败:', error)
    ElMessage.error('提问失败，请重试')
  } finally {
    isAsking.value = false
  }
}

// 清空聊天记录
const clearChat = async () => {
  try {
    await clearChatHistory(qaMode.value)
    
    // 清空当前模式的历史记录
    if (qaMode.value === 'free') {
      freeQaHistory.value = []
    } else {
      videoQaHistory.value = []
    }
    
    ElMessage.success('聊天记录已清空')
  } catch (error) {
    console.error('清空聊天记录失败:', error)
    ElMessage.error('清空聊天记录失败')
  }
}

// 组件卸载时清理资源
onUnmounted(() => {
  if (subtitleTrackUrl.value) {
    URL.revokeObjectURL(subtitleTrackUrl.value)
  }
})

// 组件挂载时加载视频和聊天历史
onMounted(async () => {
  if (route.params.id) {
    await loadVideo()
    await loadChatHistory() // 加载聊天历史
  }
})

// 监听路由变化
watch(() => route.params.id, async (newId) => {
  if (newId) {
    await loadVideo()
  }
}, { immediate: true })
</script>

<style scoped>
.video-player-container {
  display: flex;
  height: 100vh;
  background-color: #1a1a1a;
}

.left-section {
  flex: 5.5;
  display: flex;
  flex-direction: column;
  padding: 20px;
  gap: 20px;
  overflow: hidden;
}

.subtitle-section {
  flex: 4.5;
  display: flex;
  flex-direction: column;
  padding: 20px;
  background-color: #2a2a2a;
  overflow: hidden;
}

.video-info-section {
  flex: 0.2;
  background-color: #1a1a1a;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 15px;
  min-height: fit-content;
}

.subtitle-display-container {
  flex: 0.8;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.video-info h3 {
  color: #fff;
  margin: 0 0 8px 0;
  font-size: 16px;
}

.video-details {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: #aaa;
  font-size: 13px;
}

.subtitle-controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 15px;
}

.subtitle-toggle {
  display: flex;
  justify-content: center;
}

.subtitle-download {
  display: flex;
  justify-content: center;
  gap: 8px;
}

.video-wrapper {
  flex: 0.4;
  display: flex;
  flex-direction: column;
  background-color: #2a2a2a;
  border-radius: 8px;
  overflow: hidden;
  min-height: 300px;
}

.video-section {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #000;
}

.video-element {
  width: 100%;
  height: 100%;
  object-fit: contain;
  max-height: 100%;
}

.qa-section {
  flex: 0.6;
  display: flex;
  flex-direction: column;
  background-color: #2a2a2a;
  border-radius: 8px;
  overflow: hidden;
}

.qa-section.qa-expanded {
  position: fixed;
  width: 40%;
  height: 80%;
  z-index: 1000;
  background-color: #2a2a2a;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  transition: all 0.3s ease;
}

.qa-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #1a1a1a;
  padding: 8px 15px;
  min-height: 30px;
}

.qa-header h3 {
  margin: 0;
  font-size: 14px;
  color: #fff;
}

.qa-header-actions {
  display: flex;
  gap: 8px;
}

.qa-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 15px;
  gap: 15px;
  overflow-y: auto;
}

.qa-mode-switch {
  margin-bottom: 12px;
  text-align: center;
}

.qa-input {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.qa-input .el-textarea {
  flex: 1;
}

.qa-input .el-button {
  align-self: flex-start;
}

.qa-history {
  flex: 1;
  overflow-y: auto;
}

.qa-history ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.qa-item {
  background-color: #1a1a1a;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
}

.qa-item .question,
.qa-item .answer {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}

.qa-item .answer {
  margin-bottom: 0;
}

.qa-icon {
  flex-shrink: 0;
  font-size: 16px;
  margin-top: 3px;
}

.qa-text {
  flex: 1;
  color: #fff;
  line-height: 1.5;
  word-break: break-word;
}

.subtitle-mode-switch {
  margin-bottom: 12px;
  text-align: center;
  padding: 8px;
  background-color: #1a1a1a;
  border-radius: 8px;
}

.subtitle-display {
  flex: 1;
  background-color: #1a1a1a;
  border-radius: 8px;
  padding: 15px;
  overflow-y: auto;
}

.subtitle-content {
  color: #fff;
  line-height: 1.6;
}

.full-subtitle {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 6px;
}

.subtitle-item {
  padding: 12px;
  margin: 8px 0;
  background-color: #2a2a2a;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.subtitle-item.current {
  background-color: #3a3a3a;
  border-left: 3px solid #409eff;
}

.subtitle-time {
  display: block;
  color: #909399;
  font-size: 12px;
  margin-bottom: 8px;
}

.subtitle-text {
  color: #fff;
  margin: 0;
  line-height: 1.6;
}

.subtitle-placeholder {
  color: #909399;
  text-align: center;
  padding: 20px;
  background-color: #2a2a2a;
  border-radius: 8px;
}

/* 美化滚动条 */
.subtitle-display::-webkit-scrollbar,
.qa-history::-webkit-scrollbar {
  width: 6px;
}

.subtitle-display::-webkit-scrollbar-track,
.qa-history::-webkit-scrollbar-track {
  background: #2a2a2a;
}

.subtitle-display::-webkit-scrollbar-thumb,
.qa-history::-webkit-scrollbar-thumb {
  background-color: #4a4a4a;
  border-radius: 3px;
}

.subtitle-display::-webkit-scrollbar-thumb:hover,
.qa-history::-webkit-scrollbar-thumb:hover {
  background-color: #5a5a5a;
}

.video-info {
  margin-bottom: 15px;
}

.video-info h3 {
  color: #fff;
  margin: 0 0 10px 0;
  font-size: 18px;
}

.video-details {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  color: #aaa;
  font-size: 14px;
}

.subtitle-controls {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-top: 20px;
}

.subtitle-toggle {
  display: flex;
  justify-content: center;
}

.subtitle-download {
  display: flex;
  justify-content: center;
  gap: 10px;
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
  background-color: rgba(0, 0, 0, 0.8);
  color: #fff;
  z-index: 10;
}
</style>
