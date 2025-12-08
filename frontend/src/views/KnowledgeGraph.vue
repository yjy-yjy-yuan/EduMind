<template>
  <div class="knowledge-graph-container">
    <section class="video-hero-section">
      <div class="hero-overlay"></div>
      <div class="hero-container">
        <div class="hero-content-wrapper">
          <div class="hero-text">
            <h1 class="main-title">知识点总览</h1>
            <p class="subtitle">探索视频中的核心概念及其关联知识</p>
            <div class="hero-description-container">
              <p class="hero-description">🔍 通过知识图谱，轻松理解视频内容之间的关联，提升学习效率。✨</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 视频选择区域 -->
    <el-card class="video-selection-card">
      <template #header>
        <div class="card-header">
          <div class="title-wrapper">
            <i class="title-icon">
              <el-icon><VideoCamera /></el-icon>
            </i>
            <h2>选择视频</h2>
          </div>
        </div>
      </template>

      <div class="selection-content">
        <el-select
          v-model="selectedVideo"
          placeholder="请选择要查看的视频"
          class="video-select"
          @change="loadKnowledgeGraph"
          style="width: 100%"
          :key="'video-select-' + (selectedVideo ? selectedVideo.id : 'empty')"
          value-key="id"
        >
          <el-option
            v-for="video in videoList"
            :key="video.id"
            :label="video.filename"
            :value="video"
          />
        </el-select>
      </div>
    </el-card>

    <!-- 知识图谱展示区域 -->
    <el-card class="graph-display-card" v-loading="isLoading">
      <template #header>
        <div class="card-header">
          <div class="title-wrapper">
            <i class="title-icon">
              <el-icon><Connection /></el-icon>
            </i>
            <h2>知识图谱</h2>
          </div>
          <div class="graph-controls" v-if="hasGraph">
            <el-button-group>
              <el-button @click="zoomIn"><el-icon><ZoomIn /></el-icon></el-button>
              <el-button @click="zoomOut"><el-icon><ZoomOut /></el-icon></el-button>
              <el-button @click="resetZoom"><el-icon><Refresh /></el-icon></el-button>
            </el-button-group>
          </div>
        </div>
      </template>

      <div class="graph-container">
        <!-- 空状态提示 -->
        <div v-if="!hasGraph && !isLoading && !isGenerating" class="empty-graph">
          <el-empty description="暂无知识图谱数据，请选择视频并生成知识图谱" />
        </div>

        <!-- 生成中的提示信息 -->
        <div v-if="isGenerating" class="generating-container">
          <div class="generating-content">
            <div class="generating-icon">
              <el-icon class="rotating"><Connection /></el-icon>
            </div>
            <h3 class="generating-title">正在生成知识图谱</h3>

            <p class="generating-tip" v-if="currentStep === 0">正在为您分析视频内容和字幕数据...</p>
            <p class="generating-tip" v-else-if="currentStep === 1">正在从内容中提取核心知识点和关键概念...</p>
            <p class="generating-tip" v-else-if="currentStep === 2">正在建立知识点之间的关联关系和结构...</p>
            <p class="generating-tip" v-else-if="currentStep === 3">正在完成知识图谱的渲染和可视化处理...</p>

            <div class="generating-steps">
              <div class="step-item" :class="{ active: currentStep === 0 }">
                <div class="step-icon">
                  <el-icon><VideoCamera /></el-icon>
                </div>
                <div class="step-info">
                  <h4>视频分析</h4>
                  <p>正在分析视频内容和字幕</p>
                </div>
              </div>

              <div class="step-item" :class="{ active: currentStep === 1 }">
                <div class="step-icon">
                  <el-icon><Connection /></el-icon>
                </div>
                <div class="step-info">
                  <h4>知识提取</h4>
                  <p>从内容中提取核心知识点</p>
                </div>
              </div>

              <div class="step-item" :class="{ active: currentStep === 2 }">
                <div class="step-icon">
                  <i class="graph-icon"></i>
                </div>
                <div class="step-info">
                  <h4>图谱构建</h4>
                  <p>建立知识点之间的关联关系</p>
                </div>
              </div>

            </div>

            <div class="generating-tips-container">
              <div class="tip-card">
                <h4>💡 小贴士</h4>
                <p>知识图谱生成可能需要一些时间，请耐心等待。生成过程中您可以切换到其他页面，系统会在后台继续处理。</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 图例说明 -->
        <div v-if="hasGraph" class="graph-legend">
          <h4>图例说明：</h4>
          <div class="legend-item">
            <span class="legend-color" style="background-color: #F472B6;"></span>
            <span>视频节点</span>
          </div>
          <div class="legend-item">
            <span class="legend-color" style="background-color: #3B82F6;"></span>
            <span>一级知识点</span>
          </div>
          <div class="legend-item">
            <span class="legend-color" style="background-color: #10B981;"></span>
            <span>扩展知识点</span>
          </div>
          <div class="legend-item">
            <span class="legend-color" style="background-color: #EAB308;"></span>
            <span>其他视频相似知识点</span>
          </div>
          <div class="legend-item">
            <span class="legend-line" style="border-top: 2px solid #3B82F6;"></span>
            <span>当前视频的关联关系</span>
          </div>
          <div class="legend-item">
            <span class="legend-line" style="border-top: 2px dashed #FF6B6B;"></span>
            <span>其它视频的知识点</span>
          </div>
          <div class="legend-item">
            <span class="legend-line" style="border-top: 2px solid #EBBC75;"></span>
            <span>其它视频的扩展关系</span>
          </div>
        </div>

        <div id="knowledge-graph-container" class="graph-svg-container" style="width: 100%; height: 600px;"></div>
      </div>
    </el-card>
  </div>

  <!-- 知识点详情弹窗 -->
  <el-dialog
    v-model="dialogVisible"
    :title="selectedNode.label"
    width="50%"
    :close-on-click-modal="false"
  >
    <div class="knowledge-detail">
      <h3>{{ selectedNode.label }}</h3>

      <!-- 显示来源视频信息 -->
      <div v-if="selectedNode.source_video_title" class="knowledge-source">
        <el-tag type="info">来源视频: {{ selectedNode.source_video_title }}</el-tag>
      </div>

      <p v-if="selectedNode.description">{{ selectedNode.description }}</p>
      <div class="knowledge-actions">
        <h4>您想要：</h4>
        <!-- 视频节点只显示查看当前视频按钮 -->
        <template v-if="selectedNode.type === 'video'">
          <el-button type="primary" @click="navigateToVideo">
            查看当前视频
          </el-button>
        </template>
        <!-- 非视频节点显示所有选项 -->
        <template v-else>
          <el-button type="primary" @click="navigateToVideo">
            学习当前视频中的该知识点
          </el-button>
        </template>
      </div>


    </div>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, onActivated, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElNotification, ElMessageBox } from 'element-plus'
