<template>
  <div class="knowledge-graph-container">
    <div class="page-header">
      <h1 class="page-title">知识点总览</h1>
      <p class="page-subtitle">探索视频中的核心概念及其关联知识</p>
    </div>

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
        >
          <el-option 
            v-for="video in videoList" 
            :key="video.id" 
            :label="video.filename" 
            :value="video.id"
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
        <div v-if="!hasGraph && !isLoading" class="empty-graph">
          <el-empty description="暂无知识图谱数据，请选择视频并生成知识图谱" />
        </div>
        <div ref="graphContainer" class="graph-svg-container" style="width: 100%; height: 600px;"></div>
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
      <p v-if="selectedNode.description">{{ selectedNode.description }}</p>
      <div class="knowledge-actions">
        <h4>您想要：</h4>
        <el-button type="primary" @click="navigateToVideo">
          学习当前视频中的该知识点
        </el-button>
        <el-button type="success" @click="findBasicVideos" :loading="isSearchingBasic">
          查看该知识点的基础讲解
        </el-button>
        <el-button type="warning" @click="findAdvancedVideos" :loading="isSearchingAdvanced">
          深入研究该系列知识
        </el-button>
      </div>
      
      <!-- 搜索结果展示 -->
      <div v-if="searchResults.length > 0" class="search-results">
        <h4>相关视频：</h4>
        <el-table :data="searchResults" style="width: 100%">
          <el-table-column prop="title" label="标题" width="300" />
          <el-table-column prop="source" label="来源" width="100" />
          <el-table-column prop="duration" label="时长" width="100" />
          <el-table-column label="操作">
            <template #default="scope">
              <el-button type="primary" size="small" @click="openVideo(scope.row.url)">
                查看
              </el-button>
              <el-button type="success" size="small" @click="downloadVideo(scope.row.url)">
                下载
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { VideoCamera, Connection, ZoomIn, ZoomOut, Refresh } from '@element-plus/icons-vue'
import * as d3 from 'd3'
import { getVideoList } from '@/api/video'

// 状态变量
const router = useRouter()
const videoList = ref([])
const selectedVideo = ref('')
const isLoading = ref(false)
const isGenerating = ref(false)
const hasGraph = ref(false)
let checkFailCount = 0 // 检查失败次数
const graphContainer = ref(null)
const dialogVisible = ref(false)
const selectedNode = ref({})
const searchResults = ref([])
const isSearchingBasic = ref(false)
const isSearchingAdvanced = ref(false)

// 图谱相关变量
let svg = null
let simulation = null
let zoom = null
const graphData = ref({ nodes: [], links: [] })

// 初始化
onMounted(async () => {
  await loadVideoList()
})

