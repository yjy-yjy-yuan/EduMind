<template>
  <div class="video-player-container">
    <!-- 侧边栏开关按钮 -->
    <div class="sidebar-toggle" @click="toggleSidebar">
      <el-icon><arrow-right v-if="!sidebarVisible" /><arrow-left v-else /></el-icon>
    </div>
    
    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ 'sidebar-visible': sidebarVisible }">
      <div class="sidebar-header">
        <h3>功能导航</h3>
        <el-icon class="close-icon" @click="toggleSidebar"><close /></el-icon>
      </div>
      <div class="sidebar-content">
        <!-- 功能列表 -->
        <div class="sidebar-menu">
          <div class="menu-item" @click="navigateToHome">
            <el-icon><home-filled /></el-icon>
            <span>返回首页</span>
          </div>
          <div class="menu-item" @click="navigateToVideoUpload">
            <el-icon><video-camera /></el-icon>
            <span>分析新视频</span>
          </div>
          
          <!-- 已分析视频列表 -->
          <div class="menu-section">
            <h4>已分析视频</h4>
            <div class="video-list" v-if="processedVideos.length > 0">
              <div class="video-item" 
                   v-for="video in processedVideos" 
                   :key="video.id"
                   @click="navigateToVideo(video.id)">
                <div class="video-thumbnail" :style="video.thumbnail ? `background-image: url(${video.thumbnail})` : ''"></div>
                <div class="video-info">
                  <div class="video-title">{{ video.title || '未命名视频' }}</div>
                  <div class="video-duration">{{ formatDuration(video.duration) }}</div>
                </div>
              </div>
            </div>
            <div class="empty-list" v-else>
              <el-icon><video-camera /></el-icon>
              <span>暂无已处理视频</span>
            </div>
          </div>
          
          <div class="menu-item" @click="showHelpDialog">
            <el-icon><document /></el-icon>
            <span>帮助文档</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 左侧区域 -->
    <div class="left-section" :class="{ 'with-sidebar': sidebarVisible }">
      <!-- 左侧上方区域：视频播放区域(70%)和视频播放器(30%)的左右布局 -->
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
    
    <!-- 帮助文档对话框 -->
    <el-dialog
      v-model="helpDialogVisible"
      title="AI-EdVision 使用帮助"
      width="60%"
      :before-close="closeHelpDialog"
    >
      <div class="help-content">
        <h3>欢迎使用 AI-EdVision 智能教育视频分析系统</h3>
    
        <div class="help-section">
          <h4>1. 视频播放与字幕</h4>
          <ul>
            <li><strong>播放控制</strong>：使用视频播放器底部的控制栏进行播放、暂停、音量调节等操作。</li>
            <li><strong>字幕显示</strong>：视频右侧会自动显示当前播放位置的字幕内容。</li>
            <li><strong>字幕下载</strong>：点击字幕区域顶部的"下载字幕"按钮，可以下载SRT或TXT格式的字幕文件。</li>
          </ul>
        </div>
    
        <div class="help-section">
          <h4>2. 智能问答功能</h4>
          <ul>
            <li><strong>提问</strong>：在视频右侧底部的问答区域，输入您的问题并点击发送按钮。</li>
            <li><strong>查看回答</strong>：系统会基于视频内容智能分析并给出回答。</li>
            <li><strong>清空对话</strong>：点击"清空对话"按钮可以清除当前的问答记录。</li>
          </ul>
        </div>
    
        <div class="help-section">
          <h4>3. 侧边栏功能</h4>
          <ul>
            <li><strong>打开/关闭侧边栏</strong>：点击视频播放页面左上角的菜单按钮。</li>
            <li><strong>返回首页</strong>：点击"返回首页"可以回到系统主页。</li>
            <li><strong>分析新视频</strong>：点击"分析新视频"可以上传并处理新的视频文件。</li>
            <li><strong>已分析视频</strong>：显示所有已处理完成的视频列表，点击任意视频可以直接播放。</li>
          </ul>
        </div>
    
        <div class="help-section">
          <h4>4. 常见问题</h4>
          <ul>
            <li><strong>视频无法播放</strong>：请检查网络连接或刷新页面后重试。</li>
            <li><strong>字幕不同步</strong>：可能是视频处理过程中的轻微误差，通常不影响整体使用。</li>
            <li><strong>问答没有回复</strong>：请确保问题清晰明确，并与视频内容相关。</li>
          </ul>
        </div>
    
        <div class="help-section">
          <h4>5. 使用技巧</h4>
          <ul>
            <li>提问时尽量使用视频中出现的关键词，可以获得更准确的回答。</li>
            <li>点击字幕可以快速定位到视频的相应位置。</li>
            <li>处理较长的视频可能需要更多时间，请耐心等待。</li>
          </ul>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeHelpDialog">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElLoading } from 'element-plus';
