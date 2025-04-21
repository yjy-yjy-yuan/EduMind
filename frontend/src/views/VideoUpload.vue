<template>
  <div class="upload-container">
    <section class="video-hero-section">
      <div class="hero-overlay"></div>
      <div class="hero-container">
        <div class="hero-content-wrapper">
          <div class="hero-text">
            <h1 class="main-title">视频管理中心</h1>
            <p class="subtitle">上传、管理和处理您的教育视频</p>
            <div class="hero-description-container">
              <p class="hero-description">🎉 添加教学视频,我们将辅助您进行更加高效地学习。😊</p>
            </div>
          </div>
        </div>
      </div>
    </section>
    
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <div class="title-wrapper">
            <i class="title-icon">
              <el-icon><Upload /></el-icon>
            </i>
            <h2>视频上传</h2>
          </div>
        </div>
      </template>
      
      <el-form ref="uploadForm" :model="formData" label-width="100px" class="upload-form">
        <!-- 本地视频上传 -->
        <el-form-item label="本地视频">
          <div class="upload-flex-container">
            <el-upload
              class="upload-demo"
              drag
              :action="null"
              :http-request="handleUpload"
              :before-upload="beforeUpload"
              :show-file-list="false"
              accept=".mp4,.avi,.mov,.mkv,.webm"
            >
              <el-icon><Upload /></el-icon>
              <div class="el-upload__text">
                拖拽文件到此处或 <em>点击上传</em>
              </div>
            </el-upload>
            
            <div class="upload-format-tip">
              <el-icon><InfoFilled /></el-icon>
              <span>支持的格式：MP4, AVI, MOV, MKV, WEBM</span>
            </div>
          </div>
          
          <!-- 上传进度条 -->
          <div v-if="uploadProgress > 0" class="progress-container">
            <el-progress 
              :percentage="uploadProgress" 
              :status="uploadStatus"
              :stroke-width="15"
            />
            <div v-if="uploadStepInfo" class="processing-step">
              当前步骤: {{ uploadStepInfo }}
            </div>
          </div>
        </el-form-item>

        <!-- 视频链接 -->
        <el-form-item label="视频链接">
          <el-input 
            v-model="formData.videoUrl" 
            placeholder="请输入B站、YouTube视频链接"
            class="video-url-input"
            size="large"
          >
            <template #append>
              <el-button 
                @click="handleUrlUpload" 
                :loading="urlUploading"
                type="primary"
                class="submit-url-button"
              >
                {{ urlUploading ? '提交中...' : '提交链接' }}
              </el-button>
            </template>
          </el-input>
          <div class="el-upload__tip">
            支持B站、YouTube视频链接
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 视频列表 -->
    <el-card class="video-list-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <div class="title-wrapper">
            <i class="title-icon">
              <el-icon><VideoCamera /></el-icon>
            </i>
            <h3>已上传视频</h3>
          </div>
          <div>
            <el-button 
              v-if="!batchDeleteMode"
              type="primary" 
              @click="enterBatchDeleteMode"
            >
              批量删除
            </el-button>
            <template v-else>
              <el-button 
                type="danger" 
                :disabled="selectedVideos.length === 0"
                @click="handleBatchDelete"
              >
                删除选中({{ selectedVideos.length }})
              </el-button>
              <el-button @click="exitBatchDeleteMode">
                取消
              </el-button>
            </template>
            <el-button @click="refreshList" :icon="Refresh" circle />
          </div>
        </div>
      </template>
      
      <el-table 
        ref="videoTable"
        :data="paginatedVideoList" 
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column v-if="batchDeleteMode" type="selection" width="55" align="center" />
        <el-table-column prop="filename" label="视频名称" width="200" align="center"/>
        <el-table-column prop="status" label="处理状态" width="80" align="center">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="标签" width="80" align="center">
          <template #default="scope">
            <div class="video-tags">
              <template v-if="scope.row.tags && scope.row.tags.length > 0">
                <el-tag 
                  v-for="(tag, index) in scope.row.tags" 
                  :key="index"
                  size="small"
                  :type="getTagType(index)"
                  class="video-tag"
                  effect="light"
                >
                  {{ tag }}
                </el-tag>
              </template>
              <span v-else-if="scope.row.autoGeneratingTags" class="generating-tags">标签生成中...</span>
              <span v-else-if="scope.row.status === 'completed'" class="no-tags">无标签</span>
              <span v-else class="no-tags">处理完成后生成</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="封面" width="120" align="center">
          <template #default="scope">
            <el-image 
              v-if="scope.row.preview_filename"
              style="width: 100px; height: 60px"
              :src="getPreviewUrl(scope.row)"
              :preview-src-list="scope.row.preview_filename ? [getPreviewUrl(scope.row)] : []"
              :preview-teleported="true"
              fit="cover"
            />
            <span v-else>无预览图</span>
          </template>
        </el-table-column>
        <el-table-column label="视频摘要" align="center">
          <template #default="scope">
            <div class="video-summary-box">
              <div v-if="scope.row.summary" class="summary-content">
                {{ scope.row.summary }}
              </div>
              <div v-else-if="scope.row.autoGeneratingSummary" class="summary-placeholder summary-generating">
                <span>摘要正在生成中...</span>
              </div>
              <div v-else-if="scope.row.status === 'completed'" class="summary-actions">
                <el-button 
                  size="small" 
                  type="primary" 
                  @click="generateSummary(scope.row)"
                  :loading="scope.row.generatingSummary"
                >
                  {{ scope.row.generatingSummary ? '生成中...' : '生成摘要' }}
                </el-button>
              </div>
              <div v-else class="summary-placeholder">
                <span>{{ getSummaryPlaceholder(scope.row.status) }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" align="center">
          <template #default="scope">
            <div class="action-buttons">
              <el-icon 
                class="action-icon play-icon" 
                :class="{ disabled: !['completed'].includes(scope.row.status) }"
                @click="['completed'].includes(scope.row.status) ? handlePlay(scope.row) : null"
                title="播放视频"
              >
                <VideoPlay />
              </el-icon>
              <el-icon 
                class="action-icon process-icon" 
                :class="{ disabled: !['uploaded', 'pending'].includes(scope.row.status) || scope.row.status === 'downloading' }"
                @click="['uploaded', 'pending'].includes(scope.row.status) && scope.row.status !== 'downloading' ? handleProcess(scope.row) : null"
                title="处理视频"
              >
                <VideoCamera />
              </el-icon>
              <el-icon 
                class="action-icon delete-icon" 
                :class="{ disabled: ['processing', 'downloading'].includes(scope.row.status) }"
                @click="!['processing', 'downloading'].includes(scope.row.status) ? handleDelete(scope.row) : null"
                title="删除视频"
              >
                <Delete />
              </el-icon>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container" v-if="videoList.length > 0">
        <div class="custom-pagination">
          <button 
            class="pagination-btn prev" 
            :disabled="currentPage === 1"
            @click="changePage(currentPage - 1)"
            title="上一页"
          >
            <el-icon><ArrowLeft /></el-icon>
          </button>
          
          <div class="page-info">
            {{ currentPage }}/{{ totalPages }}
          </div>
          
          <button 
            class="pagination-btn next" 
            :disabled="currentPage === totalPages"
            @click="changePage(currentPage + 1)"
            title="下一页"
          >
            <el-icon><ArrowRight /></el-icon>
          </button>
        </div>
      </div>
      
      <!-- 空状态提示 -->
      <div v-if="videoList.length === 0 && !loading" class="empty-state">
        <div class="empty-icon">
          <el-icon><video-camera /></el-icon>
        </div>
        <p>暂无上传视频</p>
        <p class="empty-tip">您可以通过上方表单上传视频文件或提交视频链接</p>
      </div>
    </el-card>

    <!-- 页脚 -->
    <div class="page-footer">
      <div class="footer-content">
        <p>&copy; 2025 AI-EdVision 智能教育视频分析系统</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'

// 导入视频处理管理器
import { 
  checkProcessingVideos, 
  saveProcessingState, 
  removeProcessingState,
  checkVideoProcessStatus
} from '@/components/VideoProcessingManager'

// 添加一个标志变量，用于标识是否正在生成摘要
const isGeneratingSummary = ref(false)
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { 
  Delete, 
  VideoPlay,
  Upload, 
  Refresh, 
  ArrowLeft,
  ArrowRight,
  VideoCamera,
  InfoFilled
} from '@element-plus/icons-vue'
import { 
  uploadLocalVideo, 
  uploadVideoUrl, 
  getVideoList, 
  processVideo,
  getVideoPreview,
  deleteVideo,
  getVideoStatus,
  getVideo,
  saveVideoSummary
} from '@/api/video'

const formData = ref({
  videoUrl: ''
})

const uploadProgress = ref(0)
const uploadStatus = ref('')
const uploadStepInfo = ref('')
const urlUploading = ref(false)
const loading = ref(false)
const videoList = ref([])
const selectedVideos = ref([])
const videoTable = ref(null)
const batchDeleteMode = ref(false)

const pollingTimers = ref({})
const processingTimers = ref({})

// 分页相关变量
const currentPage = ref(1)
const pageSize = 4

// 计算总页数
const totalPages = computed(() => {
  return Math.max(1, Math.ceil(videoList.value.length / pageSize))
})

// 计算要显示的页码
const displayPages = computed(() => {
  // 创建从1到totalPages的数组
  const pages = []
  for (let i = 1; i <= totalPages.value; i++) {
    pages.push(i)
  }
  return pages
})

// 计算当前页应该显示的视频列表
const paginatedVideoList = computed(() => {
  // 确保currentPage在有效范围内
  if (currentPage.value < 1) {
    currentPage.value = 1
  } else if (currentPage.value > totalPages.value && totalPages.value > 0) {
    currentPage.value = totalPages.value
  }
  
  const startIndex = (currentPage.value - 1) * pageSize
  const endIndex = startIndex + pageSize
  return videoList.value.slice(startIndex, endIndex)
})

// 切换页面的函数
const changePage = (page) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  clearSelection()
  console.log('切换到页码:', page)
}

