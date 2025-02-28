<template>
  <div class="upload-container">
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <h2>视频上传</h2>
        </div>
      </template>
      
      <el-form ref="uploadForm" :model="formData" label-width="120px">
        <!-- 本地视频上传 -->
        <el-form-item label="本地视频">
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
            <template #tip>
              <div class="el-upload__tip">
                支持的格式：MP4, AVI, MOV, MKV, WEBM
              </div>
            </template>
          </el-upload>
          
          <!-- 上传进度条 -->
          <div v-if="uploadProgress > 0" class="progress-container">
            <el-progress 
              :percentage="uploadProgress" 
              :status="uploadStatus"
              :stroke-width="15"
            />
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
            <div v-if="scope.row.duration">
              <div>时长: {{ formatDuration(scope.row.duration) }}</div>
              <div>分辨率: {{ scope.row.width }}x{{ scope.row.height }}</div>
              <div>帧率: {{ scope.row.fps ? scope.row.fps.toFixed(2) : '未知' }} FPS</div>
            </div>
            <span v-else>暂无信息</span>
          </template>
        </el-table-column>
        <el-table-column prop="upload_time" label="上传时间">
          <template #default="scope">
            {{ formatDate(scope.row.upload_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button 
              :icon="VideoCamera"
              circle
              @click="handleProcess(scope.row)"
              :disabled="!['uploaded', 'pending'].includes(scope.row.status) || scope.row.status === 'downloading'"
              title="处理视频"
            />
            <el-button 
              type="danger" 
              :icon="Delete"
              circle
              @click="handleDelete(scope.row)"
              title="删除视频"
            />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  UploadFilled, 
  VideoCamera,
  Delete, 
  Refresh 
} from '@element-plus/icons-vue'
import { 
  uploadLocalVideo, 
  uploadVideoUrl, 
  getVideoList, 
  processVideo,
  getVideoPreviewImage,
  deleteVideo,
  getVideoStatus,
  getVideo
} from '@/api/video'

const formData = ref({
  videoUrl: ''
})

const uploadProgress = ref(0)
const uploadStatus = ref('')
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
  try {
    uploadProgress.value = 0
    uploadStatus.value = ''
    
    const formData = new FormData()
    formData.append('file', file)
    
    await uploadLocalVideo(formData, (progressEvent) => {
      if (progressEvent.lengthComputable) {
        uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
      }
    })
    
    uploadProgress.value = 100
    uploadStatus.value = 'success'
    ElMessage.success('上传成功！')
    refreshList()
  } catch (error) {
    uploadStatus.value = 'exception'
    console.error('上传错误:', error)
    ElMessage.error(error.response?.data?.error || '上传失败，请重试')
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
    
    console.log(`视频${videoId}状态: ${status}, 尝试次数: ${attempts+1}`)
    
    // 如果视频下载完成或失败，停止轮询
    if (status === 'uploaded') {
      if (pollingTimers.value[videoId]) {
        clearInterval(pollingTimers.value[videoId])
        delete pollingTimers.value[videoId]
      }
      
      console.log(`视频${videoId}下载完成，停止轮询`)
      uploadStatus.value = 'success'
      ElMessage({
        message: 'YouTube视频下载成功',
        type: 'success',
        duration: 3000
      })
      
      // 清空输入框并刷新列表
      formData.value.videoUrl = ''
      refreshList()
    } else if (status === 'failed') {
      if (pollingTimers.value[videoId]) {
        clearInterval(pollingTimers.value[videoId])
        delete pollingTimers.value[videoId]
      }
      
      console.log(`视频${videoId}下载失败，停止轮询`)
      uploadStatus.value = 'exception'
      ElMessage.error('视频下载失败')
    } else {
      console.log(`视频${videoId}仍在下载中，状态: ${status}，继续轮询`)
    }
    
    // 达到最大尝试次数，停止轮询
    if (attempts >= maxAttempts) {
      if (pollingTimers.value[videoId]) {
        clearInterval(pollingTimers.value[videoId])
        delete pollingTimers.value[videoId]
      }
      
      console.log(`视频${videoId}轮询达到最大次数，停止轮询`)
      // 不显示错误，因为视频可能仍在下载中
      ElMessage({
        message: '视频可能仍在下载中，请稍后刷新列表查看',
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
    const response = await getVideoList()
    if (response && response.videos) {
      videoList.value = response.videos
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
    await processVideo(video.id)
    ElMessage({
      message: '视频正在处理，请稍候...',
      type: 'info',
      duration: 5000
    })
    
    // 启动轮询检查处理状态
    startPollingProcessStatus(video.id)
  } catch (error) {
    console.error('处理视频失败:', error)
    ElMessage.error(error.response?.error || '处理视频失败')
  }
}

// 轮询检查视频处理状态
const startPollingProcessStatus = (videoId) => {
  // 清除可能存在的旧定时器
  if (processingTimers.value[videoId]) {
    clearInterval(processingTimers.value[videoId])
  }
  
  let attempts = 0
  const maxAttempts = 240 // 最多轮询20分钟 (240次 * 5秒)
  
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
    
    // 使用getVideoList代替getVideo，因为getVideoList更稳定
    const response = await getVideoList()
    
    if (!response || !response.videos) {
      console.log(`获取视频列表失败，继续轮询`)
      return
    }
    
    // 在列表中查找指定ID的视频
    const video = response.videos.find(v => v.id === videoId)
    
    if (!video) {
      console.log(`在列表中未找到视频${videoId}，继续轮询`)
      return
    }
    
    const status = video.status
    console.log(`视频${videoId}处理状态: ${status}, 尝试次数: ${attempts+1}`)
    
    // 如果视频处理完成或失败，停止轮询
    if (status === 'completed') {
      if (processingTimers.value[videoId]) {
        clearInterval(processingTimers.value[videoId])
        delete processingTimers.value[videoId]
      }
      
      console.log(`视频${videoId}处理完成，停止轮询`)
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
  return `http://localhost:5000/api/videos/${video.id}/preview`
}

// 处理表格多选事件
const handleSelectionChange = (selection) => {
  selectedVideos.value = selection
  console.log('选中的视频:', selectedVideos.value)
}

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

.upload-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-container {
  margin-top: 20px;
}

.el-upload {
  width: 100%;
}

.el-upload-dragger {
  width: 100%;
}

:deep(.el-upload__tip) {
  margin-top: 8px;
}

.video-list-card {
  margin-top: 20px;
}
</style>