import { 
  Loading, Warning, FullScreen, Close, 
  QuestionFilled, ChatLineSquare, ArrowDown as ArrowDown,
  ArrowRight, ArrowLeft, HomeFilled, VideoCamera, Document
} from '@element-plus/icons-vue';
import { getVideo, getSubtitle, getVideoList, getVideoPreview } from '@/api/video';
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

// 侧边栏状态
const sidebarVisible = ref(false);

// 帮助文档对话框状态
const helpDialogVisible = ref(false);

// 已处理视频列表
const processedVideos = ref([]);

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

// 获取已处理视频列表
const fetchProcessedVideos = async () => {
  try {
    const response = await getVideoList();
    console.log('视频列表响应:', response);
    
    // 处理不同的数据结构
    let videoList = [];
    
    if (response && response.data) {
      if (Array.isArray(response.data)) {
        // 如果是数组，直接使用
        videoList = response.data;
      } else if (response.data.videos && Array.isArray(response.data.videos)) {
        // 如果数据在videos字段中
        videoList = response.data.videos;
      } else if (typeof response.data === 'object') {
        // 尝试将对象转换为数组
        videoList = Object.values(response.data);
      }
    }
    
    // 过滤已处理的视频
    const filteredVideos = videoList.filter(video => 
      video && (video.status === 'completed' || video.status === 'processed')
    );
    
    // 为每个视频加载预览图
    processedVideos.value = await Promise.all(filteredVideos.map(async (video) => {
      try {
        // 获取预览图
        const previewResponse = await getVideoPreview(video.id);
        // 确保响应是一个有效的Blob对象
        if (previewResponse && previewResponse.data instanceof Blob) {
          // 创建预览图URL
          const previewUrl = URL.createObjectURL(previewResponse.data);
          // 添加预览图URL到视频对象
          return { ...video, thumbnail: previewUrl };
        } else {
          console.warn(`视频 ${video.id} 预览图响应不是有效的Blob:`, previewResponse);
          return video;
        }
      } catch (error) {
        console.error(`获取视频 ${video.id} 预览图失败:`, error);
        return video;
      }
    }));
  } catch (error) {
    console.error('获取视频列表失败:', error);
    processedVideos.value = [];
  }
};

// 导航到指定视频
const navigateToVideo = (videoId) => {
  if (videoId === Number(route.params.id)) {
    // 如果是当前视频，关闭侧边栏
    sidebarVisible.value = false;
  } else {
    // 关闭侧边栏
    sidebarVisible.value = false;
    
    // 跳转到新视频
    router.push(`/player/${videoId}`).then(() => {
      // 页面跳转后刷新页面
      window.location.reload();
    });
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
  if (!seconds && seconds !== 0) return '00:00';
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
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
  await fetchProcessedVideos();
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

// 切换侧边栏显示状态
const toggleSidebar = () => {
  sidebarVisible.value = !sidebarVisible.value;
};

// 跳转到指定时间
const seekToTime = (time) => {
  if (videoPlayer.value) {
    videoPlayer.value.currentTime = time;
    videoPlayer.value.play();
  }
};

// 导航到首页
const navigateToHome = () => {
  router.push('/');
};

// 显示帮助文档对话框
const showHelpDialog = () => {
  helpDialogVisible.value = true;
  // 如果侧边栏是打开的，关闭它
  sidebarVisible.value = false;
};

// 关闭帮助文档对话框
const closeHelpDialog = () => {
  helpDialogVisible.value = false;
};

// 导航到视频上传/管理页面
const navigateToVideoUpload = () => {
  router.push('/video/upload');
};
</script>

<style scoped>
/*视频播放容器*/
.video-player-container {
  display: flex;
  height: 100vh;
  background: linear-gradient(135deg, #1a1a1a 0%, #2d3436 100%);
  position: relative;
  overflow: hidden;
}

/* 添加背景点缀效果 */
.video-player-container::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect width="100" height="100" fill="none"/><circle cx="10" cy="10" r="1" fill="rgba(255,255,255,0.05)"/></svg>');
  pointer-events: none;
  z-index: 0;
}

/* 帮助文档 */
.help-content {
  max-height: 65vh;
  overflow-y: auto;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 8px;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.05);
}

.help-content h3 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 25px;
  font-size: 1.8rem;
  position: relative;
  padding-bottom: 10px;
}