// 监听视频列表变化
watch(videoList, () => {
  console.log('视频列表变化，总数:', videoList.value.length)
  console.log('当前页码:', currentPage.value, '总页数:', totalPages.value)
  
  // 如果当前页超出范围，重置到第一页
  if (currentPage.value > totalPages.value) {
    currentPage.value = Math.max(1, totalPages.value)
  }
  
  // 如果没有视频，重置到第一页
  if (videoList.value.length === 0) {
    currentPage.value = 1
  }
}, { deep: true })

// 在组件挂载后获取视频列表
onMounted(async () => {
  await refreshList()
  // 确保初始页码为1
  nextTick(() => {
    currentPage.value = 1
    
    // 检查是否有正在处理的视频，并恢复轮询
    checkProcessingVideos(
      videoList.value, 
      startPollingVideoStatus, 
      startPollingProcessStatus,
      refreshList
    )
  })
})

// 上传前检查
const beforeUpload = (file) => {
  const isVideo = file.type.startsWith('video/')
  if (!isVideo) {
    ElMessage.error('只能上传视频文件！')
    return false
  }
  return true
}

// 处理文件上传
const handleUpload = async ({ file }) => {
  uploadProgress.value = 0
  uploadStatus.value = ''
  uploadStepInfo.value = '准备上传...'

  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await uploadLocalVideo(formData, (progressEvent) => {
      const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
      uploadProgress.value = progress
      if (progress < 100) {
        uploadStepInfo.value = `上传中... ${progress}%`
      } else {
        uploadStepInfo.value = '处理中...'
      }
    })

    // 确保response.data存在
    if (!response || !response.data) {
      throw new Error('服务器响应格式错误')
    }

    const responseData = response.data

    if (responseData.duplicate) {
      // 处理重复视频的情况
      const existingVideo = responseData.existingVideo
      ElMessageBox.confirm(
        `该视频已存在（文件名：${existingVideo.filename}），是否查看已有视频？`,
        '视频已存在',
        {
          confirmButtonText: '查看视频',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        // 跳转到视频播放页面
        router.push({
          name: 'VideoPlayer',
          params: { id: existingVideo.id }
        })
      }).catch(() => {
        // 用户取消，不做任何操作
      })
    } else {
      // 处理正常上传的情况
      uploadProgress.value = 100
      uploadStatus.value = 'success'
      uploadStepInfo.value = '上传成功'
      ElMessage.success(responseData.message || '视频上传成功')
      refreshList()
    }
  } catch (error) {
    console.error('上传错误:', error)
    uploadStatus.value = 'exception'
    uploadStepInfo.value = '上传失败'
    ElMessage.error('上传失败：' + (error.response?.data?.error || error.message || '未知错误'))
  }
}

// 处理链接上传
const handleUrlUpload = async () => {
  // 检查URL是否为空
  if (!formData.value.videoUrl) {
    ElMessage.warning('请输入视频链接')
    return
  }

  // 检查URL是否有效
  const isBilibili = formData.value.videoUrl.includes('bilibili.com')
  const isYoutube = formData.value.videoUrl.includes('youtube.com') || formData.value.videoUrl.includes('youtu.be')
  const isIcourse163 = formData.value.videoUrl.includes('icourse163.org')

  if (!isBilibili && !isYoutube && !isIcourse163) {
    ElMessage.warning('目前仅支持B站、YouTube和中国大学慕课视频链接')
    return
  }

  // 显示加载状态
  urlUploading.value = true
  uploadProgress.value = 0
  uploadStatus.value = '正在提交视频链接...'

  // 对于YouTube视频，提前显示提示
  if (isYoutube) {
    ElMessage({
      message: 'YouTube视频下载可能需要较长时间，请耐心等待...',
      type: 'info',
      duration: 8000
    })
    uploadStatus.value = '正在下载YouTube视频，请耐心等待...'
  }

  try {
    // 提交URL到后端
    const response = await uploadVideoUrl({
      url: formData.value.videoUrl,
      title: '未命名视频'
    })

    console.log('视频链接上传响应:', response)

    // 处理响应
    if (response) {
      uploadProgress.value = 100
      
      // 如果是YouTube视频，启动轮询检查下载状态
      if (isYoutube && response.id) {
        const videoId = response.id
        console.log(`YouTube视频上传成功，视频ID: ${videoId}，开始轮询状态`)
        startPollingVideoStatus(videoId, isYoutube)
      } else {
        // 非YouTube视频直接显示成功
        uploadStatus.value = 'success'
        
        if (isIcourse163) {
          ElMessage({
            message: '慕课视频链接提交成功，请注意：由于慕课网限制，需要手动下载视频并替换占位文件',
            type: 'success',
            duration: 5000
          })
        } else {
          ElMessage({
            message: '视频链接提交成功',
            type: 'success',
            duration: 3000
          })
        }
        formData.value.videoUrl = ''
        refreshList()
      }
    } else {
      throw new Error('服务器响应格式错误')
    }
  } catch (error) {
    console.error('提交错误:', error)
    uploadStatus.value = 'exception'
    
    // 对于YouTube视频，可能是超时但实际上已经开始下载，尝试刷新列表
    if (isYoutube) {
      ElMessage({
        message: 'YouTube视频下载可能仍在进行中，正在检查是否已添加到列表...',
        type: 'warning',
        duration: 5000
      })
      
      // 延迟刷新列表，因为视频可能已经添加但前端请求超时
      setTimeout(() => {
        refreshList()
      }, 2000)
    } else if (error.response && error.response.data && error.response.data.error) {
      ElMessage.error(`提交失败: ${error.response.data.error}`)
    } else if (isIcourse163) {
      ElMessage.warning('慕课视频提交失败，由于平台限制，请手动下载视频')
    } else {
      ElMessage.error('提交失败，请检查链接是否有效')
    }
  } finally {
    urlUploading.value = false
  }
}