import { VideoCamera, Connection, ZoomIn, ZoomOut, Refresh } from '@element-plus/icons-vue'
import * as d3 from 'd3'
import { getVideoList } from '@/api/video'

// 状态变量
const router = useRouter()
const route = useRoute()
const videoList = ref([])
const selectedVideo = ref(null)
const isLoading = ref(false)
const isGenerating = ref(false)
const hasGraph = ref(false)
let checkFailCount = 0 // 检查失败次数
const graphContainer = ref(null)
const dialogVisible = ref(false)
const selectedNode = ref({})


// 知识图谱生成步骤跟踪
const currentStep = ref(0) // 0: 视频分析, 1: 知识提取, 2: 图谱构建, 3: 完成渲染
const stepUpdateTimer = ref(null) // 步骤更新定时器

// 生成状态存储键
const GENERATION_STATUS_KEY = 'knowledgeGraphGenerationStatus'

// 图谱相关变量
const graphData = ref({ nodes: [], links: [] })
let svg = ref(null) // SVG元素
let zoom = null // 缩放功能
let simulation = null // 力导向图
let containerG = null // 容器

// 初始化
onMounted(async () => {
  await loadVideoList()

  // 从 URL 参数或本地存储中恢复视频 ID
  await restoreSelectedVideo()

  // 检查是否有未完成的生成任务
  const pendingGeneration = checkPendingGeneration()
  if (pendingGeneration && selectedVideo.value && pendingGeneration.videoId === selectedVideo.value.id) {
    console.log(`发现未完成的知识图谱生成任务，视频ID: ${pendingGeneration.videoId}`)
    // 恢复生成状态
    isGenerating.value = true

    // 显示生成进度提示
    showGenerationNotification(true)

    // 开始轮询
    console.log('继续轮询知识图谱生成状态...')
    pollKnowledgeGraphStatus()
  }
})

// 当组件被激活时（从其他页面切换回来）
onActivated(async () => {
  console.log('知识图谱组件被激活')

  // 检查视频列表是否已加载
  if (videoList.value.length === 0) {
    await loadVideoList()
  }

  // 恢复选择的视频
  await restoreSelectedVideo()

  // 强制更新下拉框的选择状态
  nextTick(() => {
    if (selectedVideo.value) {
      console.log('强制更新下拉框选择状态:', selectedVideo.value)
      // 查找当前选择的视频在列表中的名称
      const selectedVideoInfo = videoList.value.find(video => String(video.id) === String(selectedVideo.value.id))
      if (selectedVideoInfo) {
        console.log('当前选择的视频名称:', selectedVideoInfo.filename)
      } else {
        console.warn('当前选择的视频在列表中不存在，但知识图谱可能已加载')
      }
    }
  })
})

// 从URL参数或本地存储中恢复视频ID
const restoreSelectedVideo = async () => {
  // 优先从URL参数中获取视频ID
  const videoIdFromUrl = route.query.videoId
  const savedVideoId = localStorage.getItem('selectedKnowledgeGraphVideo')

  let videoIdToRestore = null

  // 确定要恢复的视频ID
  if (videoIdFromUrl) {
    console.log('从URL参数中获取视频ID:', videoIdFromUrl)
    videoIdToRestore = videoIdFromUrl
  } else if (savedVideoId) {
    console.log('从本地存储中获取视频ID:', savedVideoId)
    videoIdToRestore = savedVideoId
  }

  // 如果有视频ID要恢复，检查它是否在视频列表中
  if (videoIdToRestore) {
    // 确保视频列表已加载
    if (videoList.value.length === 0) {
      await loadVideoList()
    }

    // 打印视频列表，帮助调试
    console.log('当前视频列表:', videoList.value.map(v => `${v.id}(${typeof v.id}):${v.filename}`))

    // 查找视频对象
    const videoObj = videoList.value.find(video => String(video.id) === String(videoIdToRestore))

    if (videoObj) {
      console.log('恢复的视频ID在列表中存在:', videoIdToRestore, '视频名称:', videoObj.filename)
      selectedVideo.value = videoObj
      await loadKnowledgeGraph()
    } else {
      console.warn('恢复的视频ID在列表中不存在:', videoIdToRestore)

      // 尝试直接加载知识图谱，即使视频不在列表中
      try {
        console.log('尝试直接加载知识图谱:', videoIdToRestore)

        // 创建临时视频对象
        const tempVideo = { id: videoIdToRestore, filename: `视频 ${videoIdToRestore}` }
        selectedVideo.value = tempVideo

        const response = await fetch(`/api/knowledge-graph/${videoIdToRestore}`)

        if (response.ok) {
          console.log('成功加载知识图谱，保留选择状态')
          const data = await response.json()
          if (data && data.nodes && data.nodes.length > 0) {
            graphData.value = data
            hasGraph.value = true

            // 更新URL参数
            router.push({
              query: { ...route.query, videoId: videoIdToRestore }
            })

            // 保存到本地存储
            localStorage.setItem('selectedKnowledgeGraphVideo', videoIdToRestore)

            // 渲染图谱
            nextTick(() => {
              renderGraph()
            })

            // 尝试获取视频详情，更新下拉框显示
            try {
              const videoResponse = await fetch(`/api/videos/${videoIdToRestore}`)
              if (videoResponse.ok) {
                const videoData = await videoResponse.json()
                if (videoData && videoData.filename) {
                  // 更新临时视频对象的文件名
                  tempVideo.filename = videoData.filename

                  // 如果视频不在列表中，添加到列表中
                  if (!videoList.value.some(v => String(v.id) === String(videoIdToRestore))) {
                    videoList.value.push({
                      id: videoIdToRestore,
                      filename: videoData.filename,
                      status: 'completed'
                    })
                    console.log('将视频添加到列表中:', videoData.filename)
                  }
                }
              }
            } catch (error) {
              console.error('获取视频详情失败:', error)
            }

            return
          }
        }

        // 如果加载失败，重置选择
        console.warn('无法加载知识图谱，重置选择')
        selectedVideo.value = null
        localStorage.removeItem('selectedKnowledgeGraphVideo')
        hasGraph.value = false
      } catch (error) {
        console.error('加载知识图谱出错:', error)
        selectedVideo.value = null
        localStorage.removeItem('selectedKnowledgeGraphVideo')
        hasGraph.value = false
      }
    }
  }
}