.help-content h3:after {
  content: "";
  position: absolute;
  width: 80px;
  height: 3px;
  background: linear-gradient(90deg, #409EFF, #67C23A);
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  border-radius: 3px;
}

.help-section {
  margin-bottom: 30px;
  background-color: white;
  padding: 15px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  transition: transform 0.3s, box-shadow 0.3s;
}

.help-section:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 15px 0 rgba(0, 0, 0, 0.1);
}

.help-section h4 {
  margin-bottom: 15px;
  color: #409EFF;
  border-bottom: 2px solid #EBEEF5;
  padding-bottom: 8px;
  font-size: 1.3rem;
  display: flex;
  align-items: center;
}

.help-section h4:before {
  content: "•";
  color: #409EFF;
  margin-right: 8px;
  font-size: 1.5rem;
}

.help-section ul {
  padding-left: 20px;
  list-style-type: none;
}

.help-section li {
  margin-bottom: 12px;
  line-height: 1.6;
  position: relative;
  padding-left: 22px;
}

.help-section li:before {
  content: "✓";
  position: absolute;
  left: 0;
  color: #67C23A;
  font-weight: bold;
}

.help-section li strong {
  color: #606266;
  font-weight: 600;
}

.dialog-footer {
  display: flex;
  justify-content: center;
  margin-top: 10px;
}

.dialog-footer .el-button {
  padding: 10px 25px;
  font-size: 1rem;
}

.left-section {
  flex: 6; /* 左侧栏占比6 */
  display: flex;
  flex-direction: column;
  padding: 20px;
  gap: 20px;
  overflow: hidden;
}

.help-content {
  max-height: 60vh;
  overflow-y: auto;
  padding: 0 10px;
}

.help-section {
  margin-bottom: 20px;
}

.help-section h4 {
  margin-bottom: 10px;
  color: #409EFF;
  border-bottom: 1px solid #EBEEF5;
  padding-bottom: 5px;
}

.help-section ul {
  padding-left: 20px;
}

.help-section li {
  margin-bottom: 8px;
  line-height: 1.5;
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
  background: linear-gradient(135deg, #1a1a1a 0%, #2c3e50 100%);
  border-radius: 12px;
  padding: 20px;
  height: 100%;
  overflow-y: auto;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

/* 视频播放区域 */ 
.video-section {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #000 0%, #111 100%);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.5);
}

.video-element {
  width: 100%;
  height: 100%;
  object-fit: contain;
  max-height: 100%;
  transition: all 0.3s ease;
}

/* 问答区域 */
.qa-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #2a2a2a 0%, #1e272e 100%);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.qa-section:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
}

.qa-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(90deg, #409EFF, #67C23A);
  padding: 15px 20px;
  min-height: 30px;
  border-radius: 12px 12px 0 0;
  position: relative;
  overflow: hidden;
}

.qa-header::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, rgba(255,255,255,0.1) 25%, transparent 25%, transparent 50%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.1) 75%, transparent 75%, transparent);
  background-size: 10px 10px;
  opacity: 0.2;
  pointer-events: none;
}

.qa-header h3 {
  margin: 0;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  letter-spacing: 1px;
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
  gap: 15px;
  margin-bottom: 15px;
}

.qa-input .el-textarea {
  flex: 1;
}