// 轮询检查视频状态
const startPollingVideoStatus = (videoId, isYoutube = false) => {
  // 清除可能存在的旧定时器
  if (pollingTimers.value[videoId]) {
    clearInterval(pollingTimers.value[videoId])
  }
  
  let attempts = 0
  const maxAttempts = 120 // 最多轮询10分钟 (120次 * 5秒)
  
  console.log(`开始轮询视频${videoId}的状态, isYoutube: ${isYoutube}`)
  uploadStatus.value = isYoutube ? '正在下载YouTube视频，请耐心等待...' : '正在处理视频...'
  
  // 立即进行第一次检查
  checkVideoStatus(videoId, attempts, maxAttempts, isYoutube)
  
  // 创建新的轮询定时器
  pollingTimers.value[videoId] = setInterval(() => {
    attempts++
    checkVideoStatus(videoId, attempts, maxAttempts, isYoutube)
  }, 5000) // 每5秒检查一次
}

// 检查视频状态
const checkVideoStatus = async (videoId, attempts, maxAttempts, isYoutube) => {
  try {
    console.log(`正在检查视频${videoId}的状态，第${attempts+1}次尝试`)
    
    // 获取视频状态
    const { data: statusResponse } = await getVideoStatus(videoId)
    
    // 每次轮询都刷新视频列表，但在生成摘要时不刷新
    if (!isGeneratingSummary.value) {
      await refreshList()
      console.log(`第${attempts+1}次轮询，刷新视频列表`)
    } else {
      console.log(`第${attempts+1}次轮询，正在生成摘要，跳过刷新视频列表`)
    }
    
    if (statusResponse) {
      const status = statusResponse.status
      const progress = statusResponse.progress || 0
      const currentStep = statusResponse.current_step || ''
      
      console.log(`视频${videoId}状态: ${status}, 进度: ${progress}%, 步骤: ${currentStep}, 尝试次数: ${attempts+1}`)
      
      // 更新UI显示进度
      if (status === 'processing') {
        uploadStatus.value = 'processing'
        uploadProgress.value = Math.round(progress)
        uploadStepInfo.value = currentStep || '处理中...'
      }
      
      // 如果视频下载完成或失败，停止轮询
      if (status === 'uploaded') {
        if (pollingTimers.value[videoId]) {
          clearInterval(pollingTimers.value[videoId])
          delete pollingTimers.value[videoId]
        }
        
        console.log(`视频${videoId}下载完成，停止轮询`)
        uploadStatus.value = 'success'
        uploadProgress.value = 100
        uploadStepInfo.value = '下载完成'
        ElMessage({
          message: 'YouTube视频下载成功',
          type: 'success',
          duration: 3000
        })
      } else if (status === 'completed') {
        if (pollingTimers.value[videoId]) {
          clearInterval(pollingTimers.value[videoId])
          delete pollingTimers.value[videoId]
        }
        
        console.log(`视频${videoId}处理完成，停止轮询`)
        uploadStatus.value = 'success'
        uploadProgress.value = 100
        uploadStepInfo.value = '处理完成'
        
        ElMessage({
          message: '视频处理成功',
          type: 'success',
          duration: 3000
        })
      } else if (status === 'failed') {
        if (pollingTimers.value[videoId]) {
          clearInterval(pollingTimers.value[videoId])
          delete pollingTimers.value[videoId]
        }
        
        console.log(`视频${videoId}处理失败，停止轮询`)
        uploadStatus.value = 'exception'
        uploadProgress.value = 0
        uploadStepInfo.value = currentStep || '处理失败'
        ElMessage.error('视频处理失败')
      } else {
        console.log(`视频${videoId}仍在处理中，继续轮询`)
      }
      
      // 达到最大尝试次数，停止轮询
      if (attempts >= maxAttempts) {
        if (pollingTimers.value[videoId]) {
          clearInterval(pollingTimers.value[videoId])
          delete pollingTimers.value[videoId]
        }
        
        console.log(`视频${videoId}轮询达到最大次数，停止轮询`)
        ElMessage({
          message: '视频可能仍在处理中，请稍后刷新列表查看',
          type: 'info',
          duration: 5000
        })
      }
    }
  } catch (error) {
    console.error('轮询视频状态失败:', error)
    // 出错时不停止轮询，继续尝试
  }
}

