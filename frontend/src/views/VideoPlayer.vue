<template>
  <div class="video-player-container" :class="{ 'with-sidebar': sidebarVisible }">
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
            <el-icon class="arrow-icon"><arrow-right /></el-icon>
          </div>
          <div class="menu-item" @click="navigateToVideoUpload">
            <el-icon><video-camera /></el-icon>
            <span>分析新视频</span>
            <el-icon class="arrow-icon"><arrow-right /></el-icon>
          </div>
          <div class="menu-item" @click="navigateToGuide">
            <el-icon><document /></el-icon>
            <span>使用指南</span>
            <el-icon class="arrow-icon"><arrow-right /></el-icon>
          </div>
          
          <!-- 已分析视频列表 -->
          <div class="menu-section">
            <h4>已分析视频</h4>
            <div class="video-list custom-scrollbar" v-if="processedVideos.length > 0">
              <div class="video-item" 
                   v-for="video in processedVideos" 
                   :key="video.id"
                   :class="{ 'current-playing': video.id === Number(videoId) }"
                   @click="navigateToVideo(video.id)">
                <div class="video-thumbnail" :style="video.thumbnail ? `background-image: url(${video.thumbnail})` : ''"></div>
                <div class="video-info">
                  <div class="video-title" :title="video.title || '未命名视频'">{{ video.title || '未命名视频' }}</div>
                  <div class="video-duration">{{ formatDuration(video.duration) }}</div>
                </div>
                <el-icon class="arrow-icon"><arrow-right /></el-icon>
              </div>
            </div>
            <div class="empty-list" v-else>
              <el-icon><video-camera /></el-icon>
              <span>暂无已处理视频</span>
            </div>
          </div>
          
          
          <div class="menu-item" @click="navigateToKnowledgeGraph">
            <el-icon><connection /></el-icon>
            <span>知识点总览</span>
            <el-icon class="arrow-icon"><arrow-right /></el-icon>
          </div>
          <div class="menu-item" @click="navigateToNoteSystem">
            <el-icon><edit /></el-icon>
            <span>笔记系统</span>
            <el-icon class="arrow-icon"><arrow-right /></el-icon>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 左侧区域 -->
    <div class="left-section" :class="{ 'with-sidebar': sidebarVisible }">
      <!-- 左侧上方区域：视频名称和视频播放区域的上下布局 -->
      <div class="upper-section">
        <!-- 视频名称和显示字幕按钮 -->
        <div class="video-title-area">
          <h3 class="video-title" :title="videoTitle">{{ videoTitle }}</h3>
          <el-switch
            v-model="showSubtitles"
            active-text="显示字幕"
            inactive-text="隐藏字幕"
            size="small"
            @change="toggleSubtitles"
            class="subtitle-toggle-switch"
          />
        </div>
        
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
      </div>
      
      <!-- 下方区域：智能问答区域 -->
      <div class="lower-section">
        <div class="qa-container">
          <div class="qa-section">
            <div class="qa-header">
              <h3>
                智能问答
                <el-tag 
                  size="small" 
                  :type="useOllama ? 'success' : 'primary'"
                  effect="dark"
                  class="mode-tag"
                >
                  {{ useOllama ? '离线模式' : '在线模式' }}
                </el-tag>
              </h3>
              <div class="qa-mode-switch">
                <div class="qa-mode-buttons">
                  <el-button 
                    size="small" 
                    :type="qaMode === 'video' ? 'primary' : 'default'"
                    round
                    @click="toggleQaMode"
                  >
                    与视频对话
                  </el-button>
                </div>
              </div>
              <div class="qa-header-actions">
                <el-switch
                  v-model="useOllama"
                  active-text="离线模式"
                  inactive-text="在线模式"
                  size="small"
                  style="margin-right: 10px;"
                  :active-value="true"
                  :inactive-value="false"
                />
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
              <!-- 添加模式提示信息区域，只在没有问答历史记录时显示 -->
              <div class="qa-mode-info" v-if="qaHistory.length === 0">
                <el-alert
                  :title="getModeTitle"
                  :description="getModeDescription"
                  :type="useOllama ? 'success' : 'info'"
                  :closable="false"
                  show-icon
                />
              </div>
              <div class="qa-history">
                <ul>
                  <li v-for="(item, index) in qaHistory" :key="index" class="qa-item">
                    <div class="question">
                      <span class="qa-text">{{ item.question }}</span>
                      <el-icon class="qa-icon"><User /></el-icon> <!-- 用户图标 -->
                    </div>
                    <div class="answer">
                      <el-icon class="qa-icon"><Monitor /></el-icon> <!-- 智能分析图标 -->
                      <span class="qa-text formatted-answer" v-html="sanitizeHtml(item.answer)"></span>
                    </div>
                  </li>
                </ul>
              </div>
              <div class="qa-input">
                <div class="qa-input-options">
                  <div class="thinking-mode-button" @click="toggleDeepThinking">
                    <el-button 
                      size="small" 
                      :type="deepThinking ? 'primary' : 'default'"
                      :icon="deepThinking ? 'Brain' : ''"
                      round
                    >
                      深度思考
                    </el-button>
                  </div>
                </div>
                <el-input 
                  v-model="question" 
                  :placeholder="getPlaceholderByMode" 
                  type="textarea" 
                  :rows="2" 
                />
                <el-button type="primary" @click="askQuestion" :loading="isAsking">提问</el-button>
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
          <div class="subtitle-controls">
            <!-- 字幕控制按钮区域 -->
            <div class="subtitle-buttons-row">
              <!-- 左侧：字幕模式选择 -->
              <div class="subtitle-left-buttons">
                <el-button 
                  :type="subtitleMode === 'merged' ? 'primary' : 'purple'" 
                  size="small" 
                  @click="toggleSubtitleMode"
                  :class="{'subtitle-mode-button': true, 'purple-button': subtitleMode !== 'merged'}"
                >
                  {{ subtitleMode === 'merged' ? '语义合并字幕' : '标准分段字幕' }}
                </el-button>
              </div>
              
              <!-- 右侧：字幕下载和重新合并按钮 -->
              <div class="subtitle-right-buttons">
                <!-- 字幕下载 -->
                <el-dropdown>
                  <el-button type="primary" size="small" class="download-button">
                    下载字幕<el-icon class="el-icon--right"><arrow-down /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="downloadSubtitle('srt', true)">下载SRT字幕</el-dropdown-item>
                      <el-dropdown-item @click="downloadSubtitle('vtt', true)">下载VTT字幕</el-dropdown-item>
                      <el-dropdown-item @click="downloadSubtitle('txt', true)">下载TXT字幕</el-dropdown-item>
                      <el-dropdown-item @click="downloadMergedSubtitle('txt', true)">语义合并字幕</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
                
                <!-- 重新合并字幕 -->
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="refreshMergedSubtitles" 
                  :loading="mergeSubtitlesLoading"
                >
                  重新合并字幕
                </el-button>
              </div>
            </div>
          </div>
        </div>
      
        <div class="subtitle-display">
          <template v-if="subtitleMode === 'full'">
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
          <template v-else>
            <div class="subtitle-content" v-if="mergedSubtitles.length">
              <div v-for="(section, index) in mergedSubtitles" :key="index" 
                   :class="['subtitle-item', 'merged-item', { 'current': isCurrentMergedSubtitle(section) }]">
                <div class="subtitle-header">
                  <span class="subtitle-time">{{ formatTimeMMSS(section.start_time) }} - {{ formatTimeMMSS(section.end_time) }}</span>
                  <h4 class="subtitle-title">{{ section.title }}</h4>
                </div>
                <p class="subtitle-text" style="white-space: pre-line">{{ section.text }}</p>
              </div>
            </div>
            <div class="subtitle-placeholder" v-else>
              正在加载合并字幕...
            </div>
          </template>
        </div>
      </div>
    </div>
    
    <!-- 帮助文档对话框 -->
    <el-dialog
      v-model="helpDialogVisible"
      title="视频智能伴学系统 使用帮助"
      width="60%"
      :before-close="closeHelpDialog"
      v-if="false"
    >
      <div class="help-content">
        <h3>欢迎使用视频智能伴学系统</h3>
    
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
    
    <!-- 功能引导提示弹窗 -->
    <el-dialog
      v-model="showGuideDialog"
      title="功能引导"
      width="400px"
      :show-close="true"
      :close-on-click-modal="true"
      :close-on-press-escape="true"
    >
      <div class="guide-content">
        <h3>欢迎使用视频智能伴学系统</h3>
        
        <div class="guide-section">
          <h4><el-icon><edit /></el-icon> 记录学习笔记</h4>
          <p>想要记录学习笔记？只需点击左上角的侧边栏按钮 <el-icon><arrow-right /></el-icon>，然后选择"笔记系统"即可进入笔记页面。</p>
        </div>
        
        <div class="guide-section">
          <h4>侧边栏其他功能</h4>
          <ul>
            <li><el-icon><home-filled /></el-icon> <strong>返回首页</strong>：回到系统主页</li>
            <li><el-icon><video-camera /></el-icon> <strong>分析新视频</strong>：上传并分析新的视频</li>
            <li><el-icon><document /></el-icon> <strong>帮助文档</strong>：查看系统使用帮助</li>
          </ul>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-checkbox v-model="dontShowGuideAgain">不再显示</el-checkbox>
          <el-button type="primary" @click="closeGuideDialog">我知道了</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import DOMPurify from 'dompurify';
