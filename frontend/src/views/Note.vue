<template>
  <div class="note-page-container">
    <!-- 顶部工具栏 -->
    <div class="note-toolbar">
      <div class="left-actions">
        
        <!-- 集成的笔记管理面板 -->
        <el-popover
          placement="bottom-start"
          :width="600"
          trigger="click"
          popper-class="note-manager-popover"
        >
          <template #reference>
            <el-button type="primary" plain>
              <span>笔记管理</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
          </template>
          
          <div class="note-manager-container">
            <!-- 左侧标签面板 -->
            <div class="tags-panel">
              <div class="panel-header">
                <h4>标签</h4>
                <div class="tag-actions">
                  <el-button link size="small" @click="clearTagFilter" :disabled="selectedTags.length === 0">
                    清除筛选
                  </el-button>
                  <el-button link size="small" type="primary" @click="handleSyncTags">
                    同步标签
                  </el-button>
                </div>
              </div>
              
              <div class="tags-list">
                <el-tag
                  v-for="tag in allTags"
                  :key="tag.name"
                  :type="getTagType(tag.name)"
                  :effect="selectedTags.includes(tag.name) ? 'dark' : 'plain'"
                  class="clickable-tag"
                  @click="toggleTagSelection(tag.name)"
                >
                  {{ tag.name }}
                  <span class="tag-count">{{ tag.count }}</span>
                </el-tag>
              </div>
              
              <div v-if="selectedTags.length > 0" class="selected-tags">
                <div class="selected-tags-header">已选标签：</div>
                <div class="selected-tags-list">
                  <el-tag
                    v-for="tag in selectedTags"
                    :key="tag"
                    closable
                    @close="removeSelectedTag(tag)"
                  >
                    {{ tag }}
                  </el-tag>
                  <el-button link size="small" @click="clearTagFilter">清除筛选</el-button>
                </div>
              </div>
            </div>
            
            <!-- 右侧笔记列表 -->
            <div class="notes-panel">
              <div class="panel-header">
                <h4>笔记列表</h4>
                <div class="list-actions">
                  <!-- 批量操作工具栏 -->
                  <div class="batch-operations-toolbar">
                    <el-button 
                      link
                      size="small"
                      @click="toggleBatchOperations"
                    >
                      {{ showBatchOperations ? '退出批量操作' : '批量操作' }}
                    </el-button>
                    
                    <template v-if="showBatchOperations">
                      <el-button 
                        link
                        size="small"
                        @click="toggleSelectAll"
                      >
                        {{ isAllSelected ? '取消全选' : '全选' }}
                      </el-button>
                      
                      <el-button 
                        link
                        type="primary"
                        size="small"
                        @click="handleBatchExport"
                        :disabled="selectedNoteIds.length === 0"
                      >
                        导出 ({{ selectedNoteIds.length }})
                      </el-button>
                      
                      <el-button 
                        link
                        type="danger"
                        size="small"
                        @click="handleBatchDelete"
                        :disabled="selectedNoteIds.length === 0"
                      >
                        删除 ({{ selectedNoteIds.length }})
                      </el-button>
                    </template>
                  </div>
                </div>
              </div>
              
              <div class="notes-list card-layout">
                <div 
                  v-for="note in filteredNotes" 
                  :key="note.id"
                  class="note-item"
                  :class="{ 'selected': currentNote && currentNote.id === note.id }"
                  @click="selectNote(note)"
                >
                  <!-- 批量选择复选框 -->
                  <el-checkbox 
                    v-if="showBatchOperations"
                    v-model="note.selected"
                    @change="(val) => toggleNoteSelection(note.id, val)"
                    @click.stop
                  />
                  
                  <div class="note-item-content">
                    <div class="note-title">{{ note.title }}</div>
                    <div class="note-preview">{{ getPreviewText(note) }}</div>
                    <div class="note-meta">
                      <span class="note-date">{{ formatDateTime(note.created_at) }}</span>
                      <div class="note-tags">
                        <el-tag 
                          v-for="tag in note.tags.slice(0, 3)" 
                          :key="tag" 
                          size="small"
                          :type="getTagType(tag)"
                          effect="plain"
                        >
                          {{ tag }}
                        </el-tag>
                        <span v-if="note.tags.length > 3">+{{ note.tags.length - 3 }}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div class="note-actions">
                    <el-dropdown trigger="click" @command="(cmd) => handleNoteItemAction(cmd, note.id)" @click.stop>
                      <el-button type="text">
                        <el-icon><MoreFilled /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item command="export">导出</el-dropdown-item>
                          <el-dropdown-item command="delete" style="color: #F56C6C;">删除</el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </div>
                
                <div v-if="filteredNotes.length === 0" class="empty-notes">
                  <el-icon><Document /></el-icon>
                  <p>没有找到符合条件的笔记</p>
                </div>
              </div>
            </div>
          </div>
        </el-popover>
        
        <!-- 搜索笔记 -->
        <div class="search-container">
          <el-input
            v-model="searchQuery"
            placeholder="搜索标题、内容或关键词"
            prefix-icon="Search"
            clearable
            @input="debounceSearch"
          >
            <template #append>
              <el-button @click="fetchNotes">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
          <div v-if="searchQuery && notes.length > 0" class="search-info">
            搜索到 {{ notes.length }} 条相关笔记
          </div>
          <div v-else-if="searchQuery && notes.length === 0" class="search-info">
            未找到相关笔记
          </div>
          
          <!-- 搜索结果下拉列表 -->
          <div v-if="searchQuery && notes.length > 0" class="search-results">
            <div 
              v-for="note in notes.slice(0, 5)" 
              :key="note.id"
              class="search-result-item"
              @click="selectNote(note)"
            >
              <div class="search-result-title">{{ note.title }}</div>
              <div class="search-result-preview">{{ getPreviewText(note) }}</div>
              <div class="search-result-tags">
                <el-tag 
                  v-for="tag in note.tags.slice(0, 2)" 
                  :key="tag" 
                  size="small"
                  :type="getTagType(tag)"
                  effect="plain"
                >
                  {{ tag }}
                </el-tag>
              </div>
            </div>
            <div v-if="notes.length > 5" class="search-result-more" @click="searchQuery = ''">
              查看全部 {{ notes.length }} 条结果
            </div>
          </div>
        </div>
      </div>
      <div class="right-actions">
        <el-button type="primary" round @click="createNewNote">
          <el-icon><Plus /></el-icon>新建笔记
        </el-button>
      </div>
    </div>
  
    <!-- 主要内容区域 -->
    <div class="note-content-container">
      <!-- 左侧区域：视频播放和字幕 -->
      <div class="left-section">
        <!-- 视频播放区域 -->
        <div class="video-section">
          <div class="video-header">
            <h3>视频播放</h3>
          </div>
          <div class="video-player-wrapper" v-if="showVideo">
            <video
              ref="videoPlayer"
              class="video-element"
              controls
              controlslist="nodownload"
              @timeupdate="onVideoTimeUpdate"
              @seeked="onVideoSeeked"
              v-if="videoUrl"
            >
              <source :src="videoUrl" type="video/mp4" />
              您的浏览器不支持 HTML5 视频播放
            </video>
            <div class="no-video-placeholder" v-else>
              <el-icon><VideoCamera /></el-icon>
              <p>未选择视频</p>
            </div>
          </div>
        </div>

        <!-- 字幕区域 -->
        <div class="subtitle-section">
          <div class="subtitle-header">
            <h3>视频字幕</h3>
            <div class="subtitle-actions">
              <el-tooltip content="点击字幕添加到笔记">
                <el-icon><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
          </div>
          <div class="subtitle-list-wrapper">
            <div class="subtitle-list" v-if="subtitles.length > 0">
              <div
                v-for="(subtitle, index) in subtitles"
                :key="index"
                class="subtitle-item"
                :class="{ 'active': isCurrentSubtitle(subtitle) }"
                :data-id="subtitle.id || index"
                :id="`subtitle-${index}`"
                @click="handleSubtitleClick(subtitle)"
              >
                <div class="subtitle-time">{{ formatTimeMMSS(subtitle.start_time || subtitle.start) }}</div>
                <div class="subtitle-text">{{ subtitle.content || subtitle.text }}</div>
              </div>
            </div>
            <div class="no-subtitles" v-else>
              <el-icon><Document /></el-icon>
              <p>无可用字幕</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧区域：笔记编辑 -->
      <div class="right-section">
        <div class="note-editor-container">
          <!-- 笔记编辑器 -->
          <div class="note-editor-section">
            <div class="note-editor-header">
              <div class="editor-title">
                <el-input
                  v-model="noteTitle"
                  placeholder="笔记标题"
                  :disabled="!currentNote && !isCreatingNote"
                />
              </div>
            </div>

            <!-- 标签编辑和操作按钮 -->
            <div class="note-tags-and-actions">
              <div class="note-tags-editor">
                <el-tag
                  v-for="tag in noteTags"
                  :key="tag"
                  closable
                  :type="getTagType(tag)"
                  @close="removeTag(tag)"
                  class="note-tag"
                >
                  {{ tag }}
                </el-tag>
                <el-input
                  v-if="inputTagVisible"
                  ref="tagInput"
                  v-model="inputTagValue"
                  class="tag-input"
                  size="small"
                  @keyup.enter="confirmTag"
                  @blur="confirmTag"
                />
                <el-button
                  v-else
                  class="button-new-tag"
                  size="small"
                  @click="showTagInput"
                  :disabled="!currentNote && !isCreatingNote"
                >
                  + 添加标签
                </el-button>
              </div>
              
              <!-- 操作按钮 -->
              <div class="editor-actions">
                <el-button-group>
                  <el-button
                    type="primary"
                    @click="saveNote"
                    :disabled="!currentNote && !isCreatingNote"
                  >
                    保存
                  </el-button>
                  <el-button
                    @click="exportCurrentNote"
                    :disabled="!currentNote && !isCreatingNote"
                  >
                    导出
                  </el-button>
                  <el-button
                    type="danger"
                    @click="deleteCurrentNote"
                    :disabled="!currentNote"
                  >
                    删除
                  </el-button>
                </el-button-group>
                <el-button
                  v-if="isCreatingNote"
                  @click="cancelCreate"
                >
                  取消
                </el-button>
              </div>
            </div>

            <!-- 编辑器区域 -->
            <div class="editor-wrapper" :class="{ 'disabled': !currentNote && !isCreatingNote }">
              <!-- 智能笔记编辑器 -->
              <div class="smart-note-editor">
                <div class="editor-toolbar">
                  <el-dropdown trigger="click" placement="bottom-start">
                    <el-button type="primary" size="small" class="toolbar-dropdown-button">
                      编辑选项 <el-icon><arrow-down /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="insertHeading">
                          <el-icon><Document /></el-icon> 标题
                        </el-dropdown-item>
                        <el-dropdown-item @click="formatText('bold')">
                          <el-icon><Edit /></el-icon> 粗体
                        </el-dropdown-item>
                        <el-dropdown-item @click="formatText('italic')">
                          <el-icon><Promotion /></el-icon> 斜体
                        </el-dropdown-item>
                        <el-dropdown-item divided @click="insertList('bullet')">
                          <el-icon><List /></el-icon> 无序列表
                        </el-dropdown-item>
                        <el-dropdown-item @click="insertList('number')">
                          <el-icon><SortUp /></el-icon> 有序列表
                        </el-dropdown-item>
                        <el-dropdown-item divided @click="insertCodeBlock">
                          <el-icon><Operation /></el-icon> 代码块
                        </el-dropdown-item>
                        <el-dropdown-item @click="insertQuote">
                          <el-icon><ChatDotSquare /></el-icon> 引用
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                  <!-- 保留预览切换按钮 -->
                  <div class="preview-toggle-toolbar">
                    <el-switch
                      v-model="showPreview"
                      active-text="预览"
                      inactive-text="编辑"
                      @change="handlePreviewToggle"
                    />
                  </div>
                </div>
                
                <div class="editor-content-area">
                  <textarea 
                    ref="noteEditor" 
                    v-model="noteContent" 
                    class="note-textarea"
                    placeholder="在此输入笔记内容..."
                    @input="handleContentChange"
                    @click="handleEditorClick"
                    v-show="!showPreview"
                  ></textarea>
                  
                  <!-- Markdown预览区域 -->
                  <div 
                    v-show="showPreview" 
                    class="markdown-preview" 
                    v-html="renderedContent"
                  ></div>
                </div>
                
                <!-- 编辑器禁用遮罩 -->
                <div class="editor-mask" v-if="!currentNote && !isCreatingNote">
                  <div class="mask-content">
                    <el-icon><Document /></el-icon>
                    <h3>请选择笔记管理中的笔记或创建笔记以开始编辑</h3>
                  </div>
                </div>
              </div>
            </div>

            <!-- 相似笔记推荐区域 -->
            <div class="similar-notes-section" v-if="similarNotes.length > 0">
              <div class="similar-notes-header">
                <h4>相似笔记推荐</h4>
                <el-tooltip content="基于您当前编写的内容，系统为您推荐了以下相似的笔记" placement="top">
                  <el-icon><QuestionFilled /></el-icon>
                </el-tooltip>
              </div>
              <div class="similar-notes-list">
                <div 
                  v-for="note in similarNotes" 
                  :key="note.id" 
                  class="similar-note-item"
                  @click="viewSimilarNote(note)"
                >
                  <div class="similar-note-title">{{ note.title }}</div>
                  <div class="similar-note-preview">{{ getContentPreview(note.content) }}</div>
                  <div class="similar-note-meta">
                    <span class="similar-note-date">{{ formatDateTime(note.created_at) }}</span>
                    <div class="similar-note-tags">
                      <el-tag 
                        v-for="tag in note.tags.slice(0, 2)" 
                        :key="tag" 
                        size="small"
                        effect="plain"
                      >
                        {{ tag }}
                      </el-tag>
                      <span v-if="note.tags.length > 2">+{{ note.tags.length - 2 }}</span>
                    </div>
                  </div>

                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 自动保存定时器