// 加载视频列表
const loadVideoList = async () => {
  try {
    isLoading.value = true
    const { data } = await getVideoList()
    if (data && data.videos) {
      console.log('获取到视频列表:', data.videos.length, '个视频')
      videoList.value = data.videos.filter(video => video.status === 'completed')
      console.log('过滤后的视频列表:', videoList.value.length, '个视频')
    }
  } catch (error) {
    console.error('获取视频列表失败:', error)
    ElMessage.error('获取视频列表失败')
  } finally {
    isLoading.value = false
  }
}

// 加载知识图谱
const loadKnowledgeGraph = async () => {
  if (!selectedVideo.value) return

  const videoId = selectedVideo.value.id

  // 保存到本地存储
  localStorage.setItem('selectedKnowledgeGraphVideo', videoId)

  // 更新URL参数，不刷新页面
  router.push({
    query: { ...route.query, videoId }
  })

  try {
    isLoading.value = true
    hasGraph.value = false

    // 首先检查该视频是否参与了合并
    console.log(`检查视频 ${videoId} 是否参与了合并...`)
    const checkResponse = await fetch(`/api/knowledge-graph-integration/check-combined/${videoId}`)

    let videoIdToLoad = videoId
    let isCombined = false

    if (checkResponse.ok) {
      const checkData = await checkResponse.json()
      console.log('检查结果:', checkData)

      if (checkData.is_combined) {
        console.log(`视频 ${videoId} 是合并视频`)
        isCombined = true
      } else if (checkData.is_part_of_combined) {
        console.log(`视频 ${videoId} 参与了合并，合并ID为: ${checkData.combined_video_id}`)
        videoIdToLoad = checkData.combined_video_id
        isCombined = true

        // 显示提示信息
        ElMessage.info(`正在显示合并知识图谱 (ID: ${videoIdToLoad})，包含当前视频和其他相似视频的知识点`)
      }
    }

    // 调用后端API获取知识图谱数据
    const apiUrl = `/api/knowledge-graph/${videoIdToLoad}`
    console.log(`请求知识图谱数据: ${apiUrl}`)

    // 如果是合并视频，显示提示信息
    if (isCombined && videoId !== videoIdToLoad) {
      ElMessage.info(`正在显示合并知识图谱 (ID: ${videoIdToLoad})，包含多个相关视频的知识点，每个知识点都标注了来源视频`)
    }

    const response = await fetch(apiUrl)

    if (!response.ok) {
      const responseData = await response.json()
      console.log('知识图谱响应数据:', responseData)

      // 如果返回202，说明知识图谱正在生成中
      if (response.status === 202) {
        console.info('知识图谱正在生成中:', responseData.status)
        ElMessage.info('知识图谱正在生成中，请稍后刷新页面')
        isGenerating.value = true

        // 显示生成进度提示
        ElNotification({
          title: '知识图谱生成中',
          message: '正在为您生成知识图谱，这可能需要几分钟左右时间，请耐心等待',
          type: 'info',
          duration: 10000
        })

        // 设置定时器，10秒后自动重新加载
        setTimeout(() => {
          loadKnowledgeGraph()
          isGenerating.value = false
        }, 10000)

        return
      }

      // 如果返回404，说明该视频尚未生成知识图谱
      if (response.status === 404) {
        console.info('知识图谱不存在，自动开始生成')
        hasGraph.value = false

        // 显示提示信息
        ElMessage.info('正在为您生成知识图谱，请稍等...')

        // 自动生成知识图谱
        generateKnowledgeGraph()
        return
      }

      throw new Error(responseData.error || '获取知识图谱失败')
    }

    // 解析响应数据
    const data = await response.json()

    // 确保数据有效再设置和渲染
    if (data && data.nodes && data.nodes.length > 0) {
      graphData.value = data
      hasGraph.value = true

      // 渲染图谱
      nextTick(() => {
        renderGraph()
      })
    } else {
      console.warn('知识图谱数据不完整或为空')
      hasGraph.value = false      }
  } catch (error) {
    console.error('加载知识图谱失败:', error)
    ElMessage.error(error.message || '加载知识图谱失败')
  } finally {
    // 无论是否在生成状态，都将isLoading设置为false
    isLoading.value = false
  }
}

// 生成知识图谱
// 新的轮询函数，使用全局轮询ID进行管理
let currentPollId = 0

// 轮询知识图谱生成状态
const pollKnowledgeGraphStatus = () => {
  if (!selectedVideo.value) return

  // 生成新的轮询ID
  const pollId = ++currentPollId
  isGenerating.value = true

  // 开始轮询
  console.log(`[轮询#${pollId}] 开始轮询知识图谱生成状态...`)
  checkStatusWithRetry(pollId, 1)
}

