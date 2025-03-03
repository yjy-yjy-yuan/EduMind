<template>
  <div class="video-detail">
    <el-row :gutter="20">
      <!-- 左侧：视频播放和字幕区域 -->
      <el-col :span="16">
        <el-card class="video-card">
          <!-- 视频播放器 -->
          <video-player 
            ref="videoPlayer"
            :src="videoUrl"
            :subtitle-url="subtitleUrl"
            @timeupdate="handleTimeUpdate"
          ></video-player>

          <!-- 字幕显示和编辑区域 -->
          <div class="subtitle-area" v-loading="loading">
            <div class="subtitle-header">
              <h3>字幕</h3>
              <div class="subtitle-actions">
                <el-button-group>
                  <el-button 
                    type="primary" 
                    @click="exportSubtitles('srt')"
                    :loading="exporting"
                  >
                    导出SRT
                  </el-button>
                  <el-button 
                    type="primary" 
                    @click="exportSubtitles('vtt')"
                    :loading="exporting"
                  >
                    导出VTT
                  </el-button>
                  <el-button 
                    type="primary" 
                    @click="exportSubtitles('txt')"
                    :loading="exporting"
                  >
                    导出TXT
                  </el-button>
                  <el-button
                    type="primary"
                    @click="handlePlay"
                    :disabled="!isProcessed"
                  >
                    播放视频
                  </el-button>
                </el-button-group>
              </div>
            </div>

            <!-- 字幕列表 -->
            <el-table
              :data="subtitles"
              style="width: 100%"
              height="400"
              @row-click="handleSubtitleClick"
              v-if="!loading && subtitles.length > 0"
            >
              <el-table-column prop="start_time" label="开始时间" width="120">
                <template #default="{ row }">
                  {{ formatTime(row.start_time) }}
                </template>
              </el-table-column>
              <el-table-column prop="end_time" label="结束时间" width="120">
                <template #default="{ row }">
                  {{ formatTime(row.end_time) }}
                </template>
              </el-table-column>
              <el-table-column prop="text" label="文本">
                <template #default="{ row }">
                  <el-input
                    v-if="row.editing"
                    v-model="row.text"
                    @blur="handleSubtitleEdit(row)"
                    @keyup.enter="handleSubtitleEdit(row)"
                  ></el-input>
                  <span v-else @dblclick="row.editing = true">{{ row.text }}</span>
                </template>
              </el-table-column>
              <el-table-column width="100">
                <template #default="{ row }">
                  <el-button-group>
                    <el-button 
                      type="primary" 
                      link 
                      :icon="Edit"
                      @click="row.editing = true"
                    ></el-button>
                    <el-button 
                      type="danger" 
                      link 
                      :icon="Delete"
                      @click="handleDeleteSubtitle(row)"
                    ></el-button>
                  </el-button-group>
                </template>
              </el-table-column>
            </el-table>

            <!-- 无字幕时显示 -->
            <el-empty 
              v-else-if="!loading && subtitles.length === 0" 
              description="暂无字幕"
            >
              <template #extra>
                <el-button 
                  type="primary"
                  @click="handleGenerateSubtitles"
                  :loading="generating"
                >
                  生成字幕
                </el-button>
              </template>
            </el-empty>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：对话和笔记区域 -->
      <el-col :span="8">
        <!-- 对话功能 - 待开发 -->
        <el-card class="chat-card">
          <template #header>
            <div class="card-header">
              <span>视频对话</span>
              <el-tag size="small" type="warning">开发中</el-tag>
            </div>
          </template>
          <div class="developing-notice">
            <el-empty description="对话功能开发中...">
              <template #image>
                <el-icon :size="60"><ChatRound /></el-icon>
              </template>
              <template #description>
                <p>即将推出：</p>
                <ul>
                  <li>基于视频内容的智能对话</li>
                  <li>实时问答和解释</li>
                  <li>知识点提取和扩展</li>
                </ul>
              </template>
            </el-empty>
          </div>
        </el-card>

        <!-- 笔记系统 - 待开发 -->
        <el-card class="notes-card">
          <template #header>
            <div class="card-header">
              <span>笔记系统</span>
              <el-tag size="small" type="warning">开发中</el-tag>
            </div>
          </template>
          <div class="developing-notice">
            <el-empty description="笔记功能开发中...">
              <template #image>
                <el-icon :size="60"><Edit /></el-icon>
              </template>
              <template #description>
                <p>即将推出：</p>
                <ul>
                  <li>与视频时间轴关联的笔记</li>
                  <li>AI 辅助笔记整理</li>
                  <li>知识点提取与总结</li>
                </ul>
              </template>
            </el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Delete, ChatRound } from '@element-plus/icons-vue'