// 加载视频列表
const loadVideoList = async () => {
  try {
    isLoading.value = true
    const { data } = await getVideoList()
    if (data && data.videos) {
      videoList.value = data.videos.filter(video => video.status === 'completed')
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
  
  try {
    isLoading.value = true
    hasGraph.value = false
    
    // 调用后端API获取知识图谱数据
    console.log(`请求知识图谱数据: /api/knowledge-graph/${selectedVideo.value}`)
    const response = await fetch(`/api/knowledge-graph/${selectedVideo.value}`)
    console.log('知识图谱响应状态码:', response.status)
    
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
          message: '正在为您生成知识图谱，这可能需要一分钟左右时间，请耐心等待',
          type: 'info',
          duration: 5000
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
      hasGraph.value = false
    }
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
    const statusResponse = await fetch(`/api/knowledge-graph/status/${selectedVideo.value}`)
    
    if (statusResponse.ok) {
      const statusData = await statusResponse.json()
      console.log(`[轮询#${pollId}] 知识图谱生成状态:`, statusData.status)
      
      // 如果任务已完成，尝试获取知识图谱数据
      if (statusData.status === 'completed') {
        console.log(`[轮询#${pollId}] 状态显示已完成，获取知识图谱数据`)
        
        try {
          // 尝试获取知识图谱数据
          const graphResponse = await fetch(`/api/knowledge-graph/${selectedVideo.value}`)
          
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
            console.log(`[轮询#${pollId}] 状态显示已完成，但无法获取知识图谱数据，状态码:`, graphResponse.status)
          }
        } catch (graphError) {
          console.error(`[轮询#${pollId}] 获取知识图谱数据出错:`, graphError)
        }
    
      // 如果任务失败
      if (statusData.status === 'failed') {
        console.error(`[轮询#${pollId}] 知识图谱生成失败`)
        isGenerating.value = false
        ElMessage.error('知识图谱生成失败，请重试')
        ElNotification.closeAll() // 关闭所有通知
        return
      }
      
      // 如果任务失败
      if (statusData.status === 'failed') {
        console.error(`[轮询#${pollId}] 知识图谱生成失败`)
        isGenerating.value = false
        ElMessage.error('知识图谱生成失败，请重试')
        ElNotification.closeAll() // 关闭所有通知
        return
      }
    }
    
    // 继续轮询
    console.log(`[轮询#${pollId}] 知识图谱仍在生成中，等待5秒后再次检查`)
    setTimeout(() => {
      checkStatusWithRetry(pollId, attempt + 1)
    }, 5000)
  } else {
    console.error(`[轮询#${pollId}] 状态检查API返回错误，状态码:`, statusResponse.status)
    // 即使状态检查API失败，也继续轮询
    setTimeout(() => {
      checkStatusWithRetry(pollId, attempt + 1)
    }, 5000)
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
    }, 5000)
  }
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
    
    // 调用后端API生成知识图谱
    const response = await fetch(`/api/knowledge-graph/generate/${selectedVideo.value}`, {
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
    ElNotification({
      title: '知识图谱生成中',
      message: '正在为您生成知识图谱，这可能需要一分钟左右时间，请耐心等待',
      type: 'info',
      duration: 0 // 不自动关闭
    })
    
    // 立即开始轮询
    console.log('开始轮询知识图谱生成状态...')
    pollKnowledgeGraphStatus()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('生成知识图谱失败:', error)
      ElMessage.error(error.message || '生成知识图谱失败')
      // 只在出错时才设置isGenerating为false，不影响轮询
      isGenerating.value = false
    }
  }
}

// 渲染图谱
const renderGraph = () => {
  console.log('开始渲染图谱...')
  if (!graphContainer.value) {
    console.error('图谱容器元素不存在')
    return
  }
  console.log('图谱数据:', graphData.value)
  if (!graphData.value || !graphData.value.nodes || !graphData.value.links) {
    console.error('无法渲染图谱：数据不完整')
    return
  }
  console.log('渲染图谱，节点数量:', graphData.value.nodes.length, '连接数量:', graphData.value.links.length)
  
  // 清除现有图谱
  d3.select(graphContainer.value).select('svg').remove()
  
  const width = graphContainer.value.clientWidth
  const height = 600
  
  // 创建SVG
  svg = d3.select(graphContainer.value)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', [0, 0, width, height])
    .attr('style', 'max-width: 100%; height: auto;')
  
  // 添加缩放功能
  zoom = d3.zoom()
    .scaleExtent([0.1, 3])
    .on('zoom', (event) => {
      container.attr('transform', event.transform)
    })
  
  svg.call(zoom)
  
  // 创建容器
  const container = svg.append('g')
  
  // 创建力导向图
  simulation = d3.forceSimulation(graphData.value.nodes)
    .force('link', d3.forceLink(graphData.value.links).id(d => d.id).distance(100))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(60))
  
  // 绘制连接线
  const link = container.append('g')
    .selectAll('line')
    .data(graphData.value.links)
    .join('line')
    .attr('stroke', '#999')
    .attr('stroke-opacity', 0.6)
    .attr('stroke-width', d => Math.sqrt(d.value || 1))
  
  // 绘制节点
  const node = container.append('g')
    .selectAll('.node')
    .data(graphData.value.nodes)
    .join('g')
    .attr('class', 'node')
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended))
    .on('click', handleNodeClick)
  
  // 节点圆形背景
  node.append('circle')
    .attr('r', d => d.main ? 30 : 20)
    .attr('fill', d => d.main ? '#4F46E5' : (d.expanded ? '#3CAEA3' : '#818CF8'))
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
  
  // 节点文本
  node.append('text')
    .text(d => d.label)
    .attr('x', 0)
    .attr('y', d => d.main ? 45 : 35)
    .attr('text-anchor', 'middle')
    .attr('fill', '#333')
    .style('font-size', d => d.main ? '14px' : '12px')
    .style('font-weight', d => d.main ? 'bold' : 'normal')
  
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
}