// 带重试的状态检查函数
const checkStatusWithRetry = async (pollId, attempt) => {
  // 如果轮询ID不匹配，说明有新的轮询开始，终止当前轮询
  if (pollId !== currentPollId || !isGenerating.value) {
    console.log(`[轮询#${pollId}] 轮询已终止，可能有新的轮询开始或用户取消了生成`)
    return
  }

  console.log(`[轮询#${pollId}] 第${attempt}次尝试检查状态...`)

  try {
    // 先检查生成状态，这是最可靠的方法
    const statusResponse = await fetch(`/api/knowledge-graph/status/${selectedVideo.value.id}`)

    if (statusResponse.ok) {
      const statusData = await statusResponse.json()
      console.log(`[轮询#${pollId}] 知识图谱生成状态:`, statusData.status)

      // 如果任务已完成，尝试获取知识图谱数据
      if (statusData.status === 'completed') {
        console.log(`[轮询#${pollId}] 状态显示已完成，获取知识图谱数据`)

        try {
          // 尝试获取知识图谱数据
          const graphResponse = await fetch(`/api/knowledge-graph/${selectedVideo.value.id}`)

          if (graphResponse.ok) {
            const data = await graphResponse.json()

            // 确认数据有效
            if (data && data.nodes && data.nodes.length > 0) {
              console.log(`[轮询#${pollId}] 知识图谱已生成完成，共有节点:`, data.nodes.length)

              // 更新UI
              graphData.value = data
              hasGraph.value = true
              isLoading.value = false
              isGenerating.value = false

              // 停止步骤进度模拟
              stopStepProgressSimulation()

              // 清除生成状态
              clearGenerationStatus()

              // 渲染图谱
              nextTick(() => {
                renderGraph()
              })

              // 显示成功消息
              ElMessage.success('知识图谱生成完成')
              ElNotification.closeAll() // 关闭所有通知
              return
            }
          } else {
            // 即使返回404，但状态已经是completed，我们也认为生成已完成
            console.log(`[轮询#${pollId}] 状态显示已完成，但无法获取知识图谱数据，状态码:`, graphResponse.status)

            // 清除生成状态并停止轮询
            isGenerating.value = false
            stopStepProgressSimulation()
            clearGenerationStatus()
            ElMessage.info('知识图谱生成已完成，但数据还未完全就绪，请稍后刷新页面')
            ElNotification.closeAll()
            return
          }
        } catch (graphError) {
          console.error(`[轮询#${pollId}] 获取知识图谱数据出错:`, graphError)
          // 即使出错，但状态已经是completed，我们也认为生成已完成
          isGenerating.value = false
          stopStepProgressSimulation()
          clearGenerationStatus()
          ElMessage.info('知识图谱生成已完成，但数据还未完全就绪，请稍后刷新页面')
          ElNotification.closeAll()
          return
        }

      // 如果任务失败
      if (statusData.status === 'failed') {
        console.error(`[轮询#${pollId}] 知识图谱生成失败`)
        isGenerating.value = false
        // 停止步骤进度模拟
        stopStepProgressSimulation()
        // 清除生成状态
        clearGenerationStatus()
        ElMessage.error('知识图谱生成失败，请重试')
        ElNotification.closeAll() // 关闭所有通知
        return
      }
    }

    // 继续轮询
    console.log(`[轮询#${pollId}] 知识图谱仍在生成中，等待10秒后再次检查`)
    setTimeout(() => {
      checkStatusWithRetry(pollId, attempt + 1)
    }, 10000)
  } else {
    console.error(`[轮询#${pollId}] 状态检查API返回错误，状态码:`, statusResponse.status)
    // 即使状态检查API失败，也继续轮询
    setTimeout(() => {
      checkStatusWithRetry(pollId, attempt + 1)
    }, 10000)
  }
  } catch (error) {
    console.error(`[轮询#${pollId}] 检查失败:`, error)

    // 如果尝试次数超过50次，认为失败
    if (attempt > 50) {
      console.error(`[轮询#${pollId}] 超过最大尝试次数，认为失败`)
      isGenerating.value = false
      ElMessage.error('知识图谱生成超时，请重试')
      ElNotification.closeAll() // 关闭所有通知
      return
    }

    // 继续重试
    setTimeout(() => {
      checkStatusWithRetry(pollId, attempt + 1)
    }, 10000)
  }
}

// 保存知识图谱生成状态
const saveGenerationStatus = (videoId) => {
  const status = {
    videoId,
    timestamp: Date.now(),
    isGenerating: true
  }
  localStorage.setItem(GENERATION_STATUS_KEY, JSON.stringify(status))
  console.log(`保存知识图谱生成状态: 视频ID ${videoId}`)
}

// 清除知识图谱生成状态
const clearGenerationStatus = () => {
  localStorage.removeItem(GENERATION_STATUS_KEY)
  console.log('清除知识图谱生成状态')
}

// 显示知识图谱生成通知
const showGenerationNotification = (isResume = false) => {
  // 先关闭所有通知，避免重复显示
  ElNotification.closeAll()

  // 显示生成进度提示
  ElNotification({
    title: '知识图谱生成中',
    message: isResume ?
      '正在继续为您生成知识图谱，这可能需要几分钟时间，请耐心等待' :
      '正在为您生成知识图谱，这可能需要几分钟时间，请耐心等待',
    type: 'info',
    duration: 0 // 不自动关闭
  })
}

// 检查是否有未完成的生成任务
const checkPendingGeneration = () => {
  const statusJson = localStorage.getItem(GENERATION_STATUS_KEY)
  if (!statusJson) return null

  try {
    const status = JSON.parse(statusJson)
    // 检查状态是否过期（30分钟）
    const isExpired = Date.now() - status.timestamp > 30 * 60 * 1000

    if (isExpired) {
      clearGenerationStatus()
      return null
    }

    return status
  } catch (e) {
    console.error('解析生成状态失败:', e)
    clearGenerationStatus()
    return null
  }
}

// 自动更新知识图谱生成步骤
const startStepProgressSimulation = () => {
  // 清除可能存在的定时器
  if (stepUpdateTimer.value) {
    clearInterval(stepUpdateTimer.value)
  }

  // 重置当前步骤
  currentStep.value = 0

  // 创建新的定时器，模拟生成过程中的步骤进展
  stepUpdateTimer.value = setInterval(() => {
    if (currentStep.value < 3) {
      currentStep.value++
      console.log(`知识图谱生成步骤更新：步骤 ${currentStep.value}`)
    } else {
      // 到达最后一步后停止定时器
      clearInterval(stepUpdateTimer.value)
      stepUpdateTimer.value = null
    }
  }, 15000) // 每15秒更新一次步骤
}