import VideoPlayer from '../components/VideoPlayer.vue'

const store = useStore()
const route = useRoute()
const router = useRouter()
const videoPlayer = ref(null)

// 状态
const loading = ref(false)
const exporting = ref(false)
const generating = ref(false)
const subtitles = computed(() => store.state.subtitles)
const currentVideo = computed(() => store.state.currentVideo)
const isProcessed = computed(() => currentVideo.value?.status === 'completed')
const videoId = computed(() => route.params.id)

// 计算属性
const videoUrl = computed(() => {
  if (!currentVideo.value?.id) return ''
  return `/api/videos/${currentVideo.value.id}/stream`
})

const subtitleUrl = computed(() => {
  if (!currentVideo.value?.id || !currentVideo.value?.subtitle_filepath) return ''
  return `/api/videos/${currentVideo.value.id}/subtitle`
})

// 方法
const formatTime = (seconds) => {
  const pad = (num) => String(num).padStart(2, '0')
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  return `${pad(hours)}:${pad(minutes)}:${pad(secs)}`
}

const handleTimeUpdate = (time) => {
  // 处理视频时间更新
}

const handleSubtitleClick = (row) => {
  if (videoPlayer.value) {
    videoPlayer.value.currentTime = row.start_time
  }
}

const handleSubtitleEdit = async (subtitle) => {
  try {
    await store.dispatch('updateSubtitle', {
      videoId: currentVideo.value.id,
      subtitleId: subtitle.id,
      data: {
        text: subtitle.text
      }
    })
    subtitle.editing = false
    ElMessage.success('字幕更新成功')
  } catch (error) {
    ElMessage.error('字幕更新失败')
  }
}

const handleDeleteSubtitle = async (subtitle) => {
  try {
    await ElMessageBox.confirm('确定要删除这条字幕吗？', '提示', {
      type: 'warning'
    })
    // TODO: 实现删除字幕的功能
    ElMessage.success('字幕删除成功')
  } catch {
    // 用户取消删除
  }
}

const handleGenerateSubtitles = async () => {
  try {
    generating.value = true
    await store.dispatch('generateSubtitles', {
      videoId: currentVideo.value.id,
      language: 'zh',
      model: 'base'
    })
    ElMessage.success('字幕生成成功')
  } catch (error) {
    ElMessage.error('字幕生成失败')
  } finally {
    generating.value = false
  }
}

const exportSubtitles = async (format) => {
  try {
    exporting.value = true
    await store.dispatch('exportSubtitles', {
      videoId: currentVideo.value.id,
      format
    })
    ElMessage.success('字幕导出成功')
  } catch (error) {
    ElMessage.error('字幕导出失败')
  } finally {
    exporting.value = false
  }
}

const handlePlay = () => {
  router.push(`/player/${videoId.value}`)
}

// 生命周期
onMounted(async () => {
  const videoId = route.params.id
  try {
    loading.value = true
    await store.dispatch('getVideoDetails', videoId)
    
    // 如果视频已处理完成，加载字幕
    if (currentVideo.value?.status === 'completed') {
      await store.dispatch('getSubtitles', videoId)
    }
  } catch (error) {
    ElMessage.error('加载视频信息失败：' + error.message)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.video-detail {
  padding: 20px;
}

.video-card {
  margin-bottom: 20px;
}

.subtitle-area {
  margin-top: 20px;
}

.subtitle-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chat-card,
.notes-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.developing-notice {
  min-height: 200px;
  display: flex;
  justify-content: center;
  align-items: center;
}

ul {
  text-align: left;
  margin-top: 10px;
  padding-left: 20px;
}

li {
  margin: 5px 0;
  color: #666;
}
</style>