let autoSaveInterval = null;
// 导入Element Plus图标
import {
  Plus,Search,ArrowLeft,ArrowRight,ArrowDown,VideoCamera,InfoFilled,Document,Delete,
  Edit,Promotion,List,SortUp,Operation,ChatDotSquare,QuestionFilled,Filter,Check,Download,
  MoreFilled
} from '@element-plus/icons-vue';
import { ref, onMounted, computed, watch, nextTick, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { debounce } from 'lodash-es';
import { 
  getNotes, getNote, createNote, updateNote, deleteNote, 
  addTimestamp, deleteTimestamp, getTags, getSimilarNotes, 
  batchDeleteNotes, batchExportNotes, exportNote, syncTags
} from '@/api/note';
import { getVideo, getSubtitle } from '@/api/video';
import * as marked from 'marked';
import axios from 'axios';
import DOMPurify from 'dompurify';
import request from '@/utils/request';

const isFetchingSimilarNotes = ref(false);

// 路由相关
const route = useRoute();
const router = useRouter();
const videoId = computed(() => route.query.videoId ? parseInt(route.query.videoId) : null);

// 笔记管理弹窗引用
const noteManagerPopoverRef = ref(null);

// 笔记数据
const notes = ref([]);
const currentNote = ref(null);
const isCreatingNote = ref(false);
const noteTitle = ref('');
const noteContent = ref('');
const noteTags = ref([]);
const timestamps = ref([]);
const similarNotes = ref([]);

// 编辑器相关
const quillEditor = ref(null);
const markdownEditor = ref(null);
const quillInstance = ref(null);
const vditorInstance = ref(null);
const noteEditor = ref(null);

// 视频相关
const videoPlayer = ref(null);
const currentVideo = ref(null);
const videoUrl = ref('');
const subtitleUrl = ref('');
const subtitles = ref([]);
const currentSubtitle = ref(null);
const needScrollToSubtitle = ref(false);
const currentTime = ref(0);

// UI状态
const showVideo = ref(true);
const showNoteList = ref(true);
const searchQuery = ref('');
const selectedTags = ref([]);
const allTags = ref([]);
const inputTagVisible = ref(false);
const inputTagValue = ref('');
const tagInput = ref(null);

// Markdown 编辑器帮助
const showMarkdownHelp = ref(false);
const dontShowMarkdownHelp = ref(false);

// Markdown 预览相关
const showPreview = ref(false);

// 渲染Markdown
const renderedContent = computed(() => {
  try {
    // 配置marked选项，启用breaks选项以支持单行换行
    marked.setOptions({
      breaks: true,  // 将单个换行符转换为<br>
      gfm: true      // 启用GitHub风格的Markdown
    });
    
    // 使用marked解析Markdown
    let html = marked.parse(noteContent.value || '');
    
    // 处理新的时间戳标记格式 [MM:SS]{{timestamp:秒数}}
    html = html.replace(/\[([0-9:]+)\]\{\{timestamp:(\d+\.?\d*)\}\}/g, (match, text, time) => {
      const timeSeconds = parseFloat(time);
      return `<a href="javascript:void(0)" class="timestamp-link" data-time="${timeSeconds}" onclick="window.handleTimestampClick(${timeSeconds})">${text}</a>`;
    });
    
    // 使用DOMPurify清理HTML以防止XSS攻击，但保留onclick和data-time属性
    return DOMPurify.sanitize(html, {
      ADD_ATTR: ['onclick', 'data-time']
    });
  } catch (error) {
    console.error('Markdown渲染错误:', error);
    return `<p>渲染错误: ${error.message}</p>`;
  }
});

// 批量操作相关状态
const showBatchOperations = ref(false);
const selectedNoteIds = ref([]);

// 计算属性：根据标签和搜索筛选后的笔记列表
const filteredNotes = computed(() => {
  if (!notes.value) return [];
  
  let result = [...notes.value];
  
  // 根据标签筛选
  if (selectedTags.value.length > 0) {
    result = result.filter(note => {
      if (!note.tags) return false;
      return selectedTags.value.every(tag => note.tags.includes(tag));
    });
  }
  
  // 根据搜索词筛选
  if (searchQuery.value) {
    const searchLower = searchQuery.value.toLowerCase();
    result = result.filter(note => 
      (note.title && typeof note.title === 'string' && note.title.toLowerCase().includes(searchLower)) || 
      (note.content && typeof note.content === 'string' && note.content.toLowerCase().includes(searchLower)) ||
      (note.keywords && typeof note.keywords === 'string' && note.keywords.toLowerCase().includes(searchLower)) ||
      (note.tags && typeof note.tags === 'string' && note.tags.toLowerCase().includes(searchLower))
    );
  }
  
  return result;
});

// 获取标签对应的笔记数量
const getTagCount = (tag) => {
  return notes.value.filter(note => note.tags.includes(tag)).length;
};

// 切换标签选择状态
const toggleTagSelection = (tag) => {
  if (selectedTags.value.includes(tag)) {
    removeSelectedTag(tag);
  } else {
    selectedTags.value.push(tag);
    fetchNotes(); // 确保调用 fetchNotes 更新筛选结果
  }
};

// 获取笔记列表
const fetchNotes = async () => {
  try {
    const params = {};
    if (videoId.value) {
      params.video_id = videoId.value;
    }
    if (searchQuery.value) {
      params.search = searchQuery.value;
    }
    
    // 添加标签筛选参数
    if (selectedTags.value.length > 0) {
      params.tag = selectedTags.value[0]; // 后端API只支持单个标签筛选
    }
    
    console.log('获取笔记参数:', params);
    const response = await getNotes(params);
    if (response.data && response.data.status === 'success') {
      notes.value = response.data.data;
      console.log('获取到笔记列表:', notes.value);
    }
  } catch (error) {
    console.error('获取笔记列表失败:', error);
    ElMessage.error('获取笔记列表失败');
  }
};

// 防抖搜索
const debounceSearch = debounce(() => {
  fetchNotes();
}, 300);

// 计算属性：是否全选
const isAllSelected = computed(() => {
  return selectedNoteIds.value.length === filteredNotes.value.length;
});

// 初始化
onMounted(async () => {
  console.log('笔记页面加载，视频ID:', videoId.value);
  await fetchNotes();
  await fetchTags(); // 确保标签列表被加载
  
  if (videoId.value) {
    console.log('准备加载视频:', videoId.value);
    await loadVideo(videoId.value);
  }
  
  // 初始化笔记编辑器
  initNoteEditor();
  
  // 尝试从本地存储恢复笔记
  const restored = restoreFromLocalStorage();
  
  // 如果没有恢复成功，则创建新笔记
  if (!restored) {
    // 自动创建新笔记，无需点击按钮
    initNewNote();
    // 清除本地存储的草稿
    localStorage.removeItem('draft_note');
  }

  // 设置自动保存定时器（每分钟保存一次）
  const autoSaveInterval = setInterval(() => {
    autoSaveToLocalStorage();
  }, 60000);

  window.handleTimestampClick = (timeSeconds) => {
    if (typeof timeSeconds === 'number') {
      seekToTime(timeSeconds);
    }
  };
});

// 清理资源
onUnmounted(() => {
  if (vditorInstance.value) {
    vditorInstance.value.destroy();
  }
  
  // 移除视频事件监听器
  if (videoPlayer.value) {
    videoPlayer.value.removeEventListener('timeupdate', onVideoTimeUpdate);
  }
  
  // 清理自动保存定时器
  if (autoSaveInterval) {
    clearInterval(autoSaveInterval);
  }
  
  window.handleTimestampClick = undefined;
});
// 监听笔记变化，更新编辑器内容
watch(currentNote, (newNote) => {
  if (newNote) {
    noteTitle.value = newNote.title || '';
    noteTags.value = [...(newNote.tags || [])];
    timestamps.value = [...(newNote.timestamps || [])];
    
    noteContent.value = newNote.content || '';
    
    // 加载相似笔记
    fetchSimilarNotes();
  } else if (!isCreatingNote.value) {
    resetEditor();
  }
});

// 监听视频ID变化
watch(videoId, async (newVideoId) => {
  if (newVideoId) {
    await loadVideo(newVideoId);
  } else {
    currentVideo.value = null;
    videoUrl.value = '';
    subtitleUrl.value = '';
    subtitles.value = [];
  }
});

// 视频时间更新处理
const onVideoTimeUpdate = () => {
  if (!videoPlayer.value) return;
  
  currentTime.value = videoPlayer.value.currentTime;
  
  // 更新当前字幕
  if (subtitles.value && subtitles.value.length > 0) {
    // 查找当前时间对应的字幕
    const currentSub = subtitles.value.find(sub => {
      const start = sub.start_time || sub.start;
      const end = sub.end_time || sub.end || (start + 5); // 如果没有结束时间，默认为开始时间+5秒
      return currentTime.value >= start && currentTime.value <= end;
    });
    
    // 如果找到对应字幕，并且与当前字幕不同
    if (currentSub && (!currentSubtitle.value || currentSub !== currentSubtitle.value)) {
      currentSubtitle.value = currentSub;
      
      // 如果需要滚动到字幕
      if (needScrollToSubtitle.value) {
        // 获取字幕索引
        const index = subtitles.value.indexOf(currentSub);
        
        // 滚动到字幕位置
        setTimeout(() => {
          const subtitleElement = document.getElementById(`subtitle-${index}`);
          if (subtitleElement) {
            const subtitleContainer = document.querySelector('.subtitle-list-wrapper');
            if (subtitleContainer) {
              // 计算滚动位置，使字幕在容器中居中显示
              subtitleContainer.scrollTop = subtitleElement.offsetTop - 100;
              
              // 添加闪烁效果
              subtitleElement.classList.add('highlight-flash');
              setTimeout(() => {
                subtitleElement.classList.remove('highlight-flash');
              }, 2000);
            }
          }
          
          // 重置标志
          needScrollToSubtitle.value = false;
        }, 100);
      }
    }
  }
};

// 视频拖动进度条完成处理
const onVideoSeeked = () => {
  // 设置需要滚动到字幕的标志
  needScrollToSubtitle.value = true;
};

// 初始化笔记编辑器
const initNoteEditor = () => {
  nextTick(() => {
    if (noteEditor.value) {
      // 设置编辑器初始状态
      updateEditorEditableState();
    }
  });
};

// 更新编辑器可编辑状态
const updateEditorEditableState = () => {
  if (noteEditor.value) {
    if (currentNote.value || isCreatingNote.value) {
      noteEditor.value.disabled = false;
    } else {
      noteEditor.value.disabled = true;
    }
  }
};

// 监听笔记选择和创建状态变化，更新编辑器可编辑状态
watch([currentNote, isCreatingNote], () => {
  updateEditorEditableState();
});

// 监听预览状态变化
watch(showPreview, (newValue) => {
  console.log('预览模式状态变化:', newValue);
  handlePreviewToggle(newValue);
});

// 监听标题、内容和标签的变化，自动保存
watch([noteTitle, noteContent, noteTags, timestamps], () => {
  if (isCreatingNote.value || currentNote.value) {
    autoSaveToLocalStorage();
  }
}, { deep: true });

// 处理内容变化
const handleContentChange = debounce(() => {
  // 当内容变化时，触发自动保存
  autoSaveToLocalStorage();
  // 检查是否需要获取相似笔记
  if (noteContent.value.length > 5 && !isFetchingSimilarNotes.value) {
    fetchSimilarNotes();
  }
}, 500);

const fetchSimilarNotes = async () => {
  // 在函数开始处添加日志
  console.log('开始获取相似笔记，内容长度:', noteContent.value.length);
  
  if (isFetchingSimilarNotes.value) return;
  
  isFetchingSimilarNotes.value = true;
  
  try {
    const response = await getSimilarNotes({
      content: noteContent.value,
      limit: 5
    });
    
    // 在获取响应后添加日志
    console.log('相似笔记API响应:', response);
    
    if (response && response.data && response.data.status === 'success') {
      similarNotes.value = response.data.data.filter(note => 
        !currentNote.value || note.id !== currentNote.value.id
      );
      
      // 在处理完数据后添加日志
      console.log('过滤后的相似笔记:', similarNotes.value);
    }
  } catch (error) {
    console.error('获取相似笔记失败:', error);
  } finally {
    isFetchingSimilarNotes.value = false;
  }
};

// 查看相似笔记
const viewSimilarNote = (note) => {
  // 如果当前正在编辑，提示保存
  if (isCreatingNote.value || (currentNote.value && noteContent.value !== currentNote.value.content)) {
    ElMessageBox.confirm('当前笔记未保存，是否保存后查看相似笔记？', '保存确认', {
      confirmButtonText: '保存',
      cancelButtonText: '不保存',
      distinguishCancelAndClose: true,
      closeOnClickModal: false
    }).then(() => {
      // 保存当前笔记
      saveNote().then(() => {
        // 选择相似笔记
        selectNote(note);
      });
    }).catch((action) => {
      if (action === 'cancel') {
        // 不保存，直接查看相似笔记
        selectNote(note);
      }
    });
  } else {
    // 直接查看相似笔记
    selectNote(note);
  }
};

// 获取内容预览
const getContentPreview = (content) => {
  if (!content) return '';
  return content.length > 100 ? content.substring(0, 100) + '...' : content;
};

// 格式化时间（MM:SS）
const formatTimeMMSS = (time) => {
  // 确保time是数字
  const seconds = typeof time === 'number' ? time : parseFloat(time) || 0;
  
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

// 格式化日期时间
const formatDateTime = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 自动保存笔记到本地存储
const autoSaveToLocalStorage = () => {
  if (!noteEditor.value || (!currentNote.value && !isCreatingNote.value)) return;
  
  const noteData = {
    title: noteTitle.value,
    content: noteContent.value,
    tags: noteTags.value,
    timestamps: timestamps.value,
    video_id: videoId.value || null,
    isCreating: isCreatingNote.value,
    currentNoteId: currentNote.value ? currentNote.value.id : null,
    lastSaved: new Date().toISOString()
  };
  
  // 保存到本地存储
  localStorage.setItem('draft_note', JSON.stringify(noteData));
  console.log('笔记已自动保存到本地存储', new Date().toLocaleTimeString());
};

// 从本地存储恢复笔记
const restoreFromLocalStorage = () => {
  const savedNote = localStorage.getItem('draft_note');
  if (!savedNote) return false;
  
  try {
    const noteData = JSON.parse(savedNote);
    
    // 检查保存时间，如果超过24小时则不恢复
    const lastSaved = new Date(noteData.lastSaved);
    const now = new Date();
    const hoursDiff = (now - lastSaved) / (1000 * 60 * 60);
    
    if (hoursDiff > 24) {
      localStorage.removeItem('draft_note');
      return false;
    }
    
    // 恢复笔记数据
    noteTitle.value = noteData.title || '';
    noteContent.value = noteData.content || '';
    noteTags.value = noteData.tags || [];
    timestamps.value = noteData.timestamps || [];
    
    // 恢复笔记状态
    if (noteData.isCreating) {
      isCreatingNote.value = true;
      currentNote.value = null;
    } else if (noteData.currentNoteId) {
      // 查找对应的笔记
      const foundNote = notes.value.find(note => note.id === noteData.currentNoteId);
      if (foundNote) {
        currentNote.value = foundNote;
        isCreatingNote.value = false;
      } else {
        isCreatingNote.value = true;
        currentNote.value = null;
      }
    }
    
    // 更新编辑器状态
    updateEditorEditableState();
    
    // 如果笔记内容不为空，获取相似笔记
    if (noteContent.value && noteContent.value.length > 5) {
      fetchSimilarNotes();
    }
    
    ElMessage.info('已恢复未保存的笔记');
    return true;
  } catch (error) {
    console.error('恢复笔记失败:', error);
    localStorage.removeItem('draft_note');
    return false;
  }
};

// 编辑器工具栏功能
const insertHeading = () => {
  const textarea = noteEditor.value;
  if (!textarea) return;
  
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const text = noteContent.value;
  
  // 在选中文本前后添加 # 和换行符
  const selectedText = text.substring(start, end);
  const replacement = `# ${selectedText}`;
  
  noteContent.value = text.substring(0, start) + replacement + text.substring(end);
  
  // 重新设置光标位置
  nextTick(() => {
    textarea.focus();
    textarea.setSelectionRange(start + 2, start + 2 + selectedText.length);
  });
};

const formatText = (format) => {
  const textarea = noteEditor.value;
  if (!textarea) return;
  
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const text = noteContent.value;
  
  let selectedText = text.substring(start, end);
  let replacement = '';
  
  if (format === 'bold') {
    replacement = `**${selectedText}**`;
  } else if (format === 'italic') {
    replacement = `*${selectedText}*`;
  }
  
  noteContent.value = text.substring(0, start) + replacement + text.substring(end);
  
  // 重新设置光标位置
  nextTick(() => {
    textarea.focus();
    textarea.setSelectionRange(start + 2, start + 2 + selectedText.length);
  });
};

const insertList = (type) => {
  const textarea = noteEditor.value;
  if (!textarea) return;
  
  const start = textarea.selectionStart;
  const text = noteContent.value;
  
  let prefix = type === 'bullet' ? '- ' : '1. ';
  let insertion = `\n${prefix}`;
  
  noteContent.value = text.substring(0, start) + insertion + text.substring(start);
  
  // 重新设置光标位置
  nextTick(() => {
    textarea.focus();
    textarea.setSelectionRange(start + insertion.length, start + insertion.length);
  });
};

const insertCodeBlock = () => {
  const textarea = noteEditor.value;
  if (!textarea) return;
  
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const text = noteContent.value;
  
  const selectedText = text.substring(start, end);
  const replacement = `\n\`\`\`\n${selectedText}\n\`\`\`\n`;
  
  noteContent.value = text.substring(0, start) + replacement + text.substring(end);
  
  // 更新光标位置到插入文本后
  nextTick(() => {
    textarea.focus();
    const newPosition = start + 5;
    textarea.setSelectionRange(newPosition, newPosition);
  });
};

const insertQuote = () => {
  const textarea = noteEditor.value;
  if (!textarea) return;
  
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const text = noteContent.value;
  
  const selectedText = text.substring(start, end);
  const replacement = `> ${selectedText}`;
  
  noteContent.value = text.substring(0, start) + replacement + text.substring(end);
  
  // 重新设置光标位置
  nextTick(() => {
    textarea.focus();
    const newPosition = start + 2;
    textarea.setSelectionRange(newPosition, newPosition);
  });
};

// 选择笔记
const selectNote = async (note) => {
  if (currentNote.value && currentNote.value.id === note.id) return;
  
  // 如果当前正在创建新笔记，提示保存
  if (isCreatingNote.value) {
    try {
      await ElMessageBox.confirm('您当前正在编辑的笔记尚未保存，是否保存？', '温馨提示', {
        confirmButtonText: '保存',
        cancelButtonText: '不保存',
        distinguishCancelAndClose: true,
        closeOnClickModal: false
      });
      
      await saveNote();
    } catch (action) {
      if (action === 'cancel') {
        // 不保存，继续选择新笔记
        isCreatingNote.value = false;
      } else {
        // 取消操作
        return;
      }
    }
  }
  
  currentNote.value = note;
  isCreatingNote.value = false;
  
  // 如果笔记关联了视频，且与当前视频不同，则加载该视频
  if (note.video_id && (!videoId.value || note.video_id !== videoId.value)) {
    router.replace({ query: { ...route.query, videoId: note.video_id } });
  }
  
  // 设置笔记类型和内容
  noteContent.value = note.content || '';
  
  // 更新编辑器状态
  updateEditorEditableState();
  
  // 清空相似笔记推荐
  similarNotes.value = [];

  // 设置为预览模式
  showPreview.value = true;
  
  // 关闭笔记管理弹窗（仅在非批量操作模式下）
  if (!showBatchOperations.value) {
    // 使用Element Plus的方式关闭弹窗
    noteManagerPopoverRef.value?.hide?.();
  }
};

// 保存笔记
const saveNote = async () => {
  if (!noteTitle.value || !noteContent.value) {
    ElMessage.warning('标题和内容不能为空');
    return;
  }
  
  try {
    const noteData = {
      title: noteTitle.value,
      content: noteContent.value,
      tags: noteTags.value,
      timestamps: timestamps.value,
      video_id: videoId.value || null
    };
    
    let response;
    
    if (isCreatingNote.value) {
      // 创建新笔记
      response = await createNote(noteData);
      
      if (response.data && response.data.status === 'success') {
        ElMessage.success('笔记创建成功');
        isCreatingNote.value = false;
        await fetchNotes();
        
        // 保存成功后，重置编辑器准备创建新笔记
        initNewNote();
        // 清除本地存储的草稿
        localStorage.removeItem('draft_note');
      }
    } else if (currentNote.value) {
      // 更新现有笔记
      response = await updateNote(currentNote.value.id, noteData);
      
      if (response.data && response.data.status === 'success') {
        ElMessage.success('笔记更新成功');
        await fetchNotes();
        
        // 保存成功后，重置编辑器准备创建新笔记
        initNewNote();
      }
    }
    
    // 清空相似笔记推荐
    similarNotes.value = [];
    
    return response;
  } catch (error) {
    console.error('保存笔记失败:', error);
    ElMessage.error('保存笔记失败');
    throw error;
  }
};

// 创建新笔记
const createNewNote = () => {
  // 如果当前正在创建新笔记，直接返回
  if (isCreatingNote.value) return;
  
  // 如果当前有选中的笔记且内容已修改，提示保存
  if (currentNote.value && noteContent.value !== currentNote.value.content) {
    ElMessageBox.confirm('当前笔记已修改，是否保存？', '保存确认', {
      confirmButtonText: '保存',
      cancelButtonText: '不保存',
      distinguishCancelAndClose: true,
      closeOnClickModal: false
    }).then(() => {
      // 保存当前笔记
      saveNote().then(() => {
        // 创建新笔记
        initNewNote();
      });
    }).catch((action) => {
      if (action === 'cancel') {
        // 不保存，直接创建新笔记
        initNewNote();
      }
    });
  } else {
    // 直接创建新笔记
    initNewNote();
  }
};

// 初始化新笔记
const initNewNote = () => {
  currentNote.value = null;
  isCreatingNote.value = true;
  
  // 重置表单
  noteTitle.value = '';
  noteContent.value = '';
  noteTags.value = [];
  timestamps.value = [];
  
  // 更新编辑器状态
  updateEditorEditableState();
  
  // 清空相似笔记推荐
  similarNotes.value = [];
};

// 获取标签列表
const fetchTags = async () => {
  try {
    const response = await getTags();
    if (response.data && response.data.status === 'success') {
      allTags.value = response.data.data;
      console.log('获取到标签列表:', allTags.value);
    }
  } catch (error) {
    console.error('获取标签列表失败:', error);
    ElMessage.error('获取标签列表失败');
  }
};

// 加载视频信息
const loadVideo = async (id) => {
  try {
    console.log('开始加载视频，ID:', id);
    const response = await getVideo(id);
    console.log('视频API响应:', response);
    
    // 检查响应格式并适应不同的响应结构
    if (response.data) {
      // 直接使用响应数据，不检查status字段
      currentVideo.value = response.data;
      console.log('设置当前视频:', currentVideo.value);
      
      // 设置视频URL
      videoUrl.value = `/api/videos/${id}/stream`;
      console.log('视频URL已设置:', videoUrl.value);
      
      // 只加载语义合并字幕，不加载普通字幕
      await loadMergedSubtitles(id);
      
      // 确保视频元素更新
      nextTick(() => {
        if (videoPlayer.value) {
          videoPlayer.value.load();
          console.log('视频元素已重新加载');
          
          // 添加时间更新事件监听
          videoPlayer.value.addEventListener('timeupdate', onVideoTimeUpdate);
        } else {
          console.warn('视频元素不存在，无法加载视频');
        }
      });
    } else {
      console.warn('视频API响应格式不正确:', response);
    }
  } catch (error) {
    console.error('加载视频信息失败:', error);
    ElMessage.error('加载视频信息失败');
  }
};

// 加载语义合并字幕
const loadMergedSubtitles = async (id, force = false) => {
  console.log('开始加载合并字幕，视频ID:', id, '强制刷新:', force);
  try {
    // 构建API URL，添加force_refresh参数
    const apiUrl = `/api/subtitles/videos/${id}/subtitles/semantic-merged${force ? '?force_refresh=true' : ''}`;
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
        console.log('合并字幕示例:', JSON.stringify(response.data[0])); // 使用JSON.stringify显示完整结构
        subtitles.value = response.data; // 直接使用合并字幕
        ElMessage.success(`成功加载${response.data.length}条语义合并字幕${force ? ' (重新合并)' : ''}`);
      } else {
        console.warn('服务器返回了空的合并字幕数组');
        subtitles.value = [];
        ElMessage.warning('没有找到可合并的字幕');
      }
    } else {
      console.warn('合并字幕响应无效');
      subtitles.value = [];
      ElMessage.warning('获取合并字幕失败');
    }
  } catch (error) {
    console.error('加载合并字幕失败:', error);
    subtitles.value = [];
    ElMessage.error('加载合并字幕失败');
  }
};