// 处理视频
const handleProcess = async (video) => {
  try {
    // 创建对话框内容
    const dialogHtml = `
  <div class="process-dialog-wrapper">
    <!-- 标题部分 -->
    <div class="dialog-header">
      <div style="display: flex; align-items: center; margin-bottom: 15px;">
        <i class="el-icon-video-camera" style="font-size: 24px; margin-right: 12px;"></i>
        <span style="font-size: 20px; font-weight: 600;">智能视频分析设置</span>
      </div>
      <p style="margin: 0; font-size: 14px; opacity: 0.9;">选择最适合您视频内容的语言和模型，以获得最佳的智能分析效果</p>
    </div>
    
    <!-- 语言选择 -->
    <div class="content-card">
      <label style="display: block; margin-bottom: 12px; font-weight: 600; color: #303133; font-size: 16px;">
        <i class="el-icon-s-flag" style="margin-right: 8px; color: #409EFF;"></i>视频语言
      </label>
      <div class="language-selector" style="display: flex; width: 100%; margin-bottom: 10px;">
        <div class="language-option" data-value="English" style="flex: 1; text-align: center; padding: 15px; border: 2px solid #dcdfe6; border-radius: 8px 0 0 8px; cursor: pointer; background-color: #f5f7fa; color: #606266; transition: all 0.3s; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);">
          <div style="font-weight: 600; margin-bottom: 5px; font-size: 16px;">English</div>
          <div style="font-size: 13px; color: #909399;">英语</div>
        </div>
        <div class="language-option selected" data-value="Chinese" style="flex: 1; text-align: center; padding: 15px; border: 2px solid #409EFF; border-radius: 0 8px 8px 0; cursor: pointer; background-color: #ecf5ff; color: #409EFF; transition: all 0.3s; box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);">
          <div style="font-weight: 600; margin-bottom: 5px; font-size: 16px;">Chinese</div>
          <div style="font-size: 13px; color: #409EFF;">中文/多种语言</div>
        </div>
      </div>
      <input type="hidden" id="language-select" value="Chinese">
      <div class="info-tip">
        <i class="el-icon-info-circle" style="color: #409EFF;"></i>
        <span>选择与视频主要语言相符的选项，以提高转录准确度</span>
      </div>
    </div>

    <!-- 模型选择 -->
    <div class="content-card">
      <label style="display: block; margin-bottom: 12px; font-weight: 600; color: #303133; font-size: 16px;">
        <i class="el-icon-s-operation" style="margin-right: 8px; color: #409EFF;"></i>智能转录模型
      </label>
      <div id="model-options-container">
        <div class="model-size-slider" style="margin-bottom: 20px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-size: 13px; color: #67C23A; font-weight: 500;">更快速</span>
            <span style="font-size: 13px; color: #F56C6C; font-weight: 500;">更准确</span>
          </div>
          <div style="position: relative; height: 70px; background: linear-gradient(to right, #67C23A, #E6A23C, #F56C6C); border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);">
            <div id="model-options" style="display: flex; height: 100%; position: relative;">
              <!-- 模型选项将在这里动态生成 -->
            </div>
          </div>
        </div>
        <div id="model-description" style="background-color: #f8f9fb; border-radius: 8px; padding: 15px; margin-top: 10px; border-left: 4px solid #409EFF; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);">
          <div style="font-weight: 600; color: #303133; margin-bottom: 8px; font-size: 16px;">turbo 模型 (推荐)</div>
          <div style="font-size: 14px; color: #606266;">
            <p style="margin: 0 0 8px; display: flex; align-items: center;">
              <span style="display: inline-block; width: 20px; height: 20px; background-color: #67C23A; border-radius: 50%; margin-right: 8px;"></span>
              处理速度：<span style="color: #67C23A; font-weight: 500;">极快</span>
            </p>
            <p style="margin: 0 0 8px; display: flex; align-items: center;">
              <span style="display: inline-block; width: 20px; height: 20px; background-color: #409EFF; border-radius: 50%; margin-right: 8px;"></span>
              准确度：<span style="color: #409EFF; font-weight: 500;">良好</span>
            </p>
            <p style="margin: 0;">适用场景：<span style="color: #606266;">一般视频转录，对速度要求高</span></p>
          </div>
        </div>
        <input type="hidden" id="model-select" value="turbo">
        <div class="info-tip">
          <i class="el-icon-info-circle" style="color: #409EFF;"></i>
          <span>从左到右：模型越大，转录准确度越高，但处理时间也越长</span>
        </div>
      </div>
    </div>
  </div>
`;

    // 显示对话框
    ElMessageBox.confirm(dialogHtml, '智能视频分析', {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '开始智能分析',
      cancelButtonText: '取消',
      customClass: 'video-process-dialog',
      beforeClose: (action, instance, done) => {
        if (action === 'confirm') {
          instance.confirmButtonLoading = true;
          setTimeout(() => {
            instance.confirmButtonLoading = false;
            done();
          }, 300);
        } else {
          done();
        }
      },
      callback: async (action) => {
        if (action === 'confirm') {
          // 获取用户选择的语言和模型
          const languageSelect = document.getElementById('language-select');
          const modelSelect = document.getElementById('model-select');
          
          if (languageSelect && modelSelect) {
            const language = languageSelect.value;
            const model = modelSelect.value;
            
            // 调用处理视频API
            await processVideo(video.id, language, model);
            
            ElMessage({
              message: '视频正在处理，请稍候...',
              type: 'info',
              duration: 5000
            });
            
            // 启动轮询检查处理状态
            startPollingProcessStatus(video.id);
          }
        }
      }
    });

    // 添加事件监听器
    setTimeout(() => {
      // 语言选择事件监听
      const languageOptions = document.querySelectorAll('.language-option');
      const languageInput = document.getElementById('language-select');
      
      languageOptions.forEach(option => {
        option.addEventListener('click', () => {
          // 移除所有选中状态
          languageOptions.forEach(opt => {
            opt.classList.remove('selected');
            opt.style.backgroundColor = '#f5f7fa';
            opt.style.borderColor = '#dcdfe6';
            opt.style.color = '#606266';
            const subText = opt.querySelector('div:nth-child(2)');
            if (subText) subText.style.color = '#909399';
          });
          
          // 添加选中状态
          option.classList.add('selected');
          option.style.backgroundColor = '#ecf5ff';
          option.style.borderColor = '#409EFF';
          option.style.color = '#409EFF';
          const subText = option.querySelector('div:nth-child(2)');
          if (subText) subText.style.color = '#409EFF';
          
          // 更新隐藏输入值
          const value = option.getAttribute('data-value');
          languageInput.value = value;
          
          // 更新模型选项
          updateModelOptions(value);
        });
      });
      
      // 更新模型选项函数
      function updateModelOptions(language) {
        const modelOptionsContainer = document.getElementById('model-options');
        const modelDescriptionContainer = document.getElementById('model-description');
        const modelInput = document.getElementById('model-select');
        
        if (modelOptionsContainer && modelDescriptionContainer) {
          // 清空现有选项
          modelOptionsContainer.innerHTML = '';
          
          let models = [];
          
          // 根据语言添加相应的模型选项
          if (language === 'English') {
            // 英语语言选项
            models = [
              { 
                value: 'base.en', 
                text: 'base.en', 
                desc: '基础',
                color: '#85CF4E',
                speed: '很快',
                accuracy: '良好',
                useCase: '一般内容，速度和准确度平衡',
                speedColor: '#85CF4E',
                accuracyColor: '#E6A23C'
              },
              { 
                value: 'small.en', 
                text: 'small.en', 
                desc: '小型',
                selected: true,
                color: '#E6A23C',
                speed: '中等',
                accuracy: '很好',
                useCase: '复杂内容，对准确度要求较高',
                speedColor: '#E6A23C',
                accuracyColor: '#409EFF'
              },
              { 
                value: 'medium.en', 
                text: 'medium.en', 
                desc: '中型',
                color: '#F56C6C',
                speed: '较慢',
                accuracy: '极高',
                useCase: '专业内容，对准确度要求高',
                speedColor: '#F56C6C',
                accuracyColor: '#409EFF'
              }
            ];
          } else {
            // 其他语言选项
            models = [
              { 
                value: 'small', 
                text: 'small', 
                desc: '小型',
                color: '#9FD072',
                speed: '快',
                accuracy: '良好',
                useCase: '一般内容，速度和准确度平衡',
                speedColor: '#9FD072',
                accuracyColor: '#E6A23C'
              },
              { 
                value: 'medium', 
                text: 'medium', 
                desc: '中型',
                color: '#E6A23C',
                speed: '中等',
                accuracy: '很好',
                useCase: '复杂内容，对准确度要求较高',
                speedColor: '#E6A23C',
                accuracyColor: '#409EFF'
              },
              { 
                value: 'turbo', 
                text: 'turbo', 
                desc: '极速',
                selected: true,
                color: '#67C23A',
                speed: '极快',
                accuracy: '良好',
                useCase: '一般视频转录，对速度要求高',
                speedColor: '#67C23A',
                accuracyColor: '#409EFF'
              }
            ];
          }
          
          // 设置默认选中的模型
          let selectedModel = models.find(m => m.selected) || models[models.length - 1];
          modelInput.value = selectedModel.value;
          
          // 更新模型描述
          updateModelDescription(selectedModel);
          
          // 创建模型选项
          models.forEach((model, index) => {
            const width = 100 / models.length;
            
            const option = document.createElement('div');
            option.className = 'model-option';
            option.setAttribute('data-value', model.value);
            option.setAttribute('data-index', index);
            option.style.width = `${width}%`;
            option.style.height = '100%';
            option.style.display = 'flex';
            option.style.flexDirection = 'column';
            option.style.justifyContent = 'center';
            option.style.alignItems = 'center';
            option.style.cursor = 'pointer';
            option.style.position = 'relative';
            option.style.zIndex = '1';
            option.style.transition = 'all 0.3s';
            option.style.color = 'white';
            option.style.textShadow = '0 1px 2px rgba(0,0,0,0.2)';
            
            // 设置选中状态
            if (model.selected) {
              option.classList.add('selected');
              option.style.transform = 'scale(1.05)';
              option.style.zIndex = '2';
              option.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.2)';
            }
            
            option.innerHTML = `
              <div style="font-weight: 600; font-size: 14px;">${model.text}</div>
              <div style="font-size: 12px;">${model.desc}</div>
            `;
            
            // 添加点击事件
            option.addEventListener('click', () => {
              // 移除所有选中状态
              document.querySelectorAll('.model-option').forEach(opt => {
                opt.classList.remove('selected');
                opt.style.transform = '';
                opt.style.zIndex = '1';
                opt.style.boxShadow = '';
              });
              
              // 添加选中状态
              option.classList.add('selected');
              option.style.transform = 'scale(1.05)';
              option.style.zIndex = '2';
              option.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.2)';
              
              // 更新隐藏输入值
              modelInput.value = model.value;
              
              // 更新模型描述
              updateModelDescription(model);
            });
            
            modelOptionsContainer.appendChild(option);
          });
        }
      }
      
      // 更新模型描述函数
      function updateModelDescription(model) {
        const modelDescriptionContainer = document.getElementById('model-description');
        
        if (modelDescriptionContainer && model) {
          modelDescriptionContainer.innerHTML = `
            <div style="font-weight: 500; color: #303133; margin-bottom: 5px;">${model.text} 模型 ${model.selected ? '(推荐)' : ''}</div>
            <div style="font-size: 14px; color: #606266;">
              <p style="margin: 0 0 8px; display: flex; align-items: center;">
                <span style="display: inline-block; width: 20px; height: 20px; background-color: #67C23A; border-radius: 50%; margin-right: 8px;"></span>
                处理速度：<span style="color: #67C23A; font-weight: 500;">${model.speed}</span>
              </p>
              <p style="margin: 0 0 8px; display: flex; align-items: center;">
                <span style="display: inline-block; width: 20px; height: 20px; background-color: #409EFF; border-radius: 50%; margin-right: 8px;"></span>
                准确度：<span style="color: #409EFF; font-weight: 500;">${model.accuracy}</span>
              </p>
              <p style="margin: 0;">适用场景：<span style="color: #606266;">${model.useCase}</span></p>
            </div>
          `;
          
          // 更新边框颜色
          modelDescriptionContainer.style.borderLeftColor = model.color;
        }
      }
      
      // 初始化模型选项
      updateModelOptions(languageInput.value);
    }, 100);
  } catch (error) {
    console.error('处理视频失败:', error);
    ElMessage.error(error.response?.error || '处理视频失败');
  }
}

