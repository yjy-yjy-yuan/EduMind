<template>
  <div class="upload-container">
    <div class="page-title">
      <h1>视频管理中心</h1>
      <p class="subtitle">上传、管理和处理您的教育视频</p>
    </div>
    
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <h2>视频上传</h2>
        </div>
      </template>
      
      <el-form ref="uploadForm" :model="formData" label-width="120px">
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
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                拖拽文件到此处或 <em>点击上传</em>
              </div>
            </el-upload>
            
            <div class="upload-format-tip">
              <el-icon><info-filled /></el-icon>
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
            placeholder="请输入B站、YouTube或中国大学慕课视频链接"
          >
            <template #append>
              <el-button @click="handleUrlUpload" :loading="urlUploading">
                {{ urlUploading ? '提交中...' : '提交链接' }}
              </el-button>
            </template>
          </el-input>
          <div class="el-upload__tip">
            支持B站、YouTube和中国大学慕课视频链接
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 视频列表 -->
    <el-card class="video-list-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <h3>已上传视频</h3>
          <div>
            <el-button 
              type="danger" 
              :disabled="selectedVideos.length === 0"
              @click="handleBatchDelete"
            >
              批量删除
            </el-button>
            <el-button @click="refreshList" :icon="Refresh" circle />
          </div>
        </div>
      </template>
      
      <el-table 
        ref="videoTable"
        :data="videoList" 
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="filename" label="文件名" />
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="预览图" width="120">
          <template #default="scope">
            <el-image 
              v-if="scope.row.preview_filename"
              style="width: 100px; height: 60px"
              :src="getPreviewUrl(scope.row)"
              :preview-src-list="[getPreviewUrl(scope.row)]"
              fit="cover"
            />
            <span v-else>无预览图</span>
          </template>
        </el-table-column>
        <el-table-column label="视频信息">
          <template #default="scope">
            <div v-if="scope.row.duration" class="video-info-box">
              <div><i class="el-icon-time"></i> 时长: {{ formatDuration(scope.row.duration) }}</div>
              <div><i class="el-icon-picture"></i> 分辨率: {{ scope.row.width }}x{{ scope.row.height }}</div>
              <div><i class="el-icon-video-play"></i> 帧率: {{ scope.row.fps ? scope.row.fps.toFixed(2) : '未知' }} FPS</div>
            </div>
            <span v-else>暂无信息</span>
          </template>
        </el-table-column>
        <el-table-column prop="upload_time" label="上传时间">
          <template #default="scope">
            {{ formatDate(scope.row.upload_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <div class="action-buttons">
              <el-button 
                :icon="VideoPlay"
                circle
                @click="handlePlay(scope.row)"
                :disabled="!['completed'].includes(scope.row.status)"
                title="播放视频"
                class="action-button play-button"
              />
              <el-button 
                :icon="VideoCamera"
                circle
                @click="handleProcess(scope.row)"
                :disabled="!['uploaded', 'pending'].includes(scope.row.status) || scope.row.status === 'downloading'"
                title="处理视频"
                class="action-button process-button"
              />
              <el-button 
                type="danger" 
                :icon="Delete"
                circle
                @click="handleDelete(scope.row)"
                title="删除视频"
                class="action-button delete-button"
              />
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 空状态提示 -->
      <div v-if="videoList.length === 0 && !loading" class="empty-state">
        <div class="empty-icon">
          <el-icon><video-camera /></el-icon>
        </div>
        <p>暂无上传视频</p>
        <p class="empty-tip">您可以通过上方表单上传视频文件或提交视频链接</p>
      </div>
    </el-card>

    <!-- 上传指南卡片 -->
    <el-row :gutter="20" class="guide-row">
      <el-col :span="8">
        <div class="guide-card" style="animation: fadeInLeft 0.5s ease-out;">
          <div class="guide-icon">
            <el-icon><upload-filled /></el-icon>
          </div>
          <h3>上传指南</h3>
          <ul>
            <li>支持多种视频格式</li>
            <li>单个文件大小不超过2GB</li>
            <li>视频时长建议在5-120分钟</li>
            <li>高清视频效果更佳</li>
          </ul>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="guide-card" style="animation: fadeInLeft 0.5s ease-out 0.2s; animation-fill-mode: both;">
          <div class="guide-icon">
            <el-icon><video-camera /></el-icon>
          </div>
          <h3>处理流程</h3>
          <div class="process-steps">
            <div class="process-step">
              <div class="step-number">1</div>
              <div class="step-text">上传视频</div>
            </div>
            <div class="process-arrow">→</div>
            <div class="process-step">
              <div class="step-number">2</div>
              <div class="step-text">AI处理</div>
            </div>
            <div class="process-arrow">→</div>
            <div class="process-step">
              <div class="step-number">3</div>
              <div class="step-text">分析完成</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="guide-card" style="animation: fadeInLeft 0.5s ease-out 0.4s; animation-fill-mode: both;">
          <div class="guide-icon">
            <el-icon><connection /></el-icon>
          </div>
          <h3>视频分析</h3>
          <p>AI-EdVision 将自动分析您的视频内容，提取关键信息，生成字幕和摘要，并支持智能问答功能。</p>
          <div class="feature-tags">
            <span class="feature-tag">自动字幕</span>
            <span class="feature-tag">内容摘要</span>
            <span class="feature-tag">智能问答</span>
            <span class="feature-tag">知识图谱</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 底部信息卡片 -->
    <div class="bottom-info-section">
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="info-card" style="animation: slideUp 0.5s ease-out;">
            <h3><el-icon><info-filled /></el-icon> 使用提示</h3>
            <div class="info-content">
              <p>1. 上传完成后，需要点击"处理视频"按钮进行AI分析</p>
              <p>2. 处理完成后，可以点击"播放视频"按钮查看视频和AI分析结果</p>
              <p>3. 视频处理时间取决于视频长度，请耐心等待</p>
              <p>4. 如有任何问题，请联系系统管理员获取帮助</p>
            </div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="info-card stats-card" style="animation: slideUp 0.5s ease-out 0.2s; animation-fill-mode: both;">
            <h3><el-icon><data-analysis /></el-icon> 系统状态</h3>
            <div class="stats-content">
              <div class="stat-item">
                <div class="stat-label">处理引擎</div>
                <div class="stat-value"><span class="status-dot active"></span> 运行中</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">AI模型</div>
                <div class="stat-value"><span class="status-dot active"></span> 已加载</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">存储空间</div>
                <div class="stat-value">
                  <el-progress :percentage="65" :show-text="false" style="width: 100px;"></el-progress>
                  <span>65%</span>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-label">系统版本</div>
                <div class="stat-value">v2.5.3</div>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
    
    <!-- 页脚 -->
    <div class="page-footer">
      <p>&copy; 2025 AI-EdVision 智能教育视频分析系统</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { 
  UploadFilled, 
  VideoCamera,
  VideoPlay,
  Delete, 
  Refresh,
  InfoFilled,
  DataAnalysis,
  Connection 
} from '@element-plus/icons-vue'
import { 
  uploadLocalVideo, 
  uploadVideoUrl, 
  getVideoList, 
  processVideo,
  getVideoPreview,
  deleteVideo,
  getVideoStatus,
  getVideo
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

const pollingTimers = ref({})
const processingTimers = ref({})

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
    const response = await getVideoStatus(videoId)
    const status = response.status
    const progress = response.progress || 0
    const currentStep = response.current_step || ''
    
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
      
      // 清空输入框并刷新列表
      formData.value.videoUrl = ''
      refreshList()
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
      
      // 刷新列表
      refreshList()
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
      console.log(`视频${videoId}仍在处理中，状态: ${status}，继续轮询`)
    }
    
    // 达到最大尝试次数，停止轮询
    if (attempts >= maxAttempts) {
      if (pollingTimers.value[videoId]) {
        clearInterval(pollingTimers.value[videoId])
        delete pollingTimers.value[videoId]
      }
      
      console.log(`视频${videoId}轮询达到最大次数，停止轮询`)
      // 不显示错误，因为视频可能仍在处理中
      ElMessage({
        message: '视频可能仍在处理中，请稍后刷新列表查看',
        type: 'info',
        duration: 5000
      })
    }
  } catch (error) {
    console.error('轮询视频状态失败:', error)
    // 出错时不停止轮询，继续尝试
  }
}

// 获取视频列表
const refreshList = async () => {
  try {
    loading.value = true
    const { data } = await getVideoList()
    if (data && data.videos) {
      videoList.value = data.videos
      // 清空选中的视频
      selectedVideos.value = []
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
              处理速度：<span style="color: #67C23A; font-weight: 600; margin-left: 5px;">极快</span>
            </p>
            <p style="margin: 0 0 8px; display: flex; align-items: center;">
              <span style="display: inline-block; width: 20px; height: 20px; background-color: #409EFF; border-radius: 50%; margin-right: 8px;"></span>
              准确度：<span style="color: #409EFF; font-weight: 600; margin-left: 5px;">良好</span>
            </p>
            <p style="margin: 0;">适用场景：<span style="color: #606266;">一般视频转录，对速度要求高</span></p>
          </div>
        </div>
      </div>
      <input type="hidden" id="model-select" value="turbo">
      <div class="info-tip">
        <i class="el-icon-info-circle" style="color: #409EFF;"></i>
        <span>从左到右：模型越大，转录准确度越高，但处理时间也越长</span>
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
              option.style.boxShadow = '0 0 10px rgba(0,0,0,0.2)';
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
              option.style.boxShadow = '0 0 10px rgba(0,0,0,0.2)';
              
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
            <div style="font-size: 13px; color: #606266;">
              <p style="margin: 0 0 5px;">• 处理速度：<span style="color: ${model.speedColor}; font-weight: 500;">${model.speed}</span></p>
              <p style="margin: 0 0 5px;">• 准确度：<span style="color: ${model.accuracyColor}; font-weight: 500;">${model.accuracy}</span></p>
              <p style="margin: 0;">• 适用场景：<span style="color: #606266;">${model.useCase}</span></p>
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
    if (statusResponse) {
      const status = statusResponse.status
      const progress = statusResponse.progress || 0
      const currentStep = statusResponse.current_step || ''
      
      console.log(`视频${videoId}处理状态: ${status}, 进度: ${progress}%, 步骤: ${currentStep}, 尝试次数: ${attempts+1}`)
      
      // 更新UI显示进度
      if (status === 'processing') {
        uploadStatus.value = ''  // 修改这里，使用空字符串代替'processing'
        uploadProgress.value = Math.round(progress)
        uploadStepInfo.value = currentStep || '处理中...'
        
        // 添加这里：当进度首次达到60%时刷新列表
        if (progress >= 60 && !window.hasRefreshedAt60) {
          window.hasRefreshedAt60 = true
          console.log('进度达到60%，刷新视频列表')
          refreshList()
        }
      }
      
      // 如果视频处理完成或失败，停止轮询
      if (status === 'completed') {
        if (processingTimers.value[videoId]) {
          clearInterval(processingTimers.value[videoId])
          delete processingTimers.value[videoId]
        }
        
        console.log(`视频${videoId}处理完成，停止轮询`)
        uploadStatus.value = 'success'
        uploadProgress.value = 100
        uploadStepInfo.value = '处理完成'
        ElMessage({
          message: '视频处理完成',
          type: 'success',
          duration: 3000
        })
        
        // 刷新列表
        refreshList()
      } else if (status === 'failed') {
        if (processingTimers.value[videoId]) {
          clearInterval(processingTimers.value[videoId])
          delete processingTimers.value[videoId]
        }
        
        console.log(`视频${videoId}处理失败，停止轮询`)
        uploadStatus.value = 'exception'
        uploadProgress.value = 0
        uploadStepInfo.value = currentStep || '处理失败'
        ElMessage.error('视频处理失败')
        
        // 刷新列表
        refreshList()
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
        
        // 最后一次刷新列表
        refreshList()
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
      '确定要删除这个视频吗？此操作不可恢复。',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deleteVideo(video.id)
    ElMessage.success('视频删除任务已启动')
    refreshList()
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
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const videoIds = selectedVideos.value.map(video => video.id)
    console.log('要删除的视频ID:', videoIds)
    
    // 逐个删除视频
    for (const id of videoIds) {
      await deleteVideo(id)
    }
    
    ElMessage.success(`成功删除 ${videoIds.length} 个视频`)
    
    // 清空选中的视频
    clearSelection()
    
    // 刷新列表
    refreshList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除视频失败:', error)
      ElMessage.error(error.response?.error || '批量删除视频失败')
    }
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
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
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

onMounted(() => {
  refreshList()
})

onUnmounted(() => {
  Object.values(pollingTimers.value).forEach(timer => {
    clearInterval(timer)
  })
  Object.values(processingTimers.value).forEach(timer => {
    clearInterval(timer)
  })
})
</script>

<style scoped>
.upload-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
.upload-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
  position: relative;
  overflow: hidden;
}

/* 添加背景点缀效果 */
.upload-container::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect width="100" height="100" fill="none"/><circle cx="10" cy="10" r="1" fill="rgba(30,60,114,0.05)"/></svg>');
  pointer-events: none;
  z-index: 0;
}

.page-title {
  text-align: center;
  margin-bottom: 30px;
  position: relative;
  z-index: 1;
}

.page-title h1 {
  font-size: 2.2rem;
  color: #1e3c72;
  margin-bottom: 10px;
  font-weight: 600;
  text-shadow: 0 2px 4px rgba(0,0,0,0.1);
  background: linear-gradient(135deg, #1e3c72, #2a5298);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: fadeIn 1s ease-out;
}

.subtitle {
  font-size: 1.1rem;
  color: #606266;
  opacity: 0.8;
  animation: slideUp 1s ease-out;
}


.upload-card, .video-list-card {
  margin-bottom: 30px;
  border-radius: 12px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
  transition: box-shadow 0.3s;
  overflow: hidden;
  position: relative;
  z-index: 1;
  backdrop-filter: blur(5px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  animation: fadeIn 0.8s ease-out;
}

.upload-card:hover, .video-list-card:hover {
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #1e3c72, #2a5298);
  color: #fff;
  padding: 15px 20px;
  position: relative;
  overflow: hidden;
}

/* 添加卡片标题背景效果 */
.card-header::before {
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

.card-header h2, .card-header h3 {
  margin: 0;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  position: relative;
}

.progress-container {
  margin-top: 15px;
  padding: 20px;
  border-radius: 10px;
  background-color: #f8f9fa;
  border: 1px solid #ebeef5;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  animation: pulse 2s infinite;
}

.video-actions {
  display: flex;
  justify-content: flex-end;
}

.video-actions .el-button {
  margin-left: 10px;
}

.video-process-dialog .el-message-box__content {
  max-height: 500px;
  overflow-y: auto;
  padding: 0 !important;
  background: #f5f7fa;
}

.language-option {
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.language-option:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

.model-option.selected {
  transform: scale(1.05);
  z-index: 2;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.25);
  border: 2px solid #409EFF;
}

.processing-step {
  font-size: 14px;
  color: #409EFF;
  font-weight: 500;
  margin-top: 12px;
  padding: 12px 15px;
  background-color: #ecf5ff;
  border-radius: 8px;
  border-left: 4px solid #409EFF;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08);
  animation: fadeInLeft 0.5s ease-out;
}

/* 美化上传区域 */
:deep(.el-upload-dragger) {
  background: linear-gradient(to bottom, #f9f9f9, #f0f0f0);
  border: 2px dashed #c0c4cc;
  border-radius: 12px;
  transition: all 0.4s;
  padding: 30px 20px;
  position: relative;
  overflow: hidden;
}

:deep(.el-upload-dragger)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle, rgba(255,255,255,0.8) 0%, rgba(255,255,255,0) 70%);
  z-index: 0;
}

:deep(.el-upload-dragger:hover) {
  border-color: #409EFF;
  background: linear-gradient(to bottom, #f0f7ff, #e6f1fc);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

:deep(.el-icon--upload) {
  font-size: 48px;
  color: #409EFF;
  margin-bottom: 15px;
  filter: drop-shadow(0 2px 5px rgba(0, 0, 0, 0.1));
  animation: bounce 2s infinite;
}

:deep(.el-upload__text) {
  color: #606266;
  font-size: 16px;
  margin-top: 15px;
  position: relative;
  z-index: 1;
}

:deep(.el-upload__text em) {
  color: #409EFF;
  font-style: normal;
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 3px;
}

:deep(.el-upload__tip) {
  color: #909399;
  font-size: 13px;
  margin-top: 10px;
  padding: 8px 12px;
  background-color: rgba(64, 158, 255, 0.08);
  border-radius: 6px;
  display: inline-block;
}

/* 美化表格 */
:deep(.el-table) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

:deep(.el-table__header) {
  background: linear-gradient(to right, #f0f2f5, #e4e7ed);
}

:deep(.el-table__header-wrapper th) {
  background-color: transparent;
  font-weight: 600;
  color: #1e3c72;
  padding: 12px 0;
}

:deep(.el-table__row) {
  transition: all 0.3s;
}

:deep(.el-table__row:hover) {
  background-color: #f0f7ff;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
}

:deep(.el-button) {
  transition: all 0.3s;
}

:deep(.el-button:hover) {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
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
  border-color: #409EFF;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #1e3c72;
  font-size: 15px;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #409EFF inset, 0 4px 12px rgba(0, 0, 0, 0.1);
}

:deep(.el-progress) {
  margin: 10px 0;
}

:deep(.el-progress__text) {
  font-weight: 600;
  color: #1e3c72;
}

:deep(.el-progress-bar__outer) {
  border-radius: 10px;
  background-color: #e6e6e6;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
}

:deep(.el-progress-bar__inner) {
  border-radius: 10px;
  background: linear-gradient(to right, #1e3c72, #2a5298);
  box-shadow: 0 2px 6px rgba(30, 60, 114, 0.3);
  transition: width 0.5s cubic-bezier(0.22, 0.61, 0.36, 1);
}

/* 视频信息样式 */
.video-info-box {
  background: rgba(240, 247, 255, 0.5);
  border-radius: 8px;
  padding: 8px 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  border-left: 3px solid #409EFF;
}

.video-info-box div {
  margin: 5px 0;
  font-size: 13px;
  color: #606266;
}

/* 操作按钮样式 */
.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.action-button {
  position: relative;
  overflow: hidden;
}

.action-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(255,255,255,0.8) 0%, rgba(255,255,255,0) 70%);
  transform: scale(0);
  opacity: 0;
  transition: transform 0.5s, opacity 0.3s;
}

.action-button:hover::before {
  transform: scale(2);
  opacity: 1;
}

.play-button:not(:disabled):hover {
  background-color: #67C23A;
  border-color: #67C23A;
}

.process-button:not(:disabled):hover {
  background-color: #409EFF;
  border-color: #409EFF;
}

.delete-button:hover {
  transform: rotate(5deg);
}

/* 动画效果 */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes pulse {
  0% { box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); }
  50% { box-shadow: 0 4px 20px rgba(64, 158, 255, 0.2); }
  100% { box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); }
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes fadeInLeft {
  from { transform: translateX(-20px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

/* 指南卡片样式 */
.guide-row {
  margin: 20px 0 80px 0;
}

.guide-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  height: 100%;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  animation: fadeIn 0.8s ease-out;
}

.guide-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 5px;
  background: linear-gradient(90deg, #1e3c72, #2a5298);
}

.guide-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.guide-icon {
  font-size: 36px;
  color: #1e3c72;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background: rgba(30, 60, 114, 0.1);
  margin: 0 auto 15px;
}

.guide-card h3 {
  text-align: center;
  color: #1e3c72;
  margin-bottom: 15px;
  font-size: 18px;
}

.guide-card ul {
  padding-left: 20px;
  margin: 0;
}

.guide-card li {
  margin-bottom: 8px;
  color: #606266;
  position: relative;
}

.guide-card li::before {
  content: "✓";
  color: #409EFF;
  position: absolute;
  left: -18px;
}

.guide-card p {
  color: #606266;
  line-height: 1.6;
}

.process-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 20px;
}

.process-step {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.step-number {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1e3c72, #2a5298);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-bottom: 8px;
}

.step-text {
  font-size: 14px;
  color: #606266;
}

.process-arrow {
  margin: 0 15px;
  color: #909399;
  font-size: 20px;
}

.feature-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 15px;
}

.feature-tag {
  background: rgba(64, 158, 255, 0.1);
  color: #409EFF;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
}

/* 空状态样式 */
.empty-state {
  padding: 40px 0;
  text-align: center;
  color: #909399;
}

.empty-icon {
  font-size: 60px;
  margin-bottom: 20px;
  color: #dcdfe6;
}

.empty-state p {
  margin: 5px 0;
}

.empty-tip {
  font-size: 14px;
  opacity: 0.7;
}

/* 底部信息卡片 */
.bottom-info-section {
  margin-top: 80px;
  margin-bottom: 30px;
  clear: both;
  position: relative;
}

.info-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  height: 100%;
}

.info-card h3 {
  color: #1e3c72;
  margin-top: 0;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
}

.info-content p {
  margin: 8px 0;
  color: #606266;
}

.stats-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.stat-value {
  font-size: 16px;
  color: #303133;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 5px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.status-dot.active {
  background-color: #67C23A;
  box-shadow: 0 0 5px rgba(103, 194, 58, 0.5);
}

.status-dot.inactive {
  background-color: #F56C6C;
  box-shadow: 0 0 5px rgba(245, 108, 108, 0.5);
}

/* 页脚 */
.page-footer {
  text-align: center;
  padding: 20px 0;
  color: #909399;
  font-size: 14px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  margin-top: 30px;
}

/* 视频信息盒子样式 */
.video-info-box {
  background: rgba(64, 158, 255, 0.05);
  border-left: 3px solid #409EFF;
  padding: 8px 12px;
  border-radius: 0 4px 4px 0;
}

.video-info-box div {
  margin: 4px 0;
  color: #606266;
}

/* 动画效果 */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(64, 158, 255, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(64, 158, 255, 0); }
  100% { box-shadow: 0 0 0 0 rgba(64, 158, 255, 0); }
}

@keyframes fadeInLeft {
  from { transform: translateX(-20px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.upload-flex-container {
  display: flex;
  align-items: flex-start;
  gap: 20px;
}

.upload-format-tip {
  background: rgba(30, 60, 114, 0.05);
  border-left: 3px solid #1e3c72;
  padding: 15px;
  border-radius: 0 4px 4px 0;
  color: #606266;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  height: fit-content;
  margin-top: 10px;
}

.upload-format-tip .el-icon {
  color: #1e3c72;
  font-size: 18px;
}
</style>


<style>
/* 对话框样式 */
.video-process-dialog {
  width: 800px !important;
  max-width: 90vw !important;
}

.video-process-dialog .el-message-box__header {
  background: linear-gradient(135deg, #1e3c72, #2a5298);
  padding: 15px 20px !important;
  border-bottom: none !important;
}

.video-process-dialog .el-message-box__title {
  color: white !important;
}

.video-process-dialog .el-message-box__content {
  max-height: 80vh;
  overflow-y: auto;
  padding: 0 !important;
  background: #f5f7fa;
}

.video-process-dialog .el-message-box__message {
  padding: 0 !important;
  width: 100% !important;
}

.video-process-dialog .el-message-box__message p {
  margin: 0 !important;
}

/* 处理对话框内容布局 */
.process-dialog-wrapper {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  width: 100%;
  background: #f5f7fa;
}

/* 标题区域样式 */
.dialog-header {
  border-radius: 12px;
  padding: 25px;
  background: linear-gradient(135deg, #1e3c72, #2a5298);
  color: white;
  box-shadow: 0 8px 20px rgba(30, 60, 114, 0.15);
  transform: translateY(0);
  transition: all 0.3s ease;
}

.dialog-header:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 25px rgba(30, 60, 114, 0.2);
}

/* 内容卡片样式 */
.content-card {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.content-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

/* 语言选择器样式 */
.language-option {
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.language-option:hover {
  transform: scale(1.02);
}

.language-option.selected::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, rgba(64, 158, 255, 0.1), rgba(64, 158, 255, 0.2));
  z-index: 0;
}

/* 模型选择器样式 */
.model-size-slider {
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.model-size-slider:hover {
  transform: scale(1.01);
}

#model-description {
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

#model-description:hover {
  transform: translateX(5px);
}

/* 信息提示样式 */
.info-tip {
  background: rgba(64, 158, 255, 0.1);
  border-radius: 8px;
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s ease;
}

.info-tip:hover {
  background: rgba(64, 158, 255, 0.15);
  transform: translateX(5px);
}

/* 按钮样式 */
.el-message-box__btns {
  padding: 20px !important;
  background: #f5f7fa;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.el-message-box__btns button {
  padding: 12px 25px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.el-message-box__btns button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>