import { ref, onMounted, computed, watch, onUnmounted , nextTick  } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElLoading, ElMessageBox } from 'element-plus';
import { 
  Loading, Warning, FullScreen, Close, User, Monitor, 
  QuestionFilled, ChatLineSquare, ArrowDown as ArrowDown,
  ArrowRight, ArrowLeft, HomeFilled, VideoCamera, Document, Edit as Edit,
  Connection
} from '@element-plus/icons-vue';
import { getVideo, getSubtitle, getVideoList, getVideoPreview } from '@/api/video';
import { askQuestionStream } from '@/api/qa';
import request from '@/utils/request';

const route = useRoute();
const router = useRouter();
const videoId = computed(() => route.params.id);
const videoPlayer = ref(null);
const qaDialog = ref(null);

const sanitizeHtml = (html) => {
  if (!html) return '';
  return DOMPurify.sanitize(html);
};

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
const subtitleMode = ref('merged');
const fullSubtitles = ref([]);
const mergedSubtitles = ref([]);
const showMergedSubtitles = ref(false);
const mergeSubtitlesLoading = ref(false);

// 问答状态
const qaMode = ref('video');
const useOllama = ref(false); // 是否使用Ollama离线模式
const deepThinking = ref(false); // 是否深度思考
const question = ref('');
// 界面状态
const sidebarVisible = ref(false); // 侧边栏是否可见
const helpDialogVisible = ref(false); // 帮助对话框是否可见
const isAsking = ref(false);
const processedVideos = ref([]); // 初始化为空数组
// API密钥
const apiKey = ref('sk-178e130a121445659860893fdfae1e7d'); // 设置为固定值
// 分别为两种模式创建独立的历史记录数组，并从localStorage中恢复数据
const videoQaHistory = ref(JSON.parse(localStorage.getItem(`videoQaHistory_${videoId.value}`) || '[]'));
const freeQaHistory = ref(JSON.parse(localStorage.getItem('freeQaHistory') || '[]'));
// 计算属性：根据当前模式返回对应的历史记录
const qaHistory = computed(() => {
  return qaMode.value === 'video' ? videoQaHistory.value : freeQaHistory.value;
});

// 监听历史记录变化，保存到localStorage
watch(videoQaHistory, (newHistory) => {
  localStorage.setItem(`videoQaHistory_${videoId.value}`, JSON.stringify(newHistory));
}, { deep: true });