// 轮询检查视频处理状态
const startPollingProcessStatus = (videoId) => {
  // 清除可能存在的旧定时器
  if (processingTimers.value[videoId]) {
    clearInterval(processingTimers.value[videoId])
  }
  
  let attempts = 0
  const maxAttempts = 720 // 最多轮询60分钟 (360次 * 5秒)
  
  console.log(`开始轮询视频${videoId}的处理状态`)
  
  // 立即进行第一次检查
  checkProcessStatus(videoId, attempts, maxAttempts)
  
  // 创建新的轮询定时器
  processingTimers.value[videoId] = setInterval(() => {
    attempts++
    checkProcessStatus(videoId, attempts, maxAttempts)
  }, 5000) // 每5秒检查一次
}

// 检查视频处理状态
const checkProcessStatus = async (videoId, attempts, maxAttempts) => {
  try {
    console.log(`正在检查视频${videoId}的处理状态，第${attempts+1}次尝试`)
    
    // 获取视频状态
    const { data: statusResponse } = await getVideoStatus(videoId)
    
    // 保存处理状态到localStorage，用于页面刷新后恢复
    if (statusResponse && (statusResponse.status === 'processing' || statusResponse.status === 'pending')) {
      saveProcessingState(videoId, statusResponse.status)
    }
    
    // 每次轮询都刷新视频列表，但在生成摘要时不刷新
    if (!isGeneratingSummary.value) {
      await refreshList()
      console.log(`第${attempts+1}次轮询，刷新视频列表`)
    } else {
      console.log(`第${attempts+1}次轮询，正在生成摘要，跳过刷新视频列表`)
    }
    
    if (statusResponse) {
      const status = statusResponse.status
      const progress = statusResponse.progress || 0
      const currentStep = statusResponse.current_step || ''
      
      console.log(`视频${videoId}处理状态: ${status}, 进度: ${progress}%, 步骤: ${currentStep}, 尝试次数: ${attempts+1}`)
      
      // 更新UI显示进度
      if (status === 'processing') {
        uploadStatus.value = ''  
        uploadProgress.value = Math.round(progress)
        uploadStepInfo.value = currentStep || '处理中...'
      }
      
      // 如果视频处理完成或失败，停止轮询
      if (status === 'completed') {
        if (processingTimers.value[videoId]) {
          clearInterval(processingTimers.value[videoId])
          delete processingTimers.value[videoId]
        }
        
        // 移除处理状态
        removeProcessingState(videoId)
        
        console.log(`视频${videoId}处理完成，停止轮询`)
        uploadStatus.value = 'success'
        uploadProgress.value = 100
        uploadStepInfo.value = '处理完成'
        // 自动生成摘要
        try {
          console.log(`视频${videoId}处理完成，自动生成摘要`)
          
          // 设置正在生成摘要标志
          isGeneratingSummary.value = true
          
          // 在视频列表中找到对应的视频对象，设置自动生成摘要标志
          const videoObj = videoList.value.find(v => v.id === videoId)
          if (videoObj) {
            videoObj.autoGeneratingSummary = true
            console.log(`设置视频${videoId}的自动生成摘要标志`)
          }
          
          // 显示正在生成摘要的提示
          ElMessage({
            message: '正在自动生成视频摘要，请稍候...',
            type: 'info',
            duration: 3000,
            customClass: 'custom-message info-message',
            showClose: true,
            offset: 80
          })
          
          // 调用后端API生成摘要
          const response = await fetch(`/api/videos/${videoId}/generate-summary`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            }
          })
          
          if (response.ok) {
            console.log(`视频${videoId}摘要自动生成成功`)
            
            // 显示摘要生成成功的提示
            ElMessage({
              message: '视频摘要生成成功',
              type: 'success',
              duration: 3000,
              customClass: 'custom-message success-message',
              showClose: true,
              offset: 80
            })
            
            // 自动生成标签
            try {
              console.log(`视频${videoId}开始自动生成标签`)
              
              // 在视频列表中找到对应的视频对象，设置自动生成标签标志
              const videoObj = videoList.value.find(v => v.id === videoId)
              if (videoObj) {
                videoObj.autoGeneratingTags = true
                console.log(`设置视频${videoId}的自动生成标签标志`)
              }
              
              // 调用后端API生成标签
              const tagsResponse = await fetch(`/api/videos/${videoId}/generate-tags`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json'
                }
              })
              
              if (tagsResponse.ok) {
                const tagsData = await tagsResponse.json()
                console.log(`视频${videoId}标签自动生成成功:`, tagsData.tags)
                
                // 更新视频对象的标签
                const videoObj = videoList.value.find(v => v.id === videoId)
                if (videoObj && tagsData.tags) {
                  videoObj.tags = tagsData.tags
                  console.log(`更新视频${videoId}的标签:`, videoObj.tags)
                }
                
                // 显示标签生成成功的提示
                ElMessage({
                  message: '视频标签生成成功',
                  type: 'success',
                  duration: 3000,
                  customClass: 'custom-message success-message',
                  showClose: true,
                  offset: 80
                })
              } else {
                console.error('自动生成标签失败:', await tagsResponse.text())
              }
            } catch (tagError) {
              console.error('自动生成标签过程中出错:', tagError)
            } finally {
              // 清除自动生成标签标志
              const videoObj = videoList.value.find(v => v.id === videoId)
              if (videoObj) {
                videoObj.autoGeneratingTags = false
                console.log(`清除视频${videoId}的自动生成标签标志`)
              }
            }
          } else {
            console.error('自动生成摘要失败:', await response.text())
            
            // 显示摘要生成失败的提示
            ElMessage({
              message: '视频摘要生成失败',
              type: 'error',
              duration: 3000,
              customClass: 'custom-message error-message',
              showClose: true,
              offset: 80
            })
          }
        } catch (error) {
          console.error('自动生成摘要过程中出错:', error)
          
          // 显示摘要生成出错的提示
          ElMessage({
            message: `视频摘要生成出错: ${error.message}`,
            type: 'error',
            duration: 3000
          })
        } finally {
          // 重置生成摘要标志
          isGeneratingSummary.value = false
          
          // 在视频列表中找到对应的视频对象，清除自动生成摘要标志
          const videoObj = videoList.value.find(v => v.id === videoId)
          if (videoObj) {
            videoObj.autoGeneratingSummary = false
            console.log(`清除视频${videoId}的自动生成摘要标志`)
          }
          
          // 摘要生成完成后，手动刷新一次列表
          await refreshList()
          console.log('摘要生成完成，刷新视频列表')
        }
        ElMessage({
          message: '视频处理完成',
          type: 'success',
          duration: 3000
        })
      } else if (status === 'failed') {
        if (processingTimers.value[videoId]) {
          clearInterval(processingTimers.value[videoId])
          delete processingTimers.value[videoId]
        }
        
        // 移除处理状态
        removeProcessingState(videoId)
        
        console.log(`视频${videoId}处理失败，停止轮询`)
        uploadStatus.value = 'exception'
        uploadProgress.value = 0
        uploadStepInfo.value = currentStep || '处理失败'
        ElMessage.error('视频处理失败')
      } else if (status === 'processing') {
        console.log(`视频${videoId}仍在处理中，继续轮询`)
      } else {
        console.log(`视频${videoId}状态: ${status}，继续轮询`)
      }
      
      // 达到最大尝试次数，停止轮询
      if (attempts >= maxAttempts) {
        if (processingTimers.value[videoId]) {
          clearInterval(processingTimers.value[videoId])
          delete processingTimers.value[videoId]
        }
        
        console.log(`视频${videoId}处理轮询达到最大次数，停止轮询`)
        ElMessage({
          message: '视频可能仍在处理中，请稍后刷新列表查看',
          type: 'info',
          duration: 5000
        })
      }
    }
  } catch (error) {
    console.error('轮询视频处理状态失败:', error)
    // 出错时不停止轮询，继续尝试
  }
}