.qa-input .el-textarea__inner {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.qa-input .el-textarea__inner:focus {
  border-color: #409EFF;
  box-shadow: 0 0 10px rgba(64, 158, 255, 0.3);
}

.qa-input .el-button {
  align-self: flex-start;
  background: linear-gradient(90deg, #409EFF, #67C23A);
  border: none;
  border-radius: 8px;
  padding: 12px 25px;
  font-weight: 600;
  letter-spacing: 1px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
}

.qa-input .el-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
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
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  padding: 15px;
  margin-bottom: 15px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.qa-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
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
  font-size: 18px;
  margin-top: 3px;
  background: rgba(255, 255, 255, 0.1);
  padding: 8px;
  border-radius: 50%;
  color: #409EFF;
}

.qa-item .answer .qa-icon {
  color: #67C23A;
}

.qa-text {
  flex: 1;
  color: #fff;
  line-height: 1.6;
  word-break: break-word;
  padding: 10px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  position: relative;
}

/* 侧边栏样式 */
.sidebar {
  position: fixed;
  top: 0;
  left: -300px; /* 使用固定宽度而不是百分比 */
  width: 300px;
  height: 100%;
  background: linear-gradient(135deg, #1a1a1a 0%, #2c3e50 100%);
  transition: all 0.3s ease;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 3px 0 15px rgba(0, 0, 0, 0.3);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-visible {
  left: 0;
}

.sidebar-toggle {
  position: fixed;
  top: 20px; /* 放在页面顶部而不是中间 */
  left: 20px;
  background: linear-gradient(135deg, #409EFF 0%, #67C23A 100%);
  color: #fff;
  padding: 12px;
  border-radius: 50%;
  cursor: pointer;
  z-index: 1001;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
}

.sidebar-toggle:hover {
  transform: scale(1.1);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: linear-gradient(90deg, #409EFF, #67C23A);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h3 {
  margin: 0;
  color: #fff;
  font-size: 20px;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  letter-spacing: 1px;
}

.close-icon {
  cursor: pointer;
  font-size: 20px;
  color: #fff;
  transition: transform 0.3s ease;
}

.close-icon:hover {
  transform: rotate(90deg);
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: linear-gradient(to bottom, rgba(0,0,0,0.2) 0%, rgba(0,0,0,0) 100%);
}

.sidebar-menu {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  border-radius: 10px;
  background-color: rgba(255, 255, 255, 0.08);
  color: #fff;
  cursor: pointer;
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
}

.menu-item:hover {
  background-color: rgba(255, 255, 255, 0.15);
  transform: translateX(5px);
  border-left: 3px solid #67C23A;
}

.menu-item .el-icon {
  font-size: 22px;
  color: #67C23A;
  background: rgba(255, 255, 255, 0.1);
  padding: 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.menu-item:hover .el-icon {
  transform: scale(1.1);
  color: #fff;
  background: #67C23A;
}

.menu-item span {
  font-size: 16px;
  font-weight: 500;
}

.menu-section {
  margin-top: 25px;
  margin-bottom: 20px;
}

.menu-section h4 {
  color: #fff;
  font-size: 18px;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 2px solid rgba(103, 194, 58, 0.5);
  position: relative;
  display: inline-block;
}

.menu-section h4:after {
  content: "";
  position: absolute;
  width: 40%;
  height: 2px;
  background: #67C23A;
  bottom: -2px;
  left: 0;
}

.video-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.video-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: 10px;
  background-color: rgba(255, 255, 255, 0.08);
  cursor: pointer;
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
  overflow: hidden;
}

.video-item:hover {
  background-color: rgba(255, 255, 255, 0.15);
  transform: translateX(5px);
  border-left: 3px solid #409EFF;
}

.video-thumbnail {
  width: 100px;
  height: 56px;
  background-color: #333;
  border-radius: 6px;
  background-size: cover;
  background-position: center;
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.video-item:hover .video-thumbnail {
  transform: scale(1.05);
}

.video-thumbnail:before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0) 50%, rgba(0,0,0,0.7) 100%);
}

.video-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 3px 0;
}

.video-title {
  font-size: 15px;
  color: #fff;
  margin-bottom: 8px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.3;
}

.video-duration {
  font-size: 13px;
  color: #67C23A;
  display: flex;
  align-items: center;
  gap: 5px;
}

.video-duration:before {
  content: "⏱";
  font-size: 12px;
}

.empty-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 15px;
  padding: 40px 0;
  color: rgba(255, 255, 255, 0.6);
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  border: 1px dashed rgba(255, 255, 255, 0.1);
}

.empty-list .el-icon {
  font-size: 40px;
  color: rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.05);
  padding: 15px;
  border-radius: 50%;
}

.empty-list span {
  font-size: 16px;
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
/* 美化滚动条 */
.subtitle-display::-webkit-scrollbar,
.qa-history::-webkit-scrollbar,
.sidebar-content::-webkit-scrollbar {
  width: 6px;
}

.subtitle-display::-webkit-scrollbar-track,
.qa-history::-webkit-scrollbar-track,
.sidebar-content::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.subtitle-display::-webkit-scrollbar-thumb,
.qa-history::-webkit-scrollbar-thumb,
.sidebar-content::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  transition: all 0.3s ease;
}

.subtitle-display::-webkit-scrollbar-thumb:hover,
.qa-history::-webkit-scrollbar-thumb:hover,
.sidebar-content::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.video-info {
  flex: 1;
  margin-bottom: 15px;
}

.video-info h3 {
  color: #fff;
  margin: 0 0 15px 0;
  font-size: 20px;
  font-weight: 600;
  padding-bottom: 10px;
  border-bottom: 2px solid rgba(64, 158, 255, 0.3);
  position: relative;
}