watch(freeQaHistory, (newHistory) => {
  localStorage.setItem('freeQaHistory', JSON.stringify(newHistory));
}, { deep: true });

// 监听videoId变化，更新视频相关的问答历史
watch(videoId, (newVideoId) => {
  if (newVideoId) {
    videoQaHistory.value = JSON.parse(localStorage.getItem(`videoQaHistory_${newVideoId}`) || '[]');
  }
});

// 监听问答模式变化
watch(qaMode, (newMode) => {
  console.log(`问答模式切换为: ${newMode}`);
  // 显示切换模式的提示
  ElMessage.info(`已切换到${newMode === 'video' ? '基于视频内容的问答模式' : '自由问答模式'}`);
});

// 监听模式切换
watch(useOllama, (newValue) => {
  if (newValue) {
    ElMessage.success('已切换到离线模式，使用本地Ollama服务');
  } else {
    ElMessage.info('已切换到在线模式，使用云端服务');
  }
});

// 监听深度思考模式切换
watch(deepThinking, (newValue) => {
  if (newValue) {
    ElMessage.success('已启用深度思考模式，回答将更加全面但需要更多时间');
  } else {
    ElMessage.info('已切换到快速回答模式，回答将更加简洁');
  }
});

// 监听字幕模式变化
watch(subtitleMode, (newMode) => {
  console.log('字幕模式切换为:', newMode);
  // 不再自动加载合并字幕，避免重复请求
});

// 切换字幕模式的方法
const toggleSubtitleMode = () => {
  subtitleMode.value = subtitleMode.value === 'merged' ? 'full' : 'merged';
  ElMessage.info(`已切换到${subtitleMode.value === 'merged' ? '语义合并字幕' : '标准分段字幕'}模式`);
};

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

// 导航到知识点总览页面
const navigateToKnowledgeGraph = () => {
  router.push('/knowledge');
};

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

// 在data部分添加新的状态变量
const loadMergedSubtitles = async (retryCount = 0, maxRetries = 3, force = false) => {
  console.log('开始加载合并字幕，视频ID:', videoId.value, '强制刷新:', force);
  mergeSubtitlesLoading.value = true;
  try {
    // 构建API URL，添加force_refresh参数
    const apiUrl = `/api/subtitles/videos/${videoId.value}/subtitles/semantic-merged${force ? '?force_refresh=true' : ''}`;
    console.log('请求API:', apiUrl);
    
    // 显示加载提示
    const loadingMessage = ElMessage({
      message: '正在处理视频字幕，这可能需要几分钟时间...',
      type: 'info',
      duration: 0,
      showClose: true
    });
    
    const response = await request({
      url: apiUrl,
      method: 'get'
    });
    
    // 关闭加载提示
    loadingMessage.close();
    
    console.log('合并字幕API响应:', response);
    
    if (response && response.data) {
      if (Array.isArray(response.data) && response.data.length > 0) {
        console.log(`成功加载${response.data.length}条合并字幕`);
        mergedSubtitles.value = response.data;
        ElMessage.success(`成功加载${response.data.length}条语义合并字幕${force ? ' (重新合并)' : ''}`);
      } else {
        console.warn('服务器返回了空的合并字幕数组');
        mergedSubtitles.value = [];
        ElMessage.warning('没有找到可合并的字幕');
      }
    } else {
      console.warn('合并字幕响应无效');
      mergedSubtitles.value = [];
      ElMessage.warning('获取合并字幕失败');
    }
  } catch (error) {
    console.error('加载合并字幕失败:', error);
    
    // 检查是否是404错误（语义合并字幕不存在）
    if (error.response && error.response.status === 404) {
      console.log('语义合并字幕不存在，自动触发语义合并处理');
      
      // 显示单一提示信息
      ElMessage.info('语义合并字幕生成中，请稍候...');
      
      // 自动触发语义合并
      try {
        await triggerSemanticMerge();
        return; // 提前返回，避免设置 mergedSubtitles.value = []
      } catch (mergeError) {
        console.error('自动触发语义合并失败:', mergeError);
        // 失败时才显示错误信息
        ElMessage.error('语义合并处理失败，请稍后再试');
      }
    }
    
    mergedSubtitles.value = [];
    ElMessage.error(`加载合并字幕失败: ${error.message || '未知错误'}`);
  } finally {
    mergeSubtitlesLoading.value = false;
  }
};

// 切换深度思考模式
const toggleDeepThinking = () => {
  deepThinking.value = !deepThinking.value;
};

