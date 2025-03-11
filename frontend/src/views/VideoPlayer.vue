<template>
  <div class="video-player-container">
    <!-- 左侧区域 -->
    <div class="left-section">
      <!-- 上方区域：视频播放区域(70%)和视频播放器(30%)的左右布局 -->
      <div class="upper-section">
        <!-- 视频播放区域 -->
        <div class="video-main-area">
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
        </div>
        
        <!-- 视频信息区域 -->
        <div class="video-player-area">
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
                <el-dropdown>
                  <el-button type="primary">
                    下载字幕<el-icon class="el-icon--right"><arrow-down /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="downloadSubtitle('srt', true)">下载SRT字幕</el-dropdown-item>
                      <el-dropdown-item @click="downloadSubtitle('vtt', true)">下载VTT字幕</el-dropdown-item>
                      <el-dropdown-item @click="downloadSubtitle('txt', true)">下载TXT字幕</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 下方区域：智能问答区域 -->
      <div class="lower-section">
        <div class="qa-container">
          <div class="qa-section">
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
      </div>
    </div>
    
    <!-- 右侧区域：字幕区域 -->
    <div class="subtitle-section">
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
import { ref, onMounted, computed, watch, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElLoading } from 'element-plus';
import { 
  Loading, Warning, FullScreen, Close, 
  QuestionFilled, ChatLineSquare, ArrowDown as ArrowDown
} from '@element-plus/icons-vue';
import { getVideo, getSubtitle } from '@/api/video';
import { sendChatMessage } from '@/api/chat';
import request from '@/utils/request';

const route = useRoute();
const router = useRouter();
const videoId = computed(() => route.params.id);
const videoPlayer = ref(null);
const qaDialog = ref(null);

// 视频状态
const loading = ref(true);
const videoError = ref(false);
const video = ref(null);
const videoTitle = ref('视频加载中...');
const generateVideoUrl = computed(() => {
  if (!videoId.value) return null;
  return `/api/videos/${videoId.value}/stream`;
});
const subtitleTrackUrl = computed(() => {
  if (!videoId.value) return null;
  return `/api/videos/${videoId.value}/subtitle?format=vtt`;
});

// 字幕状态
const showSubtitles = ref(true);
const subtitleMode = ref('realtime');
const currentSubtitle = ref('');
const fullSubtitles = ref([]);

// 问答状态
const qaMode = ref('video');
const question = ref('');
const isAsking = ref(false);
const qaHistory = ref([]);

// 加载视频信息
const loadVideoInfo = async () => {
  try {
    loading.value = true;
    videoError.value = false;
    const response = await getVideo(videoId.value);
    video.value = response.data;
    videoTitle.value = video.value.title || '未命名视频';
    loading.value = false;
  } catch (error) {
    console.error('加载视频信息失败:', error);
    videoError.value = true;
    loading.value = false;
    ElMessage.error('加载视频信息失败，请刷新页面重试');
  }
};

// 加载字幕
const loadSubtitles = async () => {
  try {
    // 使用普通文本格式获取字幕
    const response = await request({
      url: `/api/videos/${videoId.value}/subtitle`,
      method: 'get',
      params: { format: 'srt' }
    });
    
    console.log('字幕数据响应:', response);
    
    // 解析SRT格式字幕
    if (typeof response.data === 'string') {
      fullSubtitles.value = parseSRT(response.data);
      console.log('解析后的字幕数据:', fullSubtitles.value);
    } else {
      throw new Error('无效的字幕数据格式');
    }
  } catch (error) {
    console.error('加载字幕失败:', error);
    ElMessage.error('加载字幕失败，将使用视频内嵌字幕');
    // 设置为空数组，避免后续处理出错
    fullSubtitles.value = [];
  }
};

// 解析SRT格式字幕
const parseSRT = (srtString) => {
  // 按空行分割字幕块
  const subtitleBlocks = srtString.trim().split(/\r?\n\r?\n/);
  const subtitles = [];
  
  for (const block of subtitleBlocks) {
    const lines = block.split(/\r?\n/);
    if (lines.length < 3) continue; // 跳过格式不正确的块
    
    // 第二行包含时间信息
    const timeMatch = lines[1].match(/(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})/);
    if (!timeMatch) continue;
    
    const startTime = convertSRTTimeToSeconds(timeMatch[1]);
    const endTime = convertSRTTimeToSeconds(timeMatch[2]);
    
    // 第三行及以后是字幕文本
    const text = lines.slice(2).join('\n');
    
    subtitles.push({
      startTime,
      endTime,
      text
    });
  }
  
  return subtitles;
};

// 将SRT时间格式转换为秒
const convertSRTTimeToSeconds = (timeString) => {
  const parts = timeString.split(/[:,]/);
  if (parts.length !== 4) return 0;
  
  const hours = parseInt(parts[0], 10);
  const minutes = parseInt(parts[1], 10);
  const seconds = parseInt(parts[2], 10);
  const milliseconds = parseInt(parts[3], 10);
  
  return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000;
};

// 视频事件处理
const onVideoLoaded = () => {
  console.log('视频元数据已加载');
  loading.value = false;
};

const onVideoError = (error) => {
  console.error('视频加载错误:', error);
  videoError.value = true;
  loading.value = false;
};

const onVideoWaiting = () => {
  console.log('视频缓冲中');
  loading.value = true;
};

const onVideoPlaying = () => {
  console.log('视频播放中');
  loading.value = false;
};

const onVideoCanPlay = () => {
  console.log('视频可以播放');
  loading.value = false;
};

const retryLoading = () => {
  if (videoPlayer.value) {
    videoPlayer.value.load();
    videoError.value = false;
    loading.value = true;
  }
};