// 删除视频
const handleDelete = async (video) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除视频 "${video.filename}" 吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    loading.value = true
    await deleteVideo(video.id)
    ElMessage.success('删除成功')
    
    // 刷新列表
    await refreshList()
    // 如果当前页没有数据且不是第一页，则回到上一页
    if (paginatedVideoList.value.length === 0 && currentPage.value > 1) {
      currentPage.value--
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除视频失败:', error)
      ElMessage.error(error.response?.error || '删除视频失败')
    }
  }
}

// 批量删除视频
const handleBatchDelete = async () => {
  console.log('开始批量删除，选中的视频:', selectedVideos.value)
  if (selectedVideos.value.length === 0) {
    ElMessage.warning('请至少选择一个视频')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedVideos.value.length} 个视频吗？此操作不可恢复。`,
      '批量删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    loading.value = true
    const deletePromises = selectedVideos.value.map(video => deleteVideo(video.id))
    await Promise.all(deletePromises)
    
    ElMessage.success('批量删除成功')
    // 刷新列表
    await refreshList()
    // 如果当前页没有数据且不是第一页，则回到上一页
    if (paginatedVideoList.value.length === 0 && currentPage.value > 1) {
      currentPage.value--
    }
    // 退出批量删除模式
    exitBatchDeleteMode()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除视频失败:', error)
      ElMessage.error('批量删除视频失败')
    }
  } finally {
    loading.value = false
  }
}

// 进入批量删除模式
const enterBatchDeleteMode = () => {
  batchDeleteMode.value = true
  selectedVideos.value = []
}

// 退出批量删除模式
const exitBatchDeleteMode = () => {
  batchDeleteMode.value = false
  selectedVideos.value = []
  if (videoTable.value) {
    videoTable.value.clearSelection()
  }
}

// 清空表格选择
const clearSelection = () => {
  if (videoTable.value) {
    videoTable.value.clearSelection()
  }
  selectedVideos.value = []
}

// 获取状态类型
const getStatusType = (status) => {
  const statusMap = {
    uploaded: 'info',
    pending: 'warning',
    processing: 'primary',
    completed: 'success',
    failed: 'danger',
    downloading: 'warning'
  }
  return statusMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    uploaded: '已上传',
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '处理失败',
    downloading: '下载中'
  }
  return statusMap[status] || status
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 格式化视频时长
const formatDuration = (seconds) => {
  if (!seconds) return '未知'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

// 获取预览图URL
const getPreviewUrl = (video) => {
  if (!video.preview_filename) return ''
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'
  return `${baseURL}/api/videos/${video.id}/preview`
}

// 处理表格多选事件
const handleSelectionChange = (selection) => {
  selectedVideos.value = selection
  console.log('选中的视频:', selectedVideos.value)
}

// 播放视频
const handlePlay = (video) => {
  if (video.status !== 'completed') {
    ElMessage.warning('该视频尚未处理完成，无法播放')
    return
  }
  router.push(`/player/${video.id}`)
}

const router = useRouter()

onMounted(async () => {
  await refreshList()
  // 确保初始页码为1
  nextTick(() => {
    currentPage.value = 1
  })
})

onUnmounted(() => {
  Object.values(pollingTimers.value).forEach(timer => {
    clearInterval(timer)
  })
  Object.values(processingTimers.value).forEach(timer => {
    clearInterval(timer)
  })
})

// 获取视频列表
const refreshList = async () => {
  try {
    loading.value = true
    const { data } = await getVideoList()
    if (data && data.videos) {
      // 按照上传时间排序，最早上传的排在最前面
      videoList.value = data.videos.sort((a, b) => {
        // 如果有创建时间字段，按照创建时间排序
        if (a.created_at && b.created_at) {
          return new Date(a.created_at) - new Date(b.created_at)
        }
        // 如果没有创建时间字段，则按照ID排序（假设ID是按照创建顺序递增的）
        return a.id - b.id
      })
      
      // 清空选中的视频
      selectedVideos.value = []
      
      // 重置到第一页
      currentPage.value = 1
    } else {
      videoList.value = []
    }
  } catch (error) {
    console.error('获取视频列表失败:', error)
    ElMessage.error('获取视频列表失败')
    videoList.value = []
  } finally {
    loading.value = false
  }
}

// 获取摘要占位符文本
const getSummaryPlaceholder = (status) => {
  if (status === 'processing') {
    return '视频正在处理中，完成后可生成摘要'
  } else if (status === 'uploaded') {
    return '视频已上传，等待处理'
  } else if (status === 'failed') {
    return '视频处理失败，无法生成摘要'
  } else {
    return '当前状态不支持生成摘要'
  }
}

// 根据标签索引返回不同的标签类型
const getTagType = (index) => {
  const types = ['primary', 'success', 'warning', 'info', 'danger']
  return types[index % types.length]
}

// 生成视频摘要
const generateSummary = async (video) => {
  try {
    // 设置生成中状态
    video.generatingSummary = true
    // 设置全局生成摘要标志
    isGeneratingSummary.value = true
    
    // 显示正在生成摘要的提示
    ElMessage({
      message: '正在生成视频摘要，请稍候...',
      type: 'info',
      duration: 3000
    })
    
    // 调用后端API生成摘要
    const response = await fetch(`/api/videos/${video.id}/generate-summary`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (!response.ok) {
      throw new Error('生成摘要失败')
    }
    
    const data = await response.json()
    
    // 过滤掉思考过程
    let summary = data.summary
    if (summary) {
      // 使用正则表达式移除<think>...</think>标签及其内容
      summary = summary.replace(/<think>[\s\S]*?<\/think>/g, '').trim()
      // 清理可能出现的多余空格
      summary = summary.replace(/\s+/g, ' ').trim()
    }
    
    // 更新视频对象的摘要
    video.summary = summary
    
    // 显示摘要生成成功的提示
    ElMessage({
      message: '视频摘要生成成功',
      type: 'success',
      duration: 3000
    })
  } catch (error) {
    console.error('生成摘要错误:', error)
    
    // 显示摘要生成失败的提示
    ElMessage({
      message: '视频摘要生成失败',
      type: 'error',
      duration: 3000
    })
  } finally {
    // 清除生成中状态
    video.generatingSummary = false
    // 清除全局生成摘要标志
    isGeneratingSummary.value = false
    
    // 手动刷新一次列表，确保显示最新状态
    await refreshList()
    console.log('手动生成摘要完成，刷新视频列表')
  }
}
</script>

<style scoped>
/* 基本变量定义 */
:root {
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
  --primary-gradient: linear-gradient(135deg, #667eea, #764ba2);
}

.upload-container {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  color: var(--text-primary);
  overflow-x: hidden;
  padding-bottom: 50px;
}

/* 英雄区域样式 */
.video-hero-section {
  position: relative;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7eb 100%);
  color: #333;
  padding: 2.5rem 0;
  margin-bottom: 2rem;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  height: 180px;
}

.hero-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #3CAEA3, #4F46E5);
  opacity: 0.85;
  z-index: 1;
}

.hero-container {
  position: relative;
  z-index: 2;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  height: 100%;
}

.hero-content-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
  height: 100%;
}

.hero-text {
  max-width: 800px;
}

.main-title {
  font-size: 2.2rem;
  margin-bottom: 1rem;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  animation: fadeInUp 0.6s ease-out;
}

.subtitle {
  font-size: 1.1rem;
  font-weight: 400;
  margin-bottom: 0;
  opacity: 0.9;
  line-height: 1.6;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  animation: fadeInUp 0.8s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 美化上传区域 */
:deep(.el-upload-dragger) {
  background: linear-gradient(to bottom, #f9f9f9, #f0f0f0);
  border: 2px dashed #3CAEA3;
  border-radius: 12px;
  transition: all 0.4s;
  padding: 40px 20px;
  position: relative;
  overflow: hidden;
  box-shadow: inset 0 0 15px rgba(60, 174, 163, 0.1);
}

:deep(.el-upload-dragger)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    radial-gradient(circle at 20px 20px, rgba(60, 174, 163, 0.05) 0, rgba(60, 174, 163, 0.05) 2px, transparent 2px),
    radial-gradient(circle at 40px 40px, rgba(79, 70, 229, 0.05) 0, rgba(79, 70, 229, 0.05) 2px, transparent 2px);
  background-size: 60px 60px;
  z-index: 0;
}

:deep(.el-upload-dragger):hover {
  border-color: #4F46E5;
  transform: scale(1.01);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1), inset 0 0 20px rgba(79, 70, 229, 0.15);
}

:deep(.el-icon--upload) {
  font-size: 36px;
  color: #3CAEA3;
  margin-bottom: 12px;
  position: relative;
  z-index: 1;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

:deep(.el-upload-dragger:hover .el-icon--upload) {
  color: #4F46E5;
  transform: scale(1.1);
}

:deep(.el-upload__text) {
  color: var(--text-primary);
  font-size: 16px;
  margin-top: 15px;
  position: relative;
  z-index: 1;
  font-weight: 500;
}

:deep(.el-upload__text em) {
  color: #4F46E5;
  font-style: normal;
  text-decoration: underline;
  font-weight: 600;
}

/* 视频链接输入框样式 */
.video-url-input:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #3CAEA3;
  transition: all 0.3s;
  background-color: rgba(60, 174, 163, 0.05);
  background-image: 
    linear-gradient(45deg, rgba(60, 174, 163, 0.03) 25%, transparent 25%, transparent 50%, 
    rgba(60, 174, 163, 0.03) 50%, rgba(60, 174, 163, 0.03) 75%, transparent 75%, transparent);
  background-size: 20px 20px;
  border-radius: 8px;
}

.video-url-input:deep(.el-input__wrapper):hover {
  box-shadow: 0 0 0 1px #4F46E5;
}

.video-url-input:deep(.el-input__wrapper):focus-within {
  box-shadow: 0 0 0 2px rgba(60, 174, 163, 0.3);
  background-color: white;
  background-image: none;
}

/* 确保按钮在输入框中正确显示 */
.video-url-input:deep(.el-input-group__append) {
  padding: 0;
  background-color: transparent;
  border-color: #3CAEA3;
}

.video-url-input:deep(.el-input-group__append .el-button) {
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
  margin: 0;
}

/* 修改提交链接按钮样式 */
.video-url-input:deep(.el-input-group__append .el-button.el-button--primary) {
  background-color: #0d86e2 !important;  /* 靛蓝色背景 */
  border-color: #3b77ef !important;      /* 靛蓝色边框 */
  color: white !important;               /* 白色文字 */
  font-weight: 500;
  padding: 0 20px;
  border-radius: 8px !important;         /* 加入圆角 */
}


.video-url-input:deep(.el-input-group__append .el-button.el-button--primary:hover) {
  background-color: #4338CA !important;  /* 悬停时颜色加深 */
  border-color: #4338CA !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;  /* 添加阴影效果 */
  transform: translateY(-2px);  /* 轻微上移效果 */
}

.submit-url-button {
  font-weight: 500;
  padding: 0 20px;
  background-color: #4F46E5;  /* 靛蓝色背景 */
  border-color: #4F46E5;      /* 靛蓝色边框 */
  color: white;               /* 白色文字 */
}

.submit-url-button:hover {
  background-color: #4338CA;  /* 悬停时颜色加深 */
  border-color: #4338CA;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);  /* 添加阴影效果 */
  transform: translateY(-2px);  /* 轻微上移效果 */
}

/* 分页容器样式 */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 10px 0;
}

.custom-pagination {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pagination-btn {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  background-color: #fff;
  color: #606266;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.pagination-btn:hover:not(:disabled) {
  color: var(--primary-color);
  border-color: var(--primary-color);
}

.pagination-btn:disabled {
  cursor: not-allowed;
  color: #c0c4cc;
  background-color: #f4f4f5;
}

.page-info {
  min-width: 50px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #606266;
  background-color: #f4f4f5;
  border-radius: 4px;
  padding: 0 10px;
}

/* 英雄区域样式 */
.video-hero-section {
  position: relative;
  height: 200px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7eb 100%);
  margin-bottom: 30px;
  border-radius: 12px;
  overflow: hidden;
  max-width: 1200px;
  margin-left: auto;
  margin-right: auto;
}

.hero-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.8), rgba(79, 70, 229, 0.8));
}

.hero-container {
  position: relative;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  padding: 0 20px;
}

.hero-content-wrapper {
  text-align: center;
  color: white;
}

.main-title {
  font-size: 2.5rem;
  margin-bottom: 10px;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.subtitle {
  font-size: 1.2rem;
  font-weight: 400;
  margin-bottom: 15px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.hero-description {
  font-size: 1rem;
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.5;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  background-color: rgba(0, 0, 0, 0.2);
  padding: 8px 15px;
  border-radius: 4px;
  display: inline-block;
}

/* 页脚样式 */
.page-footer {
  margin-top: 40px;
  background-color: #333;
  padding: 15px 0;
  width: 100%;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  text-align: center;
}

.page-footer p {
  margin: 0;
  color: white;
  font-size: 14px;
}

.hero-description-container {
  margin-top: 15px;
}

.hero-description {
  font-size: 1rem;
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.5;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  color: rgba(255, 255, 255, 0.9);
  background-color: rgba(255, 255, 255, 0.15);
  padding: 8px 15px;
  border-radius: 20px;
  display: inline-block;
  backdrop-filter: blur(5px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

/* 视频链接输入框样式 */
.video-url-input:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #3CAEA3;
  transition: all 0.3s;
  background-color: rgba(60, 174, 163, 0.05);
  background-image: 
    linear-gradient(45deg, rgba(60, 174, 163, 0.03) 25%, transparent 25%, transparent 50%, 
    rgba(60, 174, 163, 0.03) 50%, rgba(60, 174, 163, 0.03) 75%, transparent 75%, transparent);
  background-size: 20px 20px;
  border-radius: 8px;
}

.video-url-input:deep(.el-input__wrapper):hover {
  box-shadow: 0 0 0 1px #4F46E5;
}

.video-url-input:deep(.el-input__wrapper):focus-within {
  box-shadow: 0 0 0 2px rgba(60, 174, 163, 0.3);
  background-color: white;
  background-image: none;
}

.submit-url-button {
  font-weight: 500;
  padding: 0 20px;
  background-color: #4F46E5;
  border-color: #4F46E5;
  color: white;
}

.submit-url-button:hover {
  background-color: #4338CA;
  border-color: #4338CA;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
  transform: translateY(-2px);
}

/* 卡片样式 */
.upload-card, .video-list-card {
  margin-bottom: 20px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  max-width: 1200px;
  margin-left: auto;
  margin-right: auto;
  background-color: #fff;
  position: relative;
  padding: 0;
  border: 3px solid transparent;
  background-image: linear-gradient(white, white), linear-gradient(135deg, #3CAEA3, #4F46E5);
  background-origin: border-box;
  background-clip: content-box, border-box;
}

/* 移除悬停特效 */
/* .upload-card:hover, .video-list-card:hover {
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
  transform: translateY(-10px);
} */

/* 美化表格 */
:deep(.el-table) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

:deep(.el-table__header) {
  background: linear-gradient(to right, #f0f2f5, #e4e7ed);
}

:deep(.el-table__header-wrapper th) {
  background-color: transparent;
  font-weight: 600;
  color: var(--indigo-600);
  padding: 12px 0;
  text-align: center !important;
}

:deep(.el-table__row) {
  transition: all 0.3s;
}

:deep(.el-table__row:hover) {
  background-color: var(--indigo-100);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
}

:deep(.el-button) {
  transition: all 0.3s;
}

:deep(.el-button:hover) {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-3px);
}

:deep(.el-tag) {
  border-radius: 6px;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  padding: 4px 8px;
  letter-spacing: 0.5px;
}

:deep(.el-image) {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.4s;
  border: 2px solid transparent;
}

:deep(.el-image:hover) {
  transform: scale(1.08);
  border-color: var(--indigo-600);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--indigo-600);
  font-size: 15px;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--indigo-600) inset, 0 4px 12px rgba(0, 0, 0, 0.1);
}

:deep(.el-progress) {
  margin: 10px 0;
}

:deep(.el-progress__text) {
  font-weight: 600;
  color: var(--indigo-600);
}

:deep(.el-progress-bar__outer) {
  border-radius: 10px;
  background-color: #e6e6e6;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
}

:deep(.el-progress-bar__inner) {
  border-radius: 10px;
  background: #67C23A; /* 修改为Element Plus的成功绿色 */
  box-shadow: 0 2px 6px rgba(103, 194, 58, 0.3); /* 调整阴影颜色匹配绿色 */
  transition: width 0.5s cubic-bezier(0.22, 0.61, 0.36, 1);
}

/* 视频信息样式 */
.video-info-box {
  background: var(--indigo-100);
  border-radius: 8px;
  padding: 8px 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  border-left: 3px solid var(--indigo-600);
}

.video-info-box div {
  margin: 5px 0;
  font-size: 13px;
  color: var(--text-primary);
}

/* 空状态提示区域样式 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 10px 20px;
  text-align: center;
  background: linear-gradient(135deg, #fafaf8, #e9ecef);
  border-radius: 12px;
  box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.03);
  border: 1px dashed #ced4da;
  margin: 10px 0;
}

.empty-icon {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  box-shadow: 0 8px 15px rgba(99, 102, 241, 0.3);
}

.empty-icon .el-icon {
  font-size: 32px;
  color: white;
}

.empty-state p {
  font-size: 20px;
  font-weight: 600;
  color: #4338ca;
  margin: 0 0 10px 0;
}

.empty-tip {
  font-size: 16px;
  color: #6b7280;
  max-width: 80%;
  line-height: 1.6;
}

/* 视频标签样式 */
.video-tags {
  display: flex;
  flex-direction: column; 
  gap: 3px; /* 调整间距 */
}

.video-tag {
  margin-bottom: 5px;
}

/* 操作按钮样式 */
.action-buttons {
  display: flex;
  justify-content: space-between; /* 改为两端对齐 */
  align-items: center;
  width: 100%; /* 确保占满整个单元格宽度 */
  padding: 0 20px; /* 添加左右内边距，防止图标贴边 */
}

.action-icon {
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 4px;
  background-color:  rgb(167, 212, 220); /* 使用主色调 */
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  border: none;
  box-shadow: 0 2px 6px rgba(60, 174, 163, 0.3);
}

.action-icon:hover:not(.disabled) {
  color: var(--primary-color);
  border-color: var(--primary-color);
  transform: scale(1.05);
}

.action-icon.disabled {
  cursor: not-allowed;
  color: #c0c4cc;
  background-color: #f4f4f5;
  opacity: 0.7;
}

/* 卡片标题样式 */
.title-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.title-icon .el-icon {
  font-size: 18px;
  color: #ffffff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  position: relative;
  z-index: 1;
  background-color: #f8f9fa;
  border-bottom: 1px solid #ebeef5;
}

.card-header h2, .card-header h3 {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 600;
  color: #4338ca;
  position: relative;
  padding-bottom: 5px;
}

.card-header h2::after, .card-header h3::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 40px;
  height: 3px;
  background: linear-gradient(to right, #6366f1, #a5b4fc);
  border-radius: 3px;
}
</style>