// 处理节点点击
const handleNodeClick = (event, d) => {
  selectedNode.value = d
  dialogVisible.value = true
  searchResults.value = []
}

// 导航到视频
const navigateToVideo = () => {
  if (!selectedNode.value.videoId || !selectedNode.value.timestamp) {
    ElMessage.warning('无法定位到视频中的知识点')
    return
  }
  
  router.push({
    path: `/player/${selectedNode.value.videoId}`,
    query: { t: selectedNode.value.timestamp }
  })
  
  dialogVisible.value = false
}

// 查找基础讲解视频
const findBasicVideos = async () => {
  if (!selectedNode.value || !selectedNode.value.label) {
    ElMessage.warning('请先选择一个知识点')
    return
  }
  
  try {
    isSearchingBasic.value = true
    searchResults.value = []
    
    // 调用后端API搜索基础讲解视频
    const response = await fetch('/api/knowledge-graph/search-videos', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        keyword: selectedNode.value.label,
        type: 'basic'
      })
    })
    
    if (!response.ok) {
      throw new Error('搜索视频失败')
    }
    
    const result = await response.json()
    searchResults.value = result.videos || []
    
    if (searchResults.value.length === 0) {
      ElMessage.info('未找到相关视频')
    }
  } catch (error) {
    console.error('搜索基础视频失败:', error)
    ElMessage.error('搜索基础视频失败')
  } finally {
    isSearchingBasic.value = false
  }
}

// 查找进阶视频
const findAdvancedVideos = async () => {
  if (!selectedNode.value || !selectedNode.value.label) {
    ElMessage.warning('请先选择一个知识点')
    return
  }
  
  try {
    isSearchingAdvanced.value = true
    searchResults.value = []
    
    // 获取相关知识点
    const relatedNodes = graphData.value.links
      .filter(link => link.source === selectedNode.value.id || link.target === selectedNode.value.id)
      .map(link => {
        const relatedId = link.source === selectedNode.value.id ? link.target : link.source
        return graphData.value.nodes.find(node => node.id === relatedId)
      })
      .filter(node => node)
      .map(node => node.label)
    
    // 调用后端API搜索进阶视频
    const response = await fetch('/api/knowledge-graph/search-videos', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        keyword: selectedNode.value.label,
        type: 'advanced',
        expanded: relatedNodes
      })
    })
    
    if (!response.ok) {
      throw new Error('搜索视频失败')
    }
    
    const result = await response.json()
    searchResults.value = result.videos || []
    
    if (searchResults.value.length === 0) {
      ElMessage.info('未找到相关视频')
    }
  } catch (error) {
    console.error('搜索进阶视频失败:', error)
    ElMessage.error('搜索进阶视频失败')
  } finally {
    isSearchingAdvanced.value = false
  }
}

// 打开视频
const openVideo = (url) => {
  window.open(url, '_blank')
}

// 下载视频
const downloadVideo = async (url) => {
  try {
    const response = await fetch(`/api/videos/download-external`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ url })
    })
    
    if (!response.ok) {
      throw new Error('下载请求失败')
    }
    
    ElMessage.success('视频下载请求已提交，请在视频管理页面查看进度')
  } catch (error) {
    console.error('下载视频失败:', error)
    ElMessage.error('下载视频失败')
  }
}

// 缩放控制
const zoomIn = () => {
  svg.transition().call(zoom.scaleBy, 1.2)
}

const zoomOut = () => {
  svg.transition().call(zoom.scaleBy, 0.8)
}

const resetZoom = () => {
  svg.transition().call(zoom.transform, d3.zoomIdentity)
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

.knowledge-graph-container {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  color: var(--text-primary);
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
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
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
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
  height: 600px;
  background-color: #f9fafb;
  border-radius: 8px;
  overflow: hidden;
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

.search-results {
  margin-top: 20px;
  border-top: 1px solid var(--border-color);
  padding-top: 20px;
}

.search-results h4 {
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
</style>