// 切换问答模式
const toggleQaMode = () => {
  qaMode.value = qaMode.value === 'video' ? 'free' : 'video';
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

// 注意：现在使用el-switch的@change事件直接调用toggleSubtitles方法
// 不再需要toggleSubtitlesDisplay方法

// 检查是否为当前字幕
const isCurrentSubtitle = (subtitle) => {
  if (!videoPlayer.value) return false;
  const currentTime = videoPlayer.value.currentTime;
  return currentTime >= subtitle.startTime && currentTime <= subtitle.endTime;
};

// 检查是否为当前合并字幕
const isCurrentMergedSubtitle = (section) => {
  if (!videoPlayer.value) return false;
  const currentTime = videoPlayer.value.currentTime;
  return currentTime >= section.start_time && currentTime <= section.end_time;
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

// 下载合并字幕
const downloadMergedSubtitle = async (format, showMessage = false) => {
  try {
    const response = await request({
      url: `/api/subtitles/videos/${videoId.value}/subtitles/semantic-merged?format=${format}`,
      method: 'get',
      responseType: 'blob'
    });
    // 从response中获取blob数据
    const blob = response.data;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    // 使用与后端一致的文件名格式：local-视频标题.格式
    a.download = `local-${videoTitle.value}-merged.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    if (showMessage) {
      ElMessage.success(`合并${format.toUpperCase()} 字幕下载成功`);
    }
  } catch (error) {
    console.error(`下载合并 ${format} 字幕失败:`, error);
    ElMessage.error(`下载合并 ${format} 字幕失败，请重试`);
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

// 触发语义合并操作
const triggerSemanticMerge = async () => {
  try {
    ElMessage.info('正在启动语义合并处理，这可能需要几分钟时间...');
    
    // 发送POST请求触发语义合并
    const response = await request({
      url: `/api/subtitles/videos/${videoId.value}/subtitles/semantic-merge`,
      method: 'post'
    });
    
    if (response && response.data && response.data.success) {
      ElMessage.success('语义合并操作已启动，请稍候...');
      // 等待几秒后尝试加载合并字幕
      setTimeout(() => {
        loadMergedSubtitles();
      }, 5000);
    } else {
      ElMessage.error('启动语义合并操作失败');
    }
  } catch (error) {
    console.error('启动语义合并操作失败:', error);
    ElMessage.error(`启动语义合并操作失败: ${error.message || '未知错误'}`);
  }
};

// 重新合并字幕
const refreshMergedSubtitles = async () => {
  // 显示确认对话框
  ElMessageBox.confirm(
    '确定要重新合并字幕吗？这将重新处理视频字幕，可能需要几分钟时间。',
    '确认操作',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(async () => {
      mergeSubtitlesLoading.value = true;
      try {
        // 用户确认后调用触发语义合并的函数
        await triggerSemanticMerge();
      } finally {
        mergeSubtitlesLoading.value = false;
      }
    })
    .catch(() => {
      // 用户取消操作
      ElMessage.info('已取消重新合并字幕操作');
    });
};

// 问答功能
const askQuestion = async () => {
  if (!question.value.trim()) {
    ElMessage.warning('请输入问题');
    return;
  }
  
  if (isAsking.value) {
    ElMessage.warning('正在回答中，请稍候...');
    return;
  }
  
  const questionText = question.value.trim();
  isAsking.value = true;
  
  try {
    let answer = '';
    let currentQuestionIndex = -1; // 用于存储当前问题的索引，避免因切换模式后询问相同的问题导致错误
    
    // 添加问题到历史记录
    if (qaMode.value === 'video') {
      videoQaHistory.value.push({
        question: questionText,
        answer: useOllama.value ? '正在思考...' : '正在连接AI服务...',
        timestamp: new Date().toLocaleString(),
        deepThinking: deepThinking.value // 记录是否使用深度思考模式
      });
      currentQuestionIndex = videoQaHistory.value.length - 1; // 记录索引
    } else {
      freeQaHistory.value.push({
        question: questionText,
        answer: useOllama.value ? '正在思考...' : '正在连接AI服务...',
        timestamp: new Date().toLocaleString(),
        deepThinking: deepThinking.value // 记录是否使用深度思考模式
      });
      currentQuestionIndex = freeQaHistory.value.length - 1; // 记录索引
    }
    // 滚动到底部
    scrollToBottom();

    console.log('使用的API服务:', useOllama.value ? 'Ollama本地服务' : '在线API服务');
    // 使用视频ID或null，取决于当前问答模式
    const videoIdParam = qaMode.value === 'video' ? videoId.value : null;
    
    console.log('开始提问:', {
      问题: questionText,
      模式: qaMode.value,
      视频ID: videoIdParam,
      使用离线模式: useOllama.value,
      深度思考: deepThinking.value
    });
    
    // 设置超时检查，如果30秒后仍然显示"正在思考..."，则更新为错误消息
    let timeoutId = null;
    if (useOllama.value) {
      timeoutId = setTimeout(() => {
        console.warn('Ollama响应超时检查');
        // 检查是否仍然显示"正在思考..."
        if (qaMode.value === 'video') {
          const lastIndex = videoQaHistory.value.findIndex(item => item.question === questionText);
          if (lastIndex >= 0 && videoQaHistory.value[lastIndex].answer === '正在思考...') {
            console.error('Ollama响应超时');
            videoQaHistory.value[lastIndex].answer = '无法获取回答，请检查Ollama服务是否正常运行，或尝试使用在线模式。';
          }
        } else {
          const lastIndex = freeQaHistory.value.findIndex(item => item.question === questionText);
          if (lastIndex >= 0 && freeQaHistory.value[lastIndex].answer === '正在思考...') {
            console.error('Ollama响应超时');
            freeQaHistory.value[lastIndex].answer = '无法获取回答，请检查Ollama服务是否正常运行，或尝试使用在线模式。';
          }
        }
      }, 30000); // 30秒超时
    }
    
    // 使用新的流式问答API
    await askQuestionStream(
      {
        question: questionText,
        video_id: videoIdParam,
        api_key: useOllama.value ? "" : "sk-178e130a121445659860893fdfae1e7d", // 使用固定API密钥
        mode: qaMode.value,
        use_ollama: useOllama.value, // 确保使用.value获取响应式值
        deep_thinking: deepThinking.value // 添加深度思考模式
      },
      {
        onData: (data) => {
          // 如果收到数据，清除超时检查
          if (timeoutId) {
            clearTimeout(timeoutId);
            timeoutId = null;
          }
          
          // 如果收到空字符串，跳过处理
          if (data === "") {
            console.log('收到空字符串，跳过处理');
            return;
          }

          answer = data;
          console.log('收到回答:', answer.substring(0, 50) + '...');
          
          // 检查是否包含深度思考的格式化回答（通常包含<details>标签）
          const isFormattedAnswer = data.includes('<details>') && data.includes('</details>');
          
          // 实时更新最新的回答到历史记录
          if (qaMode.value === 'video' && currentQuestionIndex >= 0) {
            videoQaHistory.value[currentQuestionIndex].answer = answer;
          } else if (qaMode.value !== 'video' && currentQuestionIndex >= 0) {
            freeQaHistory.value[currentQuestionIndex].answer = answer;
          }
          // 滚动到底部
          scrollToBottom();
        },
        onError: (error) => {
          // 如果发生错误，清除超时检查
          if (timeoutId) {
            clearTimeout(timeoutId);
            timeoutId = null;
          }
          
          console.error('提问失败:', error);
          ElMessage.error('提问失败，请重试');
          
          // 更新错误信息到历史记录
          if (qaMode.value === 'video' && currentQuestionIndex >= 0) {
            videoQaHistory.value[currentQuestionIndex].answer = `提问失败: ${error}`;
          } else if (qaMode.value !== 'video' && currentQuestionIndex >= 0) {
            freeQaHistory.value[currentQuestionIndex].answer = `提问失败: ${error}`;
          }
        },
        onComplete: () => {
          // 完成时清除超时检查
          if (timeoutId) {
            clearTimeout(timeoutId);
            timeoutId = null;
          }
          
          question.value = '';
          console.log('问答完成');
          // 滚动到底部
          scrollToBottom();
        }
      }
    );
  } catch (error) {
    console.error('提问失败:', error);
    ElMessage.error('提问失败，请重试');
    
    // 更新错误信息到历史记录
    if (qaMode.value === 'video' && currentQuestionIndex >= 0) {
      videoQaHistory.value[currentQuestionIndex].answer = `提问失败: ${error}`;
    } else if (qaMode.value !== 'video' && currentQuestionIndex >= 0) {
      freeQaHistory.value[currentQuestionIndex].answer = `提问失败: ${error}`;
    }
  } finally {
    isAsking.value = false;
  }
};

// 清空聊天记录
const clearChat = () => {
  // 根据当前模式清空对应的历史记录
  if (qaMode.value === 'video') {
    videoQaHistory.value = [];
    localStorage.removeItem(`videoQaHistory_${videoId.value}`);
  } else {
    freeQaHistory.value = [];
    localStorage.removeItem('freeQaHistory');
  }
  question.value = '';
  ElMessage.success('聊天记录已清空');
};

// 滚动问答历史到底部
const scrollToBottom = () => {
  nextTick(() => {
    const qaHistoryElement = document.querySelector('.qa-history');
    if (qaHistoryElement) {
      qaHistoryElement.scrollTop = qaHistoryElement.scrollHeight;
    }
  });
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
    videoPlayer.value.addEventListener('timeupdate', () => {});
  }
};

// 组件挂载
onMounted(async () => {
  // 检查是否需要显示功能引导弹窗
  const dontShowGuide = localStorage.getItem('dontShowGuideAgain');
  if (!dontShowGuide) {
    // 延迟显示引导弹窗，等待页面加载完成
    setTimeout(() => {
      showGuideDialog.value = true;
    }, 1500);
  }
  
  // 加载视频信息
  await loadVideoInfo();
  
  // 加载字幕
  await loadSubtitles();
  
  // 加载已处理视频列表
  await fetchProcessedVideos();
  
  // 加载合并字幕
  await loadMergedSubtitles();
  
  // 检查URL参数中是否有时间戳
  const timeParam = route.query.t;
  if (timeParam) {
    // 将字符串转换为数字
    const timeInSeconds = parseFloat(timeParam);
    if (!isNaN(timeInSeconds)) {
      // 等待视频加载完成后再跳转
      setTimeout(() => {
        seekToTime(timeInSeconds);
      }, 1000);
    }
  }
  
  // 检查URL参数中是否有自动问题
  const autoQuestion = route.query.auto_question;
  if (autoQuestion) {
    // 设置问答模式为基于视频内容问答
    qaMode.value = 'video';
    // 设置为离线模式
    useOllama.value = true;
    
    // 等待视频加载完成后再自动提问
    setTimeout(async () => {
      // 将问题设置到输入框
      question.value = autoQuestion;
      // 自动提交问题
      await askQuestion();
      
      // 显示提示信息
      ElMessage.success('已自动发送知识点相关问题');
      
      // 检查是否有其他存储的问题
      const storedQuestions = localStorage.getItem(`concept_questions_${videoId.value}_${decodeURIComponent(autoQuestion).split('?')[0]}`);
      if (storedQuestions) {
        try {
          const questions = JSON.parse(storedQuestions);
          if (questions && questions.length > 0) {
            // 展示提示消息，提示用户还有其他可以提问的问题
            setTimeout(() => {
              ElNotification({
                title: '其他推荐问题',
                message: `您还可以尝试提问：${questions.join(' | ')}`,
                type: 'info',
                duration: 10000
              });
            }, 5000); // 等待几秒后再显示，避免信息过多
          }
        } catch (e) {
          console.error('解析存储的问题失败:', e);
        }
      }
    }, 2000);
  }
  
  setupTimeUpdateListener();
});

// 根据当前模式获取输入框提示文本
const getPlaceholderByMode = computed(() => {
  if (qaMode.value === 'video') {
    if (deepThinking.value) {
      return useOllama.value 
        ? "请输入关于视频内容的问题（深度思考模式）..." 
        : "请输入关于视频内容的问题（深度思考模式）...";
    } else {
      return useOllama.value 
        ? "请输入关于视频内容的问题..." 
        : "请输入关于视频内容的问题...";
    }
  } else {
    if (deepThinking.value) {
      return useOllama.value 
        ? "请输入任何问题（深度思考模式）..." 
        : "请输入任何问题（深度思考模式）...";
    } else {
      return useOllama.value 
        ? "请输入任何问题..." 
        : "请输入任何问题...";
    }
  }
});
// 获取模式标题
const getModeTitle = computed(() => {
  if (qaMode.value === 'video') {
    return deepThinking.value 
      ? "基于视频内容的深度思考模式" 
      : "基于视频内容的问答模式";
  } else {
    return deepThinking.value 
      ? "自由问答的深度思考模式" 
      : "自由问答模式";
  }
});

// 获取模式描述
const getModeDescription = computed(() => {
  if (qaMode.value === 'video') {
    if (deepThinking.value) {
      return useOllama.value 
        ? "AI将分析视频内容并展示详细思考过程（离线模式）" 
        : "AI将分析视频内容并展示详细思考过程（在线模式）";
    } else {
      return useOllama.value 
        ? "可提问：视频主要讲了什么？关键概念是什么？（离线模式）" 
        : "可提问：视频主要讲了什么？关键概念是什么？（在线模式）";
    }
  } else {
    if (deepThinking.value) {
      return useOllama.value 
        ? "可提问任何问题，AI将展示详细思考过程（离线模式）" 
        : "可提问任何问题，AI将展示详细思考过程（在线模式）";
    } else {
      return useOllama.value 
        ? "自由提问模式，不限于视频内容（离线模式）" 
        : "自由提问模式，不限于视频内容（在线模式）";
    }
  }
});

// 导航到笔记系统
const navigateToNoteSystem = () => {
  router.push({
    path: '/notes',
    query: { videoId: videoId.value }
  });
};

// 导航到使用指南
const navigateToGuide = () => {
  router.push({
    path: '/guide',
    query: { videoId: videoId.value }
  });
};

// 功能引导提示弹窗相关状态
const showGuideDialog = ref(false);
const dontShowGuideAgain = ref(false);

// 关闭功能引导提示弹窗
const closeGuideDialog = () => {
  showGuideDialog.value = false;
  if (dontShowGuideAgain.value) {
    localStorage.setItem('dontShowGuideAgain', 'true');
  }
};
</script>

<style scoped>
/*视频播放容器*/
.video-player-container {
  --primary-color: #3CAEA3;
  --primary-light: rgba(60, 174, 163, 0.2);
  --text-primary: #2C3E50;
  --text-secondary: #8492A6;
  --bg-primary: #FFFFFF;
  --bg-secondary: #F5F8FA;
  --border-color: #E5E9F2;
  --transition-default: all 0.3s ease;
  --indigo-600: #4F46E5;
  --indigo-400: #818CF8;
  --indigo-100: #E0E7FF;
  --primary-gradient: linear-gradient(135deg, #f5f7fa, #ffffff);
  display: flex;
  height: 100vh;
  width: 90% !important;
  margin: 0 auto !important;
  overflow: hidden;
  position: relative;
  background: #f8f9fa;
  color: #333;
}


/*左侧区域*/
.left-section {
  flex: 0.98;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  width: 58%; /* 略微减小宽度，为间隔留出空间 */
  height: 100%;
  overflow: hidden;
  background-color: transparent;
}

.left-section.with-sidebar {
  width: 48%; /* 侧边栏打开时宽度变为48% */
  margin-left: 17%; /* 左边距为侧边栏宽度 */
}

/*上方区域*/
.upper-section {
  display: flex;
  flex-direction: column;
  height: 45%;
  width: 98%;
  margin-bottom: 5px;
}

/* 视频标题区域 */
.video-title-area {
  padding: 5px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 30px;
}

.video-title {
  margin: 0;
  color: #333;
  font-weight: 600;
  font-size: 15px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  position: relative;
  padding-left: 12px;
  flex: 1;
}

.subtitle-toggle-switch {
  margin-left: 10px;
  flex-shrink: 0;
}

.video-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 15px;
  background: linear-gradient(to bottom, #3CAEA3, #2a9d8f);
  border-radius: 2px;
}

/*视频主区域*/
.video-main-area {
  flex: 1;
  padding: 15px; 
  overflow: hidden;
}

.video-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  background: #ffffff;
  transition: all 0.3s ease;
  border: 3px solid #ff9a9e; /* 添加粉色边框 */
}

.video-section {
  width: 100%;
  height: 100%;
  position: relative;
  background: #ffffff;
  border-radius: 12px;
  overflow: hidden;
}

/*视频元素*/
.video-element {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background-color: transparent;
}

/*视频播放区域*/
.video-player-area {
  flex: 0.43; 
  padding: 15px;
  overflow: hidden;
}



/*字幕控制*/
.subtitle-controls-card {
  background: linear-gradient(135deg, #f5f7fa, #e4e7eb);
  border-radius: 7px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.subtitle-control-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.subtitle-control-item:last-child {
  border-bottom: none;
}

.control-label {
  font-weight: 500;
  color: #606266;
}

.custom-switch {
  --el-switch-on-color: #1e3c72;
}

.download-button {
  background: var(--indigo-400);
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.download-button:hover {
  background-color: var(--indigo-400);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

/* 合并字幕样式 */
.merged-item {
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 8px;
  background: var(--primary-light);
  transition: all 0.3s ease;
}

/* 移除合并字幕项悬停效果 */

.subtitle-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 5px;
  border-bottom: 1px solid rgba(42, 82, 152, 0.2);
}

.subtitle-title {
  font-weight: bold;
  color: #1a1a1a; /* 接近黑色但不那么刺眼 */
  margin: 0;
  font-size: 1.1em;
}

/*下方区域*/
.lower-section {
  flex: 1;
  padding: 0 15px 15px;
  overflow-y: auto;
}

/*问答容器*/
.qa-container {
  height: 98%;
  width: 98%;
  border-radius: 12px;
  overflow: hidden; 
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  background: #ffffff;
  transition: all 0.3s ease;
  border: 2px solid #ff9a9e; /* 添加粉色边框 */
}

/* 移除智能问答区域卡片悬停效果 */

.qa-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 12px;
  overflow-y: hidden;
  height: 100%;
}

.qa-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px;
  background: #f5f7fa;
  color: #333;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  position: relative;
}

.qa-header h3 {
  margin: 0;
  font-weight: 600;
  padding-left: 15px;
  position: relative;
}

.qa-header h3::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 18px;
  background: linear-gradient(to bottom, #a1c4fd, #c2e9fb);
  border-radius: 2px;
}

.qa-mode-switch {
  margin: 0 15px;
}

.qa-header-actions {
  display: flex;
  gap: 10px;
}

.qa-input {
  display: flex;
  gap: 8px;
  padding: 8px;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.qa-input .el-input {
  flex: 1;
}

.qa-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 10px;
  overflow: hidden; /* 改为hidden，避免双滚动条 */
  height: 100%; /* 确保有高度 */
}

.qa-history {
  flex: 1;
  overflow-y: auto;
  padding-right: 10px;
  margin-bottom: 10px; /* 为底部输入框留出空间 */
}

.qa-history ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.qa-item {
  margin-bottom: 20px;
  width: 100%;
}

.question, .answer {
  display: flex;
  align-items: flex-start;
  margin-bottom: 10px;
  padding: 10px;
  border-radius: 8px;
  width: 100%;
  box-sizing: border-box;
}

.answer {
  background-color: #ecf5ff;
  margin-right: auto; /* 回答靠左对齐 */
  margin-left: 0;
  max-width: 80%; /* 限制宽度 */
  border-top-left-radius: 5px;
  border-top-right-radius: 15px;
  border-bottom-left-radius: 15px;
  border-bottom-right-radius: 15px;
  background: #fef9d2; /* 修改为浅黄色背景 */
  color: #333; /* 深色文字，提高可读性 */
}

.answer .qa-icon {
  color: #333; /* 图标颜色改为深色，与文字匹配 */
}

.answer-header {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
}

.deep-thinking-tag {
  margin-left: 8px;
  font-size: 12px;
}

/* 美化思考过程的显示 */
.thinking-process {
  background-color: #f8f9fa;
  border-left: 3px solid #4caf50;
  padding: 10px;
  margin-bottom: 10px;
  border-radius: 4px;
  white-space: pre-wrap;
}

.thinking-process p {
  margin: 5px 0;
}

.thinking-process strong {
  color: #4caf50;
}

.question {
  background-color: #faf5f5;
  margin-left: auto; /* 问题靠右对齐 */
  margin-right: 0;
  max-width: 80%; /* 限制宽度 */
  justify-content: flex-end; /* 内容靠右 */
  border-top-left-radius: 15px;
  border-top-right-radius: 5px;
  border-bottom-left-radius: 15px;
  border-bottom-right-radius: 15px;
  background: #e6f7ff; /* 修改为浅蓝色背景 */
  color: #333; /* 深色文字，提高可读性 */
  font-weight: 500; /* 加粗文字 */
  text-shadow: none; /* 移除文字阴影，提高可读性 */
}

.question .qa-icon {
  order: 2; /* 图标放在右侧 */
  margin-right: 0;
  margin-left: 10px;
  color: #ee66a1; /* 图标颜色 */
}

.question .qa-text {
  text-align: right; /* 文本右对齐 */
  color: #151414; /* 深色文字 */
  font-weight: 600; /* 加粗文字 */
  text-shadow: none; /* 移除文字阴影 */
}

.qa-icon {
  margin-right: 10px;
  margin-top: 3px;
  color: #409EFF;
}

.qa-text {
  flex: 1;
  word-break: break-word;
  line-height: 1.5;
}

/* 深度思考模式样式 */
.qa-text :deep(details) {
  margin: 10px 0;
  border-radius: 8px;
}

.qa-text :deep(details summary) {
  cursor: pointer;
  font-weight: bold;
  color: #409EFF;
  padding: 5px;
  border-radius: 4px;
  background-color: rgba(255, 255, 255, 0.2);
}

.qa-text :deep(details p) {
  margin: 10px 0;
  padding: 10px;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  white-space: pre-wrap;
}

/*字幕区域*/
.subtitle-section {
  width: 40%; /* 略微减小宽度，为间隔留出空间 */
  height: 100%;
  padding: 15px;
  overflow: hidden;
  background: transparent;
  transition: all 0.3s ease;
}

/* 当侧边栏可见时，调整右侧栏的宽度 */
.video-player-container.with-sidebar .subtitle-section {
  width: 32%; /* 侧边栏打开时减小宽度 */
}

.subtitle-display-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  border: 3px solid #ff9a9e; /* 添加粉色边框 */
}

/* 移除字幕区域卡片悬停效果 */

.subtitle-mode-switch {
  padding: 10px;
  background: #f5f7fa;
  color: #333;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.subtitle-controls {
  width: 100%;
}

.subtitle-buttons-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.subtitle-left-buttons {
  display: flex;
  align-items: center;
}

.subtitle-right-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.subtitle-mode-button.purple-button {
  background-color: #818cf8;
  border-color: #818cf8;
  color: white;
}

.subtitle-mode-button.purple-button:hover {
  background-color: #818cf8;
  border-color: #818cf8;
}

.subtitle-buttons-row .el-button {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 8px 12px;
  font-size: 12px;
}

.subtitle-display {
  flex: 1;
  padding: 15px;
  overflow-y: auto;
  background-color: #fff;
}

.subtitle-item {
  margin-bottom: 15px;
  padding: 12px 15px;
  border-radius: 8px;
  background: #f9f9f9;
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

/* 移除字幕项悬停效果 */

.subtitle-item.current, 
.merged-item.current {
  background-color: rgba(60, 174, 163, 0.2);
  border-left: 3px solid #3CAEA3;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
  position: relative;
}

/* 添加左侧标记，增强视觉效果 */
.subtitle-item.current::before, 
.merged-item.current::before {
  content: "";
  position: absolute;
  left: -4px; /* 与边框宽度相同 */
  top: 0;
  height: 100%;
  width: 4px;
  background: linear-gradient(to bottom, #ee07da, #e30997); /* 渐变色边框 */
  border-radius: 2px;
}

/* 可以考虑添加右侧指示器 */
.subtitle-item.current::after,
.merged-item.current::after {
  content: "▶";
  position: absolute;
  right: 10px;
  top: 60%;
  transform: translateY(-50%);
  color: red;
  font-size: 20px;
}

.subtitle-time {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.subtitle-content {
  color: #333333;
  margin: 0;
  line-height: 1.6;
  font-size: 15px;
}

/*加载和错误覆盖层*/
.loading-overlay, .error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  z-index: 10;
}

.loading-icon, .error-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.error-overlay .el-button {
  margin-top: 15px;
}

/*侧边栏*/
.sidebar {
  position: fixed;
  top: 0;
  left: -22%; /* 调整初始位置 */
  width: 21%;
  height: 100%;
  background: #ffffff;
  transition: all 0.3s ease;
  z-index: 1000;
  overflow-y: auto;
  color: #0c2430;
}

.sidebar-visible {
  background-color: #ffffff;
  color: #333333;
  left: 0;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  background: #f5f7fa;
}

.sidebar-header h3 {
  margin: 0;
  font-weight: 600;
}

.close-icon {
  cursor: pointer;
  font-size: 20px;
  transition: transform 0.3s ease;
}

.close-icon:hover {
  transform: rotate(90deg);
}

.sidebar-content {
  padding: 15px;
}

.sidebar-menu {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #000000; /* 修改文字颜色为黑色 */
  background-color: #ffffff; /* 修改为白色背景 */
}

.menu-item:hover {
  background-color: #f5f5f5; /* 悬停时使用浅灰色 */
  transform: translateY(-2px);
}

.menu-item .el-icon {
  color: #333; /* 修改图标颜色为深色 */
  margin-right: 10px;
}

.menu-item .arrow-icon {
  margin-left: auto;
  margin-right: 0;
  color: #000000;
  font-size: 14px;
}

.menu-section {
  margin-top: 1px;
}

/* 侧边栏菜单标题 */
.menu-section h4 {
  margin-bottom: 10px;
  font-weight: 600;
  font-size: 20px;
  color: #000000;
}

.video-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 280px; /* 限制高度，约显示4个视频项 */
  overflow-y: auto;
  padding-right: 5px;
}

/* 自定义滚动条样式 */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

.video-item { /* 已分析视频列表的卡片 */
  display: flex;
  align-items: center;
  padding: 10px;
  border-radius: 8px;
  background-color: #ffffff; /* 修改为白色背景 */  cursor: pointer;
  transition: all 0.3s ease;
  width: 100%;
  box-sizing: border-box;
  height: 65px; /* 固定高度，确保每个视频项大小一致 */
}

.video-item:hover {
  background-color: #f5f5f5; /* 悬停时使用浅灰色 */
  transform: translateY(-2px);
}

.video-item.current-playing {
  background-color: #e6e6e6; /* 当前播放视频使用浅灰色 */
  border-left: 4px solid #c0c0c0; /* 左侧添加醒目的边框 */
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15); /* 添加阴影效果增强视觉层次 */
  transform: translateY(-2px); /* 轻微上移效果 */
}

.video-item.current-playing .video-title {
  font-weight: 700; /* 加粗标题 */
  color: #000000 ; /* 黑色文字颜色 */
}

.video-thumbnail {
  min-width: 80px; /* 使用最小宽度确保缩略图不会被压缩 */
  height: 45px; /* 增加高度，使图片更加清晰 */
  background-color: #333;
  border-radius: 4px;
  margin-right: 10px;
  background-size: cover;
  background-position: center;
  flex-shrink: 0; /* 防止缩略图被压缩 */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); /* 添加阴影效果 */
}

.video-info {
  flex: 1;
  min-width: 0; /* 允许内容在必要时缩小 */
  overflow: hidden; /* 确保溢出内容被隐藏 */
}

.video-item .arrow-icon {
  margin-left: 10px;
  color: #000000;
  font-size: 14px;
}

.video-title {  /* 侧边栏已分析视频标题 */
  font-weight: 600;
  margin-bottom: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%; /* 确保标题不会超出父容器 */
  color: #000000; /* 修改为黑色字体 */
}

.video-duration {
  font-size: 12px;
  color: #333;
  background: rgba(255, 255, 255, 0.5); /* 修改背景为半透明白色 */
  padding: 2px 6px;
  border-radius: 10px;
  display: inline-block;
}

.empty-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: #ff9a9e; 
}

.empty-list .el-icon {
  color: #808080; /* 修改图标颜色为灰色 */
  font-size: 24px;
  margin-bottom: 10px;
}

/*侧边栏开关按钮*/
.sidebar-toggle {
  position: fixed;
  top: 50%;
  left: 20px;
  transform: translateY(-50%); /* 确保完全居中 */
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--primary-color); /* 使用实色而不是渐变色，确保可见 */
  color: white; /* 确保图标是白色 */
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  z-index: 999;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
}

.sidebar-toggle:hover {
  transform: translateY(-50%) scale(1.1); /* 保持垂直居中的同时添加缩放效果 */
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}

/* 添加动画效果 */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 模式标签样式 */
.mode-tag {
  margin-left: 8px;
  vertical-align: middle;
  font-size: 0.8em;
  transform: translateY(-2px);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    opacity: 0.7;
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 0.7;
  }
}

/* 优化问答模式提示信息样式 */
.qa-mode-info {
  margin-bottom: 15px;
}

.qa-mode-info .el-alert {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(255, 154, 158, 0.3);
  background: linear-gradient(135deg, #fff5f5, #fff);
}

.qa-mode-info .el-alert__title {
  font-size: 16px;
  font-weight: 600;
  color: #ff9a9e;
}

.qa-mode-info .el-alert__description {
  font-size: 14px;
  color: #606266;
  margin-top: 5px;
  line-height: 1.5;
}

.qa-mode-info .el-alert__icon {
  color: #ff9a9e;
}

/* 深度思考模式按钮样式 */
.thinking-mode-button {
  margin-bottom: 10px;
  display: flex;
  justify-content: flex-end;
}

/* 问答模式按钮样式 */
.qa-mode-buttons {
  display: flex;
  gap: 10px;
}

/* 共享按钮样式 */
.thinking-mode-button .el-button,
.qa-mode-buttons .el-button {
  transition: all 0.3s ease;
  border-radius: 20px;
  padding: 6px 15px;
}

.thinking-mode-button .el-button--primary,
.qa-mode-buttons .el-button--primary {
  border-color: #80b3e6;
}

.thinking-mode-button .el-button--default,
.qa-mode-buttons .el-button--default {
  border: 1px solid #dcdfe6;
  background: #f5f7fa;
  color: #606266;
}

.thinking-mode-button .el-button:hover,
.qa-mode-buttons .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>