// 字幕控制
const toggleSubtitles = () => {
  if (videoPlayer.value && videoPlayer.value.textTracks.length > 0) {
    videoPlayer.value.textTracks[0].mode = showSubtitles.value ? 'showing' : 'hidden';
  }
};

// 更新当前字幕
const updateCurrentSubtitle = () => {
  if (!videoPlayer.value || !fullSubtitles.value.length) return;
  
  const currentTime = videoPlayer.value.currentTime;
  const subtitle = fullSubtitles.value.find(
    sub => currentTime >= sub.startTime && currentTime <= sub.endTime
  );
  
  currentSubtitle.value = subtitle ? subtitle.text : '';
};

// 检查是否为当前字幕
const isCurrentSubtitle = (subtitle) => {
  if (!videoPlayer.value) return false;
  const currentTime = videoPlayer.value.currentTime;
  return currentTime >= subtitle.startTime && currentTime <= subtitle.endTime;
};

// 字幕下载
const downloadSubtitle = async (format, showMessage = false) => {
  try {
    const response = await getSubtitle(videoId.value, format, true);
    // 从response中获取blob数据
    const blob = response.data;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    // 使用与后端一致的文件名格式：local-视频标题.格式
    a.download = `local-${videoTitle.value}.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    if (showMessage) {
      ElMessage.success(`${format.toUpperCase()} 字幕下载成功`);
    }
  } catch (error) {
    console.error(`下载 ${format} 字幕失败:`, error);
    ElMessage.error(`下载 ${format} 字幕失败，请重试`);
  }
};

// 问答功能
const askQuestion = async () => {
  if (!question.value.trim()) {
    ElMessage.warning('请输入问题');
    return;
  }
  
  const questionText = question.value.trim();
  isAsking.value = true;
  
  try {
    let answer = '';
    
    await sendChatMessage(questionText, {
      mode: qaMode.value,
      videoId: qaMode.value === 'video' ? videoId.value : null,
      onData: (data) => {
        answer = data;
      },
      onError: (error) => {
        console.error('提问失败:', error);
        ElMessage.error('提问失败，请重试');
      },
      onComplete: () => {
        qaHistory.value.push({
          question: questionText,
          answer: answer || '抱歉，我无法回答这个问题'
        });
        question.value = '';
      }
    });
  } catch (error) {
    console.error('提问失败:', error);
    ElMessage.error('提问失败，请重试');
  } finally {
    isAsking.value = false;
  }
};

// 清空聊天记录
const clearChat = () => {
  qaHistory.value = [];
  question.value = '';
  ElMessage.success('聊天记录已清空');
};

// 格式化时间 (MM:SS)
const formatTimeMMSS = (seconds) => {
  if (!seconds && seconds !== 0) return '00:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds && seconds !== 0) return '00:00:00';
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

// 监听视频时间更新
const setupTimeUpdateListener = () => {
  if (videoPlayer.value) {
    videoPlayer.value.addEventListener('timeupdate', updateCurrentSubtitle);
  }
};

// 组件挂载
onMounted(async () => {
  if (!videoId.value) {
    ElMessage.error('无效的视频ID');
    router.push('/');
    return;
  }
  
  await loadVideoInfo();
  await loadSubtitles();
  setupTimeUpdateListener();
});

// 监听字幕模式变化
watch(subtitleMode, (newMode) => {
  console.log(`字幕模式切换为: ${newMode}`);
});

// 清理事件监听器
const cleanupEventListeners = () => {
  if (videoPlayer.value) {
    videoPlayer.value.removeEventListener('timeupdate', updateCurrentSubtitle);
  }
};

// 组件卸载前清理
onUnmounted(() => {
  cleanupEventListeners();
});
</script>

<style scoped>
.video-player-container {
  display: flex;
  height: 100vh;
  background-color: #1a1a1a;
}

.left-section {
  flex: 6; /* 左侧栏占比6 */
  display: flex;
  flex-direction: column;
  padding: 20px;
  gap: 20px;
  overflow: hidden;
}

.subtitle-section {
  flex: 4; /* 右侧栏占比4 */
  display: flex;
  flex-direction: column;
  padding: 20px;
  background-color: #2a2a2a;
  overflow: hidden;
}

/* 左侧上方区域布局 */
.upper-section {
  flex: 1; /* 上方区域占左侧栏50% */
  display: flex;
  gap: 20px;
  overflow: hidden;
}

/* 左侧下方区域布局 */
.lower-section {
  flex: 1; /* 下方区域占左侧栏50% */
  display: flex;
  overflow: hidden;
}

/* 视频播放区域 */
.video-main-area {
  flex: 0.7; /* 视频播放区域占上方区域70% */
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 视频播放器区域 */
.video-player-area {
  flex: 0.3; /* 视频播放器区域占上方区域30% */
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.qa-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.video-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #2a2a2a;
  border-radius: 8px;
  overflow: hidden;
  min-height: 300px;
}

.video-info-section {
  display: flex;
  flex-direction: column;
  background-color: #1a1a1a;
  border-radius: 8px;
  padding: 12px;
  height: 100%;
  overflow-y: auto;
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
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #2a2a2a;
  border-radius: 8px;
  overflow: hidden;
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

.subtitle-display-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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
  background-color: #1a1a1a;
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
  flex: 1;
  margin-bottom: 15px;
}

.video-info h3 {
  color: #fff;
  margin: 0 0 10px 0;
  font-size: 18px;
}

.video-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: #aaa;
  font-size: 14px;
}

.subtitle-controls {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.subtitle-toggle {
  display: flex;
  justify-content: center;
}

.subtitle-download {
  display: flex;
  justify-content: center;
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