// 停止步骤进度模拟
const stopStepProgressSimulation = () => {
  if (stepUpdateTimer.value) {
    clearInterval(stepUpdateTimer.value)
    stepUpdateTimer.value = null
  }
  currentStep.value = 0
}

// 生成知识图谱
const generateKnowledgeGraph = async () => {
  if (!selectedVideo.value) {
    ElMessage.warning('请先选择视频')
    return
  }

  try {
    console.log('开始生成知识图谱...')

    isGenerating.value = true
    currentStep.value = 0 // 重置当前步骤

    // 启动步骤进度模拟
    startStepProgressSimulation()

    // 保存生成状态
    saveGenerationStatus(selectedVideo.value.id)

    // 调用后端API生成知识图谱
    const response = await fetch(`/api/knowledge-graph/generate/${selectedVideo.value.id}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      // 解析错误响应
      const errorData = await response.json()
      throw new Error(errorData.error || '生成知识图谱请求失败')
    }

    const result = await response.json()
    ElMessage.success(result.message || '知识图谱生成任务已提交，请稍后查看')

    // 显示生成进度提示
    showGenerationNotification(false)

    // 立即开始轮询
    console.log('开始轮询知识图谱生成状态...')
    pollKnowledgeGraphStatus()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('生成知识图谱失败:', error)

      // 检查是否是因为没有字幕文件导致的错误
      if (error.message && error.message.includes('没有找到字幕文件')) {
        // 使用 ElMessageBox 弹出确认窗口，提示用户跳转到播放器页面
        ElMessageBox.confirm(
          '没有找到合并后的字幕文件，需要先进行字幕合并才能生成知识图谱。是否跳转到播放器页面进行字幕合并？',
          '提示',
          {
            confirmButtonText: '跳转到播放器',
            cancelButtonText: '取消',
            type: 'warning',
            closeOnClickModal: false
          }
        ).then(() => {
          // 用户点击确认，跳转到播放器页面
          if (selectedVideo.value && selectedVideo.value.id) {
            router.push(`/player/${selectedVideo.value.id}`)
          }
        }).catch(() => {
          // 用户取消操作，不做任何处理
          ElMessage.info('您可以稍后在播放器页面完成字幕合并后再生成知识图谱')
        })
      } else {
        // 其他错误直接显示错误信息
        ElMessage.error(error.message || '生成知识图谱失败')
      }

      // 只在出错时才设置isGenerating为false，不影响轮询
      isGenerating.value = false
    }
  }
}

// 渲染图谱
const renderGraph = () => {
  console.log('开始渲染图谱...')
  if (!document.getElementById('knowledge-graph-container')) {
    console.error('图谱容器元素不存在')
    return
  }
  console.log('图谱数据:', graphData.value)
  if (!graphData.value || !graphData.value.nodes || !graphData.value.links) {
    console.error('无法渲染图谱：数据不完整')
    return
  }
  console.log('渲染图谱，节点数量:', graphData.value.nodes.length, '连接数量:', graphData.value.links.length)

  // 渲染图谱

  // 清除现有图谱
  d3.select('#knowledge-graph-container').selectAll('*').remove()

  // 获取容器实际宽度
  const container = document.getElementById('knowledge-graph-container')
  const width = container.clientWidth || 800 // 使用容器实际宽度，如果无法获取则使用默认值
  const height = 600

  console.log('图谱容器尺寸:', width, 'x', height)

  // 创建SVG
  svg.value = d3.select('#knowledge-graph-container')
    .append('svg')
    .attr('width', '100%') // 使用百分比宽度以适应容器
    .attr('height', height)
    .attr('viewBox', [0, 0, width, height])
    .attr('style', 'max-width: 100%; height: auto;')

  // 创建容器
  containerG = svg.value.append('g')

  // 添加缩放功能
  zoom = d3.zoom()
    .scaleExtent([0.1, 3])
    .on('zoom', (event) => {
      containerG.attr('transform', event.transform)
    })

  svg.value.call(zoom)

  // 创建力导向图
  simulation = d3.forceSimulation(graphData.value.nodes)
    .force('link', d3.forceLink(graphData.value.links).id(d => d.id).distance(100))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2)) // 使用实际宽度居中
    .force('collision', d3.forceCollide().radius(60))

  // 绘制连接线
  const link = containerG.append('g')
    .selectAll('line')
    .data(graphData.value.links)
    .join('line')
    .attr('stroke', d => {
      console.log('处理连线:', d);

      // 强制处理其他视频的一级知识点与视频节点之间的连线
      if (d.source && d.target) {
        // 将源和目标转换为字符串，以防止对象引用
        const sourceId = typeof d.source === 'string' ? d.source : d.source.id;
        const targetId = typeof d.target === 'string' ? d.target : d.target.id;

        // 检查是否是视频节点到其他知识点的连线
        if (sourceId && sourceId.startsWith && sourceId.startsWith('video-')) {
          // 获取目标节点
          const targetNode = graphData.value.nodes.find(node => node.id === targetId);
          console.log('检查连线:', sourceId, '->', targetId, '目标节点:', targetNode);

          // 如果目标节点存在且是其他视频的知识点
          if (targetNode) {
            // 检查目标节点是否是其他视频的知识点
            if (targetNode.category === 'similar_concept' ||
                targetNode.category === 'similar_secondary_concept' ||
                (targetNode.itemStyle && (targetNode.itemStyle.color === '#EAB308' ||
                                          targetNode.itemStyle.color === '#fac858' ||
                                          targetNode.itemStyle.color === '#e6a23c'))) {
              console.log('强制将视频节点与其他视频知识点的连线设置为红色');
              // 强制将该连线的关系类型设置为 SIMILAR_TO
              d.relationship = 'SIMILAR_TO';
              return '#FF6B6B'; // 红色
            }
          }
        }
      }

      // 使用连接线自定义样式（如果有）
      if (d.lineStyle && d.lineStyle.color) {
        return d.lineStyle.color;
      }

      // 根据关系类型设置不同的颜色
      if (d.relationship === 'SIMILAR_TO') {
        return '#FF6B6B'; // 相似关系使用红色
      } else if (d.relationship === 'RELATED_TO') {
        return '#73c0de'; // 一级到二级知识点关系使用浅蓝色
      } else if (d.relationship === 'PRIMARY') {
        return '#3B82F6'; // 视频到一级知识点关系使用蓝色
      } else if (d.relationship === 'SECONDARY') {
        return '#91cc75'; // 视频到二级知识点关系使用绿色
      }
      return '#999'; // 默认关系使用灰色
    })
    .attr('stroke-opacity', d => {
      // 相似关系使用较高的透明度
      if (d.relationship === 'SIMILAR_TO') {
        return 0.8;
      } else if (d.relationship === 'RELATED_TO') {
        return 0.7; // 一级到二级知识点关系透明度
      }
      return 0.6;
    })
    .attr('stroke-width', d => {
      // 使用连接线自定义宽度（如果有）
      if (d.lineStyle && d.lineStyle.width) {
        return d.lineStyle.width;
      }

      // 相似关系的线宽度根据相似度调整
      if (d.relationship === 'SIMILAR_TO') {
        return Math.max(1, d.similarity * 3);
      } else if (d.relationship === 'RELATED_TO') {
        return 1.5; // 一级到二级知识点关系线宽
      } else if (d.relationship === 'PRIMARY') {
        return 3; // 视频到一级知识点关系线宽
      } else if (d.relationship === 'SECONDARY') {
        return 2; // 视频到二级知识点关系线宽
      }
      return Math.sqrt(d.value || 1);
    })
    .attr('stroke-dasharray', d => {
      // 相似关系使用虚线
      if (d.relationship === 'SIMILAR_TO') {
        return '5,5';
      }
      return null;
    })

  // 绘制节点
  const node = containerG.append('g')
    .selectAll('.node')
    .data(graphData.value.nodes)
    .join('g')
    .attr('class', 'node')
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended))
    .on('click', handleNodeClick)

  // 节点圆形背景，根据节点类型和来源添加不同颜色
  node.append('circle')
    .attr('r', d => {
      // 根据节点类型设置半径
      if (d.type === 'video') return 40; // 视频节点更大
      if (d.main) return 30; // 主要概念节点
      return 20; // 扩展概念节点
    })
    .attr('fill', d => {
      // 直接使用后端返回的颜色，如果有的话
      if (d.itemStyle && d.itemStyle.color) {
        return d.itemStyle.color;
      }

      // 否则根据节点类型设置默认颜色
      if (d.type === 'video') return '#F472B6'; // 视频节点，浅粉色
      if (d.type === 'primary_concept') return '#3B82F6'; // 一级知识点使用蓝色
      if (d.type === 'secondary_concept') return '#10B981'; // 二级知识点使用绿色
      if (d.type === 'similar_concept') return '#EAB308'; // 相似知识点使用黄色
      if (d.type === 'similar_secondary_concept') return '#e6a23c'; // 其他视频的二级知识点使用更深的黄色

      // 如果是合并视频的节点，根据来源视频使用不同颜色
      if (d.source_video_id) {
        // 检查是否是当前选中的视频
        const isCurrentVideo = selectedVideo.value &&
          (d.source_video_id === selectedVideo.value.id ||
           d.source_video_id === parseInt(selectedVideo.value.id));

        if (isCurrentVideo) {
          // 当前视频的知识点使用蓝色
          return d.isPrimaryKnowledge ? '#5470c6' : '#91cc75';
        } else {
          // 其他视频的知识点使用黄色
          return '#fac858';
        }
      }

      // 兼容旧版本
      if (d.isPrimaryKnowledge) return '#5470c6'; // 一级知识点使用蓝色
      if (d.isSecondaryKnowledge) return '#91cc75'; // 二级知识点使用绿色
      return '#3B82F6'; // 默认使用蓝色
    })
    .attr('stroke', d => {
      // 为当前视频的知识点添加更明显的边框
      if (d.source_video_id && selectedVideo.value &&
          (d.source_video_id === selectedVideo.value.id ||
           d.source_video_id === parseInt(selectedVideo.value.id))) {
        return '#2563EB'; // 深蓝色边框
      }
      return '#fff';
    })
    .attr('stroke-width', d => {
      // 为当前视频的知识点添加更粗的边框
      if (d.source_video_id && selectedVideo.value &&
          (d.source_video_id === selectedVideo.value.id ||
           d.source_video_id === parseInt(selectedVideo.value.id))) {
        return 3;
      }
      return 2;
    })

  // 添加来源标记
  node.append('text')
    .filter(d => d.source_video_title) // 只为有来源信息的节点添加标记
    .text(d => {
      // 检查是否是当前选中的视频
      const isCurrentVideo = selectedVideo.value &&
        (d.source_video_id === selectedVideo.value.id ||
         d.source_video_id === parseInt(selectedVideo.value.id));

      // 从视频标题中提取简短标识
      const shortTitle = d.source_video_title.split('-').pop().substring(0, 3);
      return isCurrentVideo ? `★${shortTitle}` : `○${shortTitle}`;
    })
    .attr('x', 0)
    .attr('y', -25)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', d => {
      // 检查是否是当前选中的视频
      const isCurrentVideo = selectedVideo.value &&
        (d.source_video_id === selectedVideo.value.id ||
         d.source_video_id === parseInt(selectedVideo.value.id));

      return isCurrentVideo ? '#2563EB' : '#666';
    })

  // 节点文本
  node.append('text')
    .text(d => {
      // 如果是视频节点且名称超过15个字符，只显示前15个字符加省略号
      if (d.type === 'video' && d.label && d.label.length > 15) {
        return d.label.substring(0, 15) + '...';
      }
      return d.label;
    })
    .attr('x', 0)
    .attr('y', d => d.main ? 45 : 35)
    .attr('text-anchor', 'middle')
    .attr('fill', '#333')
    .style('font-size', d => d.main ? '14px' : '12px')
    .style('font-weight', d => d.main ? 'bold' : 'normal')
    // 添加标题属性，在鼠标悬停时显示完整名称
    .append('title')
    .text(d => d.label)

  // 更新力导向图
  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    node
      .attr('transform', d => `translate(${d.x},${d.y})`)
  })

  // 拖拽函数
  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    d.fx = d.x
    d.fy = d.y
  }

  function dragged(event, d) {
    d.fx = event.x
    d.fy = event.y
  }

  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0)
    d.fx = null
    d.fy = null
  }

  // 在控制台输出图谱数据，便于调试
  console.log('知识图谱数据:', graphData.value)
  console.log('节点数量:', graphData.value.nodes.length)
  console.log('连接数量:', graphData.value.links.length)
  console.log('节点来源分布:', graphData.value.nodes.reduce((acc, node) => {
    const sourceId = node.source_video_id
    if (sourceId) {
      acc[sourceId] = (acc[sourceId] || 0) + 1
    } else {
      acc['unknown'] = (acc['unknown'] || 0) + 1
    }
    return acc
  }, {}))
  console.log('连接类型分布:', graphData.value.links.reduce((acc, link) => {
    const type = link.relationship
    acc[type] = (acc[type] || 0) + 1
    return acc
  }, {}))

  // 不再需要D3添加的图例，使用HTML图例替代

  // 添加节点悬停提示
  const tooltip = d3.select('body').append('div')
    .attr('class', 'tooltip')
    .style('position', 'absolute')
    .style('visibility', 'hidden')
    .style('background-color', 'white')
    .style('border', '1px solid #ddd')
    .style('border-radius', '4px')
    .style('padding', '8px')
    .style('box-shadow', '0 2px 4px rgba(0,0,0,0.1)')
    .style('pointer-events', 'none')
    .style('z-index', '1000')

  // 添加悬停事件
  node.on('mouseover', function(event, d) {
    // 构建提示内容
    let content = `<strong>${d.name || d.title}</strong>`;

    if (d.description) {
      content += `<p>${d.description}</p>`;
    }

    if (d.source_video_title) {
      const isCurrentVideo = selectedVideo.value &&
        (d.source_video_id === selectedVideo.value.id ||
         d.source_video_id === parseInt(selectedVideo.value.id));

      const sourceLabel = isCurrentVideo ?
        '<span style="color:#2563EB;font-weight:bold;">当前视频</span>' :
        '<span style="color:#666;">其他视频</span>';

      content += `<p>来源: ${sourceLabel} ${d.source_video_title}</p>`;
    }

    if (d.timestamp) {
      const minutes = Math.floor(d.timestamp / 60);
      const seconds = d.timestamp % 60;
      content += `<p>时间点: ${minutes}:${seconds.toString().padStart(2, '0')}</p>`;
    }

    tooltip.html(content)
      .style('visibility', 'visible')
      .style('left', (event.pageX + 10) + 'px')
      .style('top', (event.pageY - 10) + 'px');
  })
  .on('mousemove', function(event) {
    tooltip.style('left', (event.pageX + 10) + 'px')
      .style('top', (event.pageY - 10) + 'px');
  })
  .on('mouseout', function() {
    tooltip.style('visibility', 'hidden');
  });
}

// 处理节点点击
const handleNodeClick = (event, d) => {
  selectedNode.value = d
  dialogVisible.value = true
}

// 导航到视频
const navigateToVideo = async () => {
  // 处理视频节点的情况
  if (selectedNode.value.type === 'video') {
    // 对于视频节点，直接使用节点的id作为视频id
    const videoId = selectedNode.value.id ? selectedNode.value.id.replace('video-', '') : null;

    if (!videoId) {
      ElMessage.warning('无法找到视频信息')
      return
    }

    router.push({
      path: `/player/${videoId}`
    })

    dialogVisible.value = false
    return
  }

  // 判断是否是一级知识点
  const isPrimaryKnowledge = selectedNode.value.type === 'primary_concept' ||
                            selectedNode.value.isPrimaryKnowledge ||
                            (selectedNode.value.itemStyle && selectedNode.value.itemStyle.color === '#3B82F6');

  // 处理知识点节点的情况
  if (!selectedNode.value.videoId) {
    // 尝试从节点的其他属性中获取视频ID
    if (selectedNode.value.source_video_id) {
      selectedNode.value.videoId = selectedNode.value.source_video_id;
    } else {
      ElMessage.warning('无法找到知识点对应的视频')
      return
    }
  }

  // 如果是一级知识点，生成相关问题
  let generatedQuestion = null;
  if (isPrimaryKnowledge) {
    try {
      // 显示加载中提示
      ElMessage.info('正在生成相关学习问题...');

      // 调用后端生成问题的API
      const response = await fetch('/api/knowledge-graph/generate-questions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          concept: selectedNode.value.label,
          context: selectedNode.value.description || '',
          count: 3,  // 生成3个问题
          use_ollama: true  // 默认使用离线模式
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.questions && data.questions.length > 0) {
          // 随机选择一个问题
          const randomIndex = Math.floor(Math.random() * data.questions.length);
          generatedQuestion = data.questions[randomIndex];

          // 将其他问题保存到localStorage，供用户后续使用
          const otherQuestions = data.questions.filter((_, index) => index !== randomIndex);
          localStorage.setItem(`concept_questions_${selectedNode.value.videoId}_${selectedNode.value.label}`, JSON.stringify(otherQuestions));
        }
      } else {
        console.error('生成问题失败:', await response.text());
      }
    } catch (error) {
      console.error('生成问题时出错:', error);
    }
  }

  // 将生成的问题添加到路由参数中
  const routeParams = {
    path: `/player/${selectedNode.value.videoId}`,
    query: {}
  };

  // 如果有时间戳，添加到查询参数中
  if (selectedNode.value.timestamp) {
    routeParams.query.t = selectedNode.value.timestamp;
  }

  // 如果有生成的问题，添加到查询参数中
  if (generatedQuestion) {
    routeParams.query.auto_question = generatedQuestion;
  }

  router.push(routeParams);

  dialogVisible.value = false;
}

// 缩放控制
const zoomIn = () => {
  svg.value.transition().call(zoom.scaleBy, 1.2)
}

const zoomOut = () => {
  svg.value.transition().call(zoom.scaleBy, 0.8)
}

const resetZoom = () => {
  svg.value.transition().call(zoom.transform, d3.zoomIdentity)
}

// 在组件销毁时移除tooltip
onUnmounted(() => {
  d3.selectAll('.tooltip').remove()
})
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

.knowledge-graph-container {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  color: var(--text-primary);
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  position: relative;
  width: 100%;
  overflow-y: auto;
  min-height: 100vh;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-title {
  font-size: 2.2rem;
  margin-bottom: 0.5rem;
  font-weight: 700;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: inline-block;
}

.page-subtitle {
  font-size: 1.1rem;
  color: var(--text-secondary);
  margin-top: 0;
}

.video-selection-card,
.graph-display-card {
  margin-bottom: 20px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #ebeef5;
}

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
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}

.title-icon .el-icon {
  font-size: 18px;
  color: #ffffff;
}

.card-header h2 {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 600;
  color: #4338ca;
  position: relative;
  padding-bottom: 5px;
}

.card-header h2::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 40px;
  height: 3px;
  background: linear-gradient(to right, #6366f1, #a5b4fc);
  border-radius: 3px;
}

.selection-content {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.video-select {
  flex-grow: 1;
}

.graph-container {
  height: 700px;
  background-color: #f9fafb;
  border-radius: 8px;
  overflow: visible;
  position: relative;
}

.empty-graph {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.knowledge-detail {
  padding: 10px;
}

.knowledge-detail h3 {
  margin-top: 0;
  color: var(--indigo-600);
  font-size: 1.5rem;
}

.knowledge-actions {
  margin: 20px 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.knowledge-actions h4 {
  margin-bottom: 10px;
  color: var(--text-secondary);
}



/* 响应式设计 */
@media (max-width: 768px) {
  .selection-content {
    flex-direction: column;
    align-items: stretch;
  }

  .graph-container {
    height: 400px;
  }
}

.graph-svg-container {
  width: 100% !important; /* 确保容器占满可用空间 */
  height: 600px;
  background-color: #f9fafb;
  border-radius: 8px;
  overflow: visible;
}

/* 图例样式 */
.graph-legend {
  position: absolute;
  top: 10px;
  right: 10px;
  background-color: rgba(255, 255, 255, 0.9);
  padding: 10px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  z-index: 10;
  max-width: 200px;
}

.graph-legend h4 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 14px;
  color: #606266;
}

.legend-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  margin-right: 8px;
  display: inline-block;
}

.legend-line {
  width: 20px;
  border-top: 2px solid #999;
  margin-right: 8px;
  display: inline-block;
}

/* 生成中提示信息样式 */
.generating-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  min-height: 700px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.03);
  text-align: center;
}

.generating-content {
  max-width: 900px;
  width: 100%;
}

.generating-icon {
  margin-bottom: 1.5rem;
}

.generating-icon .el-icon {
  font-size: 3rem;
  color: #4F46E5;
  filter: drop-shadow(0 4px 6px rgba(79, 70, 229, 0.2));
}

.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.generating-title {
  font-size: 1.8rem;
  font-weight: 600;
  color: #4338ca;
  margin-bottom: 1.5rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.generating-progress {
  margin-bottom: 1.5rem;
  width: 100%;
}

.progress-bar {
  height: 8px;
  background-color: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
}

.progress-inner {
  height: 100%;
  width: 30%;
  background: linear-gradient(90deg, #4F46E5, #818CF8);
  border-radius: 4px;
  animation: progress 2s ease-in-out infinite alternate;
  box-shadow: 0 1px 3px rgba(79, 70, 229, 0.3);
}

@keyframes progress {
  0% {
    width: 10%;
  }
  100% {
    width: 70%;
  }
}

.generating-tip {
  font-size: 1rem;
  color: #6b7280;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.generating-steps {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  margin: 1rem 0 1.5rem 0;
  text-align: left;
  width: 100%;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 0.8rem;
  padding: 0.8rem;
  border-radius: 8px;
  background-color: rgba(255, 255, 255, 0.7);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  opacity: 0.7;
  transform: translateY(0);
  width: 100%;
}

.step-item.active {
  background-color: #ffffff;
  box-shadow: 0 4px 15px rgba(79, 70, 229, 0.15);
  opacity: 1;
  transform: translateY(-5px);
  border-left: 4px solid #4F46E5;
}

.step-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4F46E5, #818CF8);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 10px rgba(79, 70, 229, 0.3);
  flex-shrink: 0;
}

.step-icon .el-icon {
  font-size: 1.2rem;
}

.graph-icon {
  display: inline-block;
  width: 16px;
  height: 16px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z'/%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
}

.complete-icon {
  display: inline-block;
  width: 16px;
  height: 16px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z'/%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
}

.step-info h4 {
  margin: 0;
  font-size: 1rem;
  color: #1f2937;
  font-weight: 600;
  margin-bottom: 0.3rem;
}

.step-info p {
  margin: 0;
  font-size: 0.85rem;
  color: #6b7280;
  line-height: 1.3;
}

.generating-tips-container {
  margin-top: 1rem;
}

.tip-card {
  background-color: #eff6ff;
  border-radius: 8px;
  padding: 1rem 1.5rem;
  border-left: 4px solid #3b82f6;
  text-align: left;
  box-shadow: 0 2px 10px rgba(59, 130, 246, 0.1);
}

.tip-card h4 {
  margin: 0 0 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: #1e40af;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.tip-card p {
  margin: 0;
  font-size: 0.9rem;
  color: #3b4f7d;
  line-height: 1.6;
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
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  animation: fadeInUp 0.6s ease-out;
}

.subtitle {
  font-size: 1.1rem;
  font-weight: 400;
  margin-bottom: 0.5rem;
  opacity: 0.9;
  line-height: 1.6;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  animation: fadeInUp 0.8s ease-out;
}

.hero-description-container {
  margin-top: 0.5rem;
}

.hero-description {
  font-size: 1rem;
  color: white;
  opacity: 0.95;
  animation: fadeInUp 1s ease-out;
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
</style>