// 将SRT时间格式转换为秒
const convertSRTTimeToSeconds = (timeString) => {
  const match = timeString.match(/(\d{2}):(\d{2}):(\d{2}),(\d{3})/);
  if (match) {
    const hours = parseInt(match[1]);
    const minutes = parseInt(match[2]);
    const seconds = parseInt(match[3]);
    const milliseconds = parseInt(match[4]);
    
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000;
  }
  return 0;
};

// 重置编辑器
const resetEditor = () => {
  noteTitle.value = '';
  noteContent.value = '';
  noteTags.value = [];
  timestamps.value = [];
  
  // 清空相似笔记推荐
  similarNotes.value = [];
};

// 删除当前笔记
const deleteCurrentNote = async () => {
  if (!currentNote.value) return;
  
  try {
    await ElMessageBox.confirm('确定要删除该笔记吗？此操作不可恢复', '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      distinguishCancelAndClose: true,
      closeOnClickModal: false
    });
    
    const response = await deleteNote(currentNote.value.id);
    
    if (response.data && response.data.status === 'success') {
      ElMessage.success('笔记已删除');
      currentNote.value = null;
      await fetchNotes();
      await fetchTags(); // 删除笔记后刷新标签列表
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除笔记失败:', error);
      ElMessage.error('删除笔记失败');
    }
  }
};