.video-info h3:after {
  content: "";
  position: absolute;
  left: 0;
  bottom: -2px;
  width: 50px;
  height: 2px;
  background: linear-gradient(90deg, #409EFF, #67C23A);
}

.video-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
  color: #ddd;
  font-size: 14px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  padding: 15px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.video-details p {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.video-details p:before {
  content: "•";
  color: #67C23A;
  font-size: 18px;
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
  background: rgba(0, 0, 0, 0.2);
  padding: 15px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.subtitle-download {
  display: flex;
  justify-content: center;
}

.subtitle-download .el-dropdown {
  width: 100%;
}

.subtitle-download .el-button {
  width: 100%;
  background: linear-gradient(90deg, #409EFF, #67C23A);
  border: none;
  border-radius: 8px;
  padding: 12px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
}

.subtitle-download .el-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 15px rgba(0, 0, 0, 0.3);
}

/* 加载和错误提示美化 */
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
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  z-index: 10;
  backdrop-filter: blur(5px);
  border-radius: 12px;
}

.loading-icon {
  font-size: 40px;
  margin-bottom: 15px;
  animation: spin 1.5s linear infinite;
  color: #409EFF;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon {
  font-size: 40px;
  margin-bottom: 15px;
  color: #F56C6C;
}

.loading-overlay span,
.error-overlay span {
  font-size: 16px;
  margin-bottom: 15px;
  text-align: center;
  max-width: 80%;
}

.error-overlay .el-button {
  background: linear-gradient(90deg, #409EFF, #67C23A);
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
}

.error-overlay .el-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 15px rgba(0, 0, 0, 0.3);
}

/* 侧边栏样式 */
.sidebar {
  position: fixed;
  top: 0;
  left: -25%;
  width: 25%;
  height: 100%;
  background-color: #1a1a1a;
  transition: left 0.3s ease;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-visible {
  left: 0;
}

.sidebar-toggle {
  position: fixed;
  top: 50%;
  left: 0;
  transform: translateY(-50%);
  background-color: #1a1a1a;
  color: #fff;
  padding: 15px 5px;
  border-radius: 0 4px 4px 0;
  cursor: pointer;
  z-index: 1001;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.2);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background-color: #2a2a2a;
  border-bottom: 1px solid #333;
}

.sidebar-header h3 {
  margin: 0;
  color: #fff;
  font-size: 16px;
}

.close-icon {
  cursor: pointer;
  font-size: 18px;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
}

.sidebar-section {
  margin-bottom: 20px;
}

.sidebar-section h4 {
  color: #ddd;
  margin: 0 0 10px 0;
  font-size: 14px;
  border-bottom: 1px solid #333;
  padding-bottom: 5px;
}

.chapter-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.chapter-list li {
  padding: 8px 10px;
  margin: 5px 0;
  background-color: #2a2a2a;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: flex-start;
  transition: background-color 0.2s;
}

.chapter-list li:hover {
  background-color: #333;
}

.chapter-list li.active {
  background-color: #409eff;
}

.chapter-time {
  color: #aaa;
  font-size: 12px;
  margin-right: 10px;
  min-width: 45px;
}

.chapter-title {
  color: #fff;
  font-size: 13px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.left-section.with-sidebar {
  margin-left: 25%;
  transition: margin-left 0.3s ease;
}

/* 侧边栏菜单样式 */
.sidebar-menu {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 15px;
  background-color: #2a2a2a;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.menu-item:hover {
  background-color: #333;
}

.menu-item .el-icon {
  font-size: 18px;
  color: #409eff;
}

.menu-item span {
  color: #fff;
  font-size: 14px;
}

.menu-section {
  margin-top: 20px;
  margin-bottom: 20px;
}

.menu-section h4 {
  color: #ddd;
  margin: 0 0 10px 0;
  font-size: 14px;
  border-bottom: 1px solid #333;
  padding-bottom: 5px;
}

.video-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.video-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background-color: #2a2a2a;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.video-item:hover {
  background-color: #333;
}

.video-thumbnail {
  width: 60px;
  height: 40px;
  background-color: #333;
  background-size: cover;
  background-position: center;
  border-radius: 4px;
  flex-shrink: 0;
}

.video-info {
  flex: 1;
  overflow: hidden;
}

.video-title {
  color: #fff;
  font-size: 13px;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.video-duration {
  color: #aaa;
  font-size: 12px;
}

.empty-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background-color: #2a2a2a;
  border-radius: 6px;
  color: #aaa;
  gap: 10px;
}

.empty-list .el-icon {
  font-size: 24px;
  color: #555;
}
</style>
