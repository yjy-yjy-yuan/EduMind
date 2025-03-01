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
    // 创建对话框内容
    const dialogHtml = `
      <div style="font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;">
        <div style="margin-bottom: 20px; border-bottom: 1px solid #ebeef5; padding-bottom: 15px;">
          <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <i class="el-icon-video-camera" style="color: #409EFF; font-size: 18px; margin-right: 8px;"></i>
            <span style="font-size: 16px; font-weight: 600; color: #303133;">视频转录设置</span>
          </div>
          <p style="margin: 5px 0 0; font-size: 13px; color: #909399;">请选择视频语言和转录模型大小，以获得最佳转录效果</p>
        </div>
        
        <div style="margin-bottom: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: 500; color: #606266; font-size: 14px;">
            <i class="el-icon-s-flag" style="margin-right: 5px;"></i>视频语言：
          </label>
          <div class="language-selector" style="display: flex; width: 100%; margin-bottom: 5px;">
            <div class="language-option" data-value="English" style="flex: 1; text-align: center; padding: 10px; border: 1px solid #dcdfe6; border-radius: 4px 0 0 4px; cursor: pointer; background-color: #f5f7fa; color: #606266; transition: all 0.3s;">
              <div style="font-weight: 500; margin-bottom: 3px;">English</div>
              <div style="font-size: 12px; color: #909399;">英语</div>
            </div>
            <div class="language-option selected" data-value="Other" style="flex: 1; text-align: center; padding: 10px; border: 1px solid #409EFF; border-radius: 0 4px 4px 0; cursor: pointer; background-color: #ecf5ff; color: #409EFF; transition: all 0.3s;">
              <div style="font-weight: 500; margin-bottom: 3px;">Other</div>
              <div style="font-size: 12px; color: #409EFF;">其他语言</div>
            </div>
          </div>
          <input type="hidden" id="language-select" value="Other">
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            <i class="el-icon-info-circle" style="margin-right: 3px;"></i>选择与视频主要语言相符的选项
          </div>
        </div>
        
        <div style="margin-bottom: 10px;">
          <label style="display: block; margin-bottom: 8px; font-weight: 500; color: #606266; font-size: 14px;">
            <i class="el-icon-s-operation" style="margin-right: 5px;"></i>转录模型大小：
          </label>
          <div id="model-options-container">
            <div class="model-size-slider" style="margin-bottom: 15px;">
              <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="font-size: 12px; color: #909399;">更快速</span>
                <span style="font-size: 12px; color: #909399;">更准确</span>
              </div>
              <div style="position: relative; height: 60px; background: linear-gradient(to right, #67C23A, #E6A23C, #F56C6C); border-radius: 4px; overflow: hidden;">
                <div id="model-options" style="display: flex; height: 100%; position: relative;">
                  <!-- 模型选项将在这里动态生成 -->
                </div>
              </div>
            </div>
            <div id="model-description" style="background-color: #f5f7fa; border-radius: 4px; padding: 12px; margin-top: 5px; border-left: 3px solid #409EFF;">
              <div style="font-weight: 500; color: #303133; margin-bottom: 5px;">turbo 模型 (推荐)</div>
              <div style="font-size: 13px; color: #606266;">
                <p style="margin: 0 0 5px;">• 处理速度：<span style="color: #67C23A; font-weight: 500;">极快</span></p>
                <p style="margin: 0 0 5px;">• 准确度：<span style="color: #409EFF; font-weight: 500;">良好</span></p>
                <p style="margin: 0;">• 适用场景：<span style="color: #606266;">一般视频转录，对速度要求高</span></p>
              </div>
            </div>
          </div>
          <input type="hidden" id="model-select" value="turbo">
          <div style="font-size: 12px; color: #909399; margin-top: 10px; display: flex; align-items: center;">
            <i class="el-icon-info-circle" style="margin-right: 3px;"></i>
            <span>从左到右：模型越大，转录准确度越高，但处理时间也越长</span>
          </div>
        </div>
        
        <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #ebeef5; font-size: 13px; color: #606266;">
          <div style="display: flex; align-items: center;">
            <i class="el-icon-warning-outline" style="color: #e6a23c; margin-right: 5px;"></i>
            <span>选择后将开始处理视频，请耐心等待</span>
          </div>
        </div>
      </div>
    `;

    // 显示对话框
    ElMessageBox.confirm(dialogHtml, '处理视频', {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '开始处理',
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
                value: 'tiny.en', 
                text: 'tiny.en', 
                desc: '最小',
                color: '#67C23A',
                speed: '极快',
                accuracy: '一般',
                useCase: '简单内容，对速度要求高',
                speedColor: '#67C23A',
                accuracyColor: '#E6A23C'
              },
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
                value: 'tiny', 
                text: 'tiny', 
                desc: '最小',
                color: '#67C23A',
                speed: '极快',
                accuracy: '一般',
                useCase: '简单内容，对速度要求高',
                speedColor: '#67C23A',
                accuracyColor: '#E6A23C'
              },
              { 
                value: 'base', 
                text: 'base', 
                desc: '基础',
                color: '#85CF4E',
                speed: '很快',
                accuracy: '良好',
                useCase: '一般内容，速度和准确度平衡',
                speedColor: '#85CF4E',
                accuracyColor: '#E6A23C'
              },
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
                value: 'large', 
                text: 'large', 
                desc: '大型',
                color: '#F56C6C',
                speed: '较慢',
                accuracy: '极高',
                useCase: '专业内容，对准确度要求高',
                speedColor: '#F56C6C',
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