// 导出笔记
const exportCurrentNote  = () => {
  if (!currentNote.value && !isCreatingNote.value) return;
  
  let content = '';
  let filename = '';
  
  content = noteContent.value;
  filename = `${noteTitle.value}.md`;
  
  // 创建下载链接
  const blob = new Blob([content], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
  
  ElMessage.success(`笔记已导出为 ${filename}`);
};

// 批量导出笔记
const handleBatchExport = async () => {
  if (selectedNoteIds.value.length === 0) {
    ElMessage.warning('请先选择要导出的笔记');
    return;
  }

  try {
    ElMessage.info('正在准备导出文件...');
    const response = await batchExportNotes(selectedNoteIds.value);
    
    // 创建Blob对象
    const blob = new Blob([response.data], { type: 'application/zip' });
    
    // 创建下载链接
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    
    // 从响应头中获取文件名
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'notes_export.zip';
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename=(.+)/);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].replace(/"/g, '');
      }
    }
    
    link.download = filename;
    
    // 触发下载
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    ElMessage.success('笔记导出成功');
  } catch (error) {
    console.error('批量导出失败:', error);
    ElMessage.error('批量导出失败');
  }
};

// 批量删除笔记
const handleBatchDelete = async () => {
  if (selectedNoteIds.value.length === 0) {
    ElMessage.warning('请先选择要删除的笔记');
    return;
  }

  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedNoteIds.value.length} 条笔记吗？此操作不可恢复！`,
    '批量删除确认',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      const response = await batchDeleteNotes(selectedNoteIds.value);
      if (response.data && response.data.status === 'success') {
        ElMessage.success(response.data.message || '批量删除成功');
        await fetchNotes();
        await fetchTags(); // 删除笔记后刷新标签列表
        selectedNoteIds.value = [];
        showBatchOperations.value = false;
      }
    } catch (error) {
      console.error('批量删除失败:', error);
      ElMessage.error('批量删除失败');
    }
  }).catch(() => {
    // 用户取消删除
  });
};

// 切换批量操作模式
const toggleBatchOperations = () => {
  showBatchOperations.value = !showBatchOperations.value;
  if (!showBatchOperations.value) {
    selectedNoteIds.value = [];
  }
};

// 选择/取消选择笔记
const toggleNoteSelection = (noteId, val) => {
  if (val) {
    if (!selectedNoteIds.value.includes(noteId)) {
      selectedNoteIds.value.push(noteId);
    }
  } else {
    const index = selectedNoteIds.value.indexOf(noteId);
    if (index !== -1) {
      selectedNoteIds.value.splice(index, 1);
    }
  }
};

// 全选/取消全选
const toggleSelectAll = () => {
  if (selectedNoteIds.value.length === filteredNotes.value.length) {
    // 如果已全选，则取消全选
    selectedNoteIds.value = [];
  } else {
    // 否则全选
    selectedNoteIds.value = filteredNotes.value.map(note => note.id);
  }
};

// 标签相关功能
const showTagInput = () => {
  inputTagVisible.value = true;
  nextTick(() => {
    tagInput.value.focus();
  });
};

const confirmTag = () => {
  if (inputTagValue.value) {
    if (!noteTags.value.includes(inputTagValue.value)) {
      noteTags.value.push(inputTagValue.value);
    }
  }
  inputTagVisible.value = false;
  inputTagValue.value = '';
};

const removeTag = (tag) => {
  noteTags.value = noteTags.value.filter(t => t !== tag);
};

// 根据标签筛选笔记
const filterByTags = () => {
  fetchNotes();
};

// 获取标签类型（用于显示不同颜色）
const getTagType = (tag) => {
  const types = ['primary', 'success', 'warning', 'danger', 'info'];
  // 添加类型检查，确保tag是字符串
  if (!tag || typeof tag !== 'string') {
    return types[0]; // 默认返回第一个类型
  }
  const hash = tag.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return types[hash % types.length];
};

// 获取笔记预览文本
const getPreviewText = (note) => {
  let text = '';
  
  if (note.content) {
    // 从HTML中提取纯文本
    text = note.content.replace(/<[^>]*>/g, '');
  } else if (note.markdown_content) {
    text = note.markdown_content;
  }
  
  return text.length > 100 ? text.substring(0, 100) + '...' : text;
};

// 切换视频显示
// 删除toggleVideo函数，因为不再需要

// 切换笔记列表显示
const toggleNoteList = () => {
  showNoteList.value = !showNoteList.value;
};

// 切换Markdown预览
const togglePreview = () => {
  showPreview.value = !showPreview.value;
  console.log('预览模式状态:', showPreview.value);
  handlePreviewToggle(showPreview.value);
};

// 处理预览切换
const handlePreviewToggle = (isPreview) => {
  // 强制DOM更新
  nextTick(() => {
    if (isPreview) {
      console.log('预览内容:', renderedContent.value.substring(0, 100));
    } else {
      // 确保从预览模式切换回编辑模式时，编辑区域可见
      const textarea = noteEditor.value;
      if (textarea) {
        textarea.focus();
      }
    }
  });
};

// 取消创建新笔记
const cancelCreate = () => {
  isCreatingNote.value = false;
  noteTitle.value = '';
  noteContent.value = '';
  noteTags.value = [];
  timestamps.value = [];
  currentNote.value = null;
};

// 处理笔记选择
const handleNoteSelect = (noteId) => {
  const selectedNote = notes.value.find(note => note.id === noteId);
  if (selectedNote) {
    selectNote(selectedNote);
  }
};

// 移除已选标签
const removeSelectedTag = (tag) => {
  selectedTags.value = selectedTags.value.filter(t => t !== tag);
  fetchNotes();  //调用fetchNotes更新筛选结果
};

// 处理单个笔记的操作
const handleNoteItemAction = async (action, noteId) => {
  switch (action) {
    case 'edit':
      handleNoteSelect(noteId);
      break;
    case 'export':
      await exportSingleNote(noteId);
      break;
    case 'delete':
      await deleteSingleNote(noteId);
      break;
  }
};

// 导出单个笔记
const exportSingleNote = async (noteId) => {
  try {
    // 先获取笔记信息
    const noteInfo = await getNote(noteId);
    const noteTitle = noteInfo.data.data.title;
    
    // 导出笔记
    const response = await exportNote(noteId);
    const blob = new Blob([response.data], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    
    // 使用笔记标题作为文件名
    const safeTitle = noteTitle.replace(/[^\w\s-]/g, '_');
    const filename = `${safeTitle}.md`;
    
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    ElMessage.success(`笔记已导出为 ${filename}`);
  } catch (error) {
    console.error('导出笔记失败:', error);
    ElMessage.error('导出笔记失败');
  }
};

// 删除单个笔记
const deleteSingleNote = async (noteId) => {
  try {
    const result = await ElMessageBox.confirm(
      '确定要删除这个笔记吗？此操作不可恢复。',
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );
    
    if (result === 'confirm') {
      await deleteNote(noteId);
      ElMessage.success('笔记已删除');
      
      // 如果当前正在编辑的笔记被删除，重置编辑器
      if (currentNote.value && currentNote.value.id === noteId) {
        currentNote.value = null;
      }
      
      // 刷新笔记列表和标签列表
      await fetchNotes();
      await fetchTags(); // 删除笔记后刷新标签列表
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除笔记失败:', error);
      ElMessage.error('删除笔记失败');
    }
  }
};

// 清除标签筛选
const clearTagFilter = () => {
  selectedTags.value = [];
  fetchNotes();
};

// 判断是否为当前字幕
const isCurrentSubtitle = (subtitle) => {
  if (!currentSubtitle.value) return false;
  // 直接比较对象引用
  return subtitle === currentSubtitle.value;
};

// 添加字幕到笔记
const addSubtitleToNote = (subtitle) => {
  if (!noteEditor.value || (!currentNote.value && !isCreatingNote.value)) return;
  
  // 获取字幕文本和时间
  const subtitleContent = subtitle.text || subtitle.content || '';
  const timeSeconds = subtitle.start_time || subtitle.start || 0;
  const formattedTime = formatTimeMMSS(timeSeconds);
  
  // 创建一个更美观的时间戳标记
  // 格式: [03:02]{{timestamp:182}}
  const timestampMark = `[${formattedTime}]{{timestamp:${timeSeconds}}}`;
  
  // 添加带时间戳的字幕文本到编辑器
  const subtitleText = `> ${timestampMark} ${subtitleContent}\n\n`;
  
  
  // 如果使用的是Vditor编辑器
  if (vditorInstance.value) {
    const currentContent = vditorInstance.value.getValue();
    vditorInstance.value.setValue(currentContent + subtitleText);
  } else {
    // 使用普通文本编辑器
    // 获取当前光标位置
    const textarea = noteEditor.value;
    const cursorPosition = textarea.selectionStart;
    
    // 在光标位置插入字幕文本
    const currentContent = noteContent.value;
    noteContent.value = 
      currentContent.substring(0, cursorPosition) + 
      subtitleText + 
      currentContent.substring(cursorPosition);
    
    // 更新光标位置到插入文本后
    nextTick(() => {
      textarea.focus();
      const newPosition = cursorPosition + subtitleText.length;
      textarea.setSelectionRange(newPosition, newPosition);
    });
  }
  
  // 记录字幕时间戳
  const timestampObj = {
    time_seconds: timeSeconds,
    subtitle_text: subtitleContent
  };
  
  // 检查是否已存在相同时间戳的记录
  if (!timestamps.value.some(t => t.time_seconds === timestampObj.time_seconds)) {
    timestamps.value.push(timestampObj);
  }
  
  // 自动保存笔记
  if (currentNote.value) {
    saveNote();
  } else { // 即使没有当前笔记，也保存到本地存储
    autoSaveToLocalStorage();
  }
};

// 处理字幕点击事件
const handleSubtitleClick = (subtitle) => {
  // 首先跳转到对应的视频时间点
  const startTime = subtitle.start_time || subtitle.start;
  seekToTime(startTime);
  
  // 然后添加字幕到笔记
  addSubtitleToNote(subtitle);
};

// 移除时间戳
const removeTimestamp = (index) => {
  if (index >= 0 && index < timestamps.value.length) {
    timestamps.value.splice(index, 1);
    
    // 如果当前有笔记，自动保存
    if (currentNote.value) {
      saveNote();
    } else {
      // 即使没有当前笔记，也保存到本地存储
      autoSaveToLocalStorage();
    }
  }
};

// 跳转到视频特定时间点
const seekToTime = (timeSeconds) => {
  if (videoPlayer.value && typeof timeSeconds === 'number') {
    videoPlayer.value.currentTime = timeSeconds;
    // 如果视频暂停状态，自动播放
    if (videoPlayer.value.paused) {
      videoPlayer.value.play().catch(err => {
        console.error('自动播放失败:', err);
      });
    }
    
    // 设置需要滚动到字幕的标志
    needScrollToSubtitle.value = true;
  }
};

// 处理文本编辑器点击事件
const handleEditorClick = (event) => {
  if (!noteEditor.value) return;
  
  // 获取当前选中的文本
  const selectedText = window.getSelection().toString();
  
  // 如果没有选中文本，检查是否点击了时间戳
  if (!selectedText) {
    // 获取编辑器内容
    const content = noteContent.value;
    
    // 获取光标位置
    const cursorPosition = noteEditor.value.selectionStart;
    
    // 查找光标附近的时间戳标记 - 新格式
    const timestampRegex = /\[([0-9:]+)\]\{\{timestamp:(\d+\.?\d*)\}\}/g;
    let match;
    
    // 查找所有时间戳标记
    while ((match = timestampRegex.exec(content)) !== null) {
      const startIndex = match.index;
      const endIndex = startIndex + match[0].length;
      
      // 检查光标是否在时间戳标记内或附近（允许5个字符的误差）
      if (Math.abs(cursorPosition - startIndex) <= 5 || 
          (cursorPosition >= startIndex && cursorPosition <= endIndex)) {
        // 提取时间戳
        const timeSeconds = parseFloat(match[2]);
        
        // 跳转到对应时间
        seekToTime(timeSeconds);
        break;
      }
    }
  }
};

// 处理同步标签
const handleSyncTags = async () => {
  try {
    ElMessage.info('正在同步标签数据...');
    const response = await syncTags();
    if (response.data && response.data.status === 'success') {
      ElMessage.success('标签数据同步成功');
      // 刷新标签列表
      await fetchTags();
      // 刷新笔记列表
      await fetchNotes();
    }
  } catch (error) {
    console.error('同步标签失败:', error);
    ElMessage.error('同步标签失败');
  }
};
</script>

<style scoped>
.timestamp-link {
  color: #409eff;
  font-weight: bold;
  cursor: pointer;
  text-decoration: underline;
}

.timestamp-link:hover {
  color: #66b1ff;
}

/* 整体容器 */
.note-page-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  overflow: hidden;
  background-color: #f8f9fa;
  position: relative;
}

/* 顶部工具栏 */
.note-toolbar {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: linear-gradient(135deg, #ffffff, #f5f7fa);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  z-index: 10;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.left-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.left-actions .el-button {
  transition: all 0.3s ease;
}

.left-actions .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.right-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.right-actions .el-button {
  transition: all 0.3s ease;
}

.right-actions .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.search-container {
  position: relative;
  margin-left: 15px;
}

.search-input {
  width: 250px;
  transition: all 0.3s ease;
}

.search-input:focus, .search-input:hover {
  width: 300px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tag-filter-container {
  margin-left: auto;
  margin-right: 20px;
}

.tag-filter-button {
  display: flex;
  align-items: center;
  gap: 5px;
  transition: all 0.3s ease;
}

.tag-filter-button:hover {
  transform: translateY(-2px);
}

.tag-badge {
  margin-left: 5px;
  background: linear-gradient(135deg, #ff9a9e, #fad0c4);
  color: white;
  border-radius: 10px;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: bold;
}

/* 主要内容区域 */
.note-content-container {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
}

/* 左侧区域 */
.left-section {
  width: 45%;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(0, 0, 0, 0.08);
  overflow: hidden;
  background-color: #fff;
  box-shadow: 4px 0 12px rgba(0, 0, 0, 0.05);
  z-index: 5;
}

/* 视频播放区域 */
.video-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 15px;
  min-height: 40%;
  max-height: 60%;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  background: linear-gradient(to bottom, #ffffff, #f8f9fa);
  border: 1px solid #9d84d8; /* 添加浅紫色边框 */
  border-radius: 8px;
  margin: 5px;
}

.video-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding: 5px 0;
  height: 30px;
  position: relative;
}

.video-header::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 18px;
  background: linear-gradient(to bottom, #ff9a9e, #fad0c4);
  border-radius: 2px;
}

.video-header h3 {
  margin-left: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.video-player-wrapper {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #000;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.video-player-wrapper:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  transform: translateY(-2px);
}

.video-element {
  width: 100%;
  height: 100%;
  object-fit: contain;
  aspect-ratio: 16/9;
}

/* 调整视频播放器容器高度 */
.video-container {
  height: calc(50vh - 100px); /* 使用视口高度的一半减去一些空间 */
  min-height: 250px; /* 确保最小高度 */
}

.no-video-placeholder {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #909399;
  height: 100%;
}

.no-video-placeholder .el-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

/* 字幕区域 */
.subtitle-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 15px;
  overflow: hidden;
  background: linear-gradient(to bottom, #f8f9fa, #ffffff);
  border: 1px solid #9674ee; /* 添加浅紫色边框 */
  border-radius: 8px;
  margin: 5px; 
}

.subtitle-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
  padding: 3px 0;
  height: 25px;
  position: relative;
}

.subtitle-header::before {
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

.subtitle-header h3 {
  margin-left: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

/* 调整字幕列表容器 */
.subtitle-list-wrapper {
  flex: 1; 
  overflow-y: auto;
  background-color: #fff;
  border-radius: 8px;
  padding: 10px;
  padding-bottom: 20px; /* 增加底部内边距，确保最后一项完全显示 */
  height: calc(50vh - 80px);
  min-height: 300px;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.05);
}

/* 调整字幕列表 */
.subtitle-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 字幕项 */
.subtitle-item {
  padding: 12px 15px;
  border-radius: 8px;
  background-color: #f9f9f9;
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.subtitle-item:hover {
  background-color: #f0f0f0;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.subtitle-item.current {
  background-color: rgba(161, 196, 253, 0.2);
  border-left: 3px solid #a1c4fd;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* 确保最后一个字幕项有足够的底部边距 */
.subtitle-item:last-child {
  margin-bottom: 20px;
}

.subtitle-item.active {
  background-color: #e6f1fc;
  border-left: 3px solid #409eff;
}

.subtitle-time {
  flex-shrink: 0; /* 防止时间标签被压缩 */
  margin-right: 8px;
  min-width: 40px; /* 给时间标签一个固定宽度 */
}

.subtitle-text {
  flex: 1;
  word-break: break-word; /* 允许在任何字符间换行 */
  overflow-wrap: break-word; /* 确保长单词也能换行 */
  line-height: 1.5; /* 增加行高 */
}
.no-subtitles {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #909399;
  height: 100%;
}

.no-subtitles .el-icon {
  font-size: 32px;
  margin-bottom: 10px;
}

/* 右侧区域 */
.right-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #fff;
  position: relative;
}

.note-editor-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 15px;
  overflow: hidden;
}

.note-editor-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 8px;
  background-color: #fff;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.note-editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  background: linear-gradient(135deg, #ffffff, #f5f7fa);
}

.editor-title {
  flex: 1;
  margin-right: 15px;
}

.editor-title :deep(.el-input) {
  box-shadow: none !important;
  border: none !important;
}

.editor-title :deep(.el-input__wrapper) {
  box-shadow: none !important;
  background: transparent !important;
  padding: 0 !important;
  margin: 0 !important;
}

.editor-title :deep(.el-input__inner) {
  border: 2px solid #ffb6c1 !important;
  border-radius: 4px !important;
  padding-left: 20px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 0 5px rgba(255, 182, 193, 0.3) !important;
  background-color: #fff !important;
}

.editor-title :deep(.el-input__inner:focus) {
  border-color: #ff69b4 !important;
  box-shadow: 0 0 8px rgba(255, 105, 180, 0.5) !important;
}

.editor-title :deep(.el-input__inner) {
  border: 2px solid #ffb6c1 !important;
  border-radius: 12px !important;
  padding-left: 30px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  transition: all 0.3s ease !important; 
  box-shadow: 0 0 5px rgba(255, 182, 193, 0.3) !important; 
  background-color: #fff !important;
}

.editor-title :deep(.el-input__inner:focus) {
  border-color: #ff69b4 !important;
  box-shadow: 0 0 8px rgba(255, 105, 180, 0.5) !important;
}

.note-tags-and-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 15px;
}

.note-tags-editor {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 5px;
}

.editor-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.editor-actions .el-button {
  transition: all 0.3s ease;
}

.editor-actions .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.editor-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.editor-wrapper.disabled {
  opacity: 0.7;
  pointer-events: none;
}

.smart-note-editor {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  padding: 10px 15px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-right: 15px;
}

.toolbar-divider {
  width: 1px;
  height: 20px;
  background-color: #dcdfe6;
  margin: 0 10px;
}

.toolbar-button {
  padding: 6px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.toolbar-button:hover {
  background-color: #ecf5ff;
  color: #409eff;
}

.toolbar-button.active {
  background-color: #ecf5ff;
  color: #409eff;
}

.toolbar-group:last-child {
  border-right: none;
  padding-right: 0;
  margin-right: 0;
}

.editor-content-area {
  flex: 1;
  overflow: auto;
  position: relative;
}

/* 提示用户时间戳是可点击的 */
.editor-content-area::after {
  content: "提示：在编辑模式下点击时间戳 [[timestamp:...]] 可跳转到对应视频位置";
  position: absolute;
  bottom: 5px;
  right: 10px;
  font-size: 12px;
  color: #909399;
  opacity: 0.8;
}

.note-textarea {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 300px;
  padding: 12px;
  border: none;
  resize: none;
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
  background-color: #fff;
  outline: none;
  font-family: 'Source Code Pro', monospace,'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}

/* 移除原来的预览切换按钮样式 */
.preview-toggle {
  display: none;
}

.preview-toggle-toolbar {
  display: flex;
  align-items: center;
  padding: 0 10px;
}

.markdown-preview {
  padding: 12px;
  background-color: #f9f9f9;
  border-radius: 4px;
  overflow: auto;
  height: 100%;
  width: 100%;
  position: absolute;
  top: 0;
  left: 0;
  z-index: 20; /* 确保在文本框上方 */
}

/* 编辑器禁用遮罩 */
.editor-mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

.mask-content {
  text-align: center;
  color: #909399;
}

.mask-content .el-icon {
  font-size: 32px;
  margin-bottom: 10px;
}

/* 相似笔记推荐 */
.similar-notes-section {
  margin-top: 20px;
  border-radius: 8px;
  background-color: #f9f9f9;
  padding: 15px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  max-height: 30%; /* 设置最大高度为右侧区域的40% */
  display: flex;
  flex-direction: column;
  border: 1px solid #30a1de; /* 添加浅紫色边框 */
  border-radius: 8px;
  margin: 8px;
}

.similar-notes-header {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
  position: relative;
  flex-shrink: 0; /* 防止头部被压缩 */
  height: 30px; /* 添加固定高度 */
}

.similar-notes-header::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 18px;
  background: linear-gradient(to bottom, #fbc2eb, #a6c1ee);
  border-radius: 2px;
}

.similar-notes-header h4 {
  margin-left: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.similar-notes-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto; /* 添加垂直滚动条 */
  flex: 1; /* 占用剩余空间 */
  padding-right: 5px; /* 为滚动条留出空间 */
}

.similar-note-item {
  padding: 12px;
  border-radius: 8px;
  background-color: #fff;
  transition: all 0.3s ease;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  border-left: 3px solid transparent;
}

.similar-note-item:hover {
  background-color: #f0f0f0;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.similar-note-item:last-child {
  margin-bottom: 0;
}

.similar-note-title {
  font-weight: bold;
  margin-bottom: 4px;
  color: #303133;
}

.similar-note-preview {
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
  line-height: 1.5;
  max-height: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.similar-note-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.similar-note-date {
  color: #909399;
}

.similar-note-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 8px;
}

/* 笔记列表下拉菜单 */
.note-dropdown {
  margin-left: 15px;
}

.note-dropdown-menu {
  max-height: 300px;
  overflow-y: auto;
}

.note-dropdown-item {
  display: flex;
  align-items: center;
  padding: 5px 0;
  width: 100%;
}

.note-dropdown-content {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.note-item-actions {
  margin-left: 8px;
  display: flex;
  align-items: center;
}

.note-checkbox {
  margin-right: 8px;
}

/* 批量操作相关样式 */
.batch-operations-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 15px;
  background: linear-gradient(135deg, #f5f7fa, #e4e7eb);
  border-top: 1px solid #e4e7ed;
}

.batch-operations-buttons {
  display: flex;
  gap: 10px;
  margin-top: 5px;
}

.selected-count {
  font-size: 12px;
  color: #409EFF;
  margin-top: 5px;
}

.is-active {
  color: #409EFF;
  font-weight: bold;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .note-content-container {
    flex-direction: column;
  }
  
  .left-section, .right-section {
    width: 100%;
  }
  
  .left-section {
    height: 50%;
    border-right: none;
    border-bottom: 1px solid #e0e0e0;
  }
  
  .right-section {
    height: 50%;
  }
}


/* 修改左侧栏样式 */
.left-panel {
  width: 300px; /* 可以根据需要调整宽度 */
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e0e0e0;
  overflow: hidden;
  padding: 0; /* 减少内边距 */
}

.tag-filter-popover {
  padding: 0;
}

.tag-filter-content {
  padding: 10px;
}

.tag-filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.tag-filter-list {
  max-height: 200px;
  overflow-y: auto;
}

.selected-tags {
  margin-top: 15px;
  padding: 10px;
  background-color: #f0f9ff;
  border-radius: 4px;
  border: 1px solid #e1f3ff;
}

.selected-tags-header {
  font-weight: bold;
  margin-bottom: 8px;
  color: #606266;
}

.selected-tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
/* 笔记管理弹出框 */
.note-manager-popover {
  padding: 0 !important;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
}

.note-manager-container {
  display: flex;
  height: 500px;
  overflow: hidden;
}

.tags-panel {
  width: 200px;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: linear-gradient(135deg, #f5f7fa, #e4e7eb);
}

.panel-header {
  padding: 15px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #ffffff, #f5f7fa);
}

.panel-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  position: relative;
  padding-left: 12px;
}

.panel-header h4::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 16px;
  background: linear-gradient(to bottom, #a1c4fd, #c2e9fb);
  border-radius: 2px;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
  max-height: 150px;
  overflow-y: auto;
  padding: 5px;
  border-radius: 4px;
  background-color: #f9f9f9;
}

.clickable-tag {
  cursor: pointer;
  margin-right: 0 !important;
  transition: all 0.2s ease;
  position: relative;
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.clickable-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.tag-count {
  margin-left: 5px;
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  padding: 0 6px;
  font-size: 12px;
}

.notes-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0 15px;
}

.notes-list {
  flex: 1;
  overflow-y: auto;
  padding: 5px 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.note-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 12px;
  min-height: 98px;
  border-radius: 8px;
  background-color: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
  border: 1px solid #ebeef5;
}

.note-item-content {
  flex: 1;
  min-width: 0; /* 防止子元素溢出 */
}

.note-item:hover {
  background-color: #f9f9f9;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.note-item.selected {
  background-color: rgba(64, 158, 255, 0.1);
  border-left: 3px solid #409eff;
}

.note-title {
  font-weight: bold;
  margin-bottom: 5px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.note-preview {
  color: #606266;
  font-size: 13px;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.note-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #909399;
}

.note-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  align-items: center;
  max-width: 70%;
}

.note-date {
  color: #909399;
}

.note-tag {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  background-color: rgba(64, 158, 255, 0.1);
  color: #409eff;
}

.more-tags {
  font-size: 12px;
  color: #909399;
}

.note-actions {
  display: flex;
  gap: 5px;
  margin-top: 10px;
}

.note-actions .el-button {
  transition: all 0.3s ease;
}

.note-actions .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.add-to-note-btn {
  margin-top: 8px;
  transition: all 0.3s ease;
}

.add-to-note-btn:hover {
  transform: translateX(2px);
}

/* 笔记列表样式 */
.notes-list.card-layout {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 10px;
  overflow-y: auto;
  height: calc(100% - 60px); /* 增加高度，确保显示完整 */
  padding-bottom: 30px; /* 增加底部内边距，确保最后一行显示完整 */
}

.note-item {
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 12px; /* 增加卡片间距 */
  border: 1px solid #ebeef5;
  cursor: pointer;
  display: flex;
  align-items: flex-start;
  transition: all 0.3s;
  background-color: #fff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

/* 在你的样式部分添加 */
.highlight-flash {
  animation: flash 1s ease;
}

@keyframes flash {
  0%, 100% { background-color: transparent; }
  50% { background-color: rgba(255, 215, 0, 0.5); /* 金色半透明 */ }
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #e0e0e0;
}

.tag-actions {
  display: flex;
  gap: 5px;
}

.search-info {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
  margin-bottom: 5px;
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  z-index: 100;
  max-height: 300px;
  overflow-y: auto;
}

.search-result-item {
  padding: 10px 15px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.2s ease;
}

.search-result-item:hover {
  background-color: #f5f7fa;
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-title {
  font-weight: bold;
  margin-bottom: 5px;
}

.search-result-preview {
  font-size: 12px;
  color: #606266;
  margin-bottom: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.search-result-tags {
  display: flex;
  gap: 5px;
}

.search-result-more {
  padding: 10px;
  text-align: center;
  color: #409eff;
  cursor: pointer;
  font-size: 14px;
}

.search-result-more:hover {
  background-color: #f5f7fa;
}

.toolbar-dropdown-button {
  background-color: #ffb6c1;
  border-color: #ff69b4;
  color: #fff;
  padding: 8px 15px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.toolbar-dropdown-button:hover,
.toolbar-dropdown-button:focus {
  background-color: #ff69b4;
  border-color: #ff1493;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background-color: #f9f9f9;
  border-bottom: 1px solid #eee;
}

.el-dropdown-menu__item .el-icon {
  margin-right: 5px;
  color: #ff69b4;
}

.markdown-preview {
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.6;
}

.markdown-preview p {
  margin-bottom: 16px;
}

.markdown-preview br {
  display: block;
  content: "";
  margin-top: 0.5em;
}

.note-app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.note-header {
  flex-shrink: 0; /* 防止头部被压缩 */
}

.note-content-container {
  flex: 1;
  min-height: 0; /* 防止内容区域溢出 */
}

.left-section, .right-section {
  min-height: 0; /* 防止内容区域溢出 */
  overflow: hidden;
}
</style>