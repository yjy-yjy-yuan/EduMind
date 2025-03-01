&lt;template>
  <div class="video-qa">
    <el-card class="qa-card">
      <template #header>
        <div class="card-header">
          <h3>智能问答</h3>
          <el-radio-group v-model="qaMode" size="small">
            <el-radio-button label="video">视频问答</el-radio-button>
            <el-radio-button label="chat">自由对话</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      
      <!-- 问答历史 -->
      <div class="qa-history" v-loading="loading">
        <el-timeline>
          <el-timeline-item
            v-for="qa in qaHistory"
            :key="qa.id"
            :timestamp="formatTime(qa.created_at)"
            placement="top"
          >
            <el-card class="qa-item">
              <h4>问：{{ qa.content }}</h4>
              <p>答：{{ qa.answer }}</p>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
      
      <!-- 提问表单 -->
      <div class="ask-form">
        <el-input
          v-model="question"
          type="textarea"
          :rows="3"
          :placeholder="qaMode === 'video' ? '请输入关于视频内容的问题...' : '请输入您的问题...'"
          :disabled="asking"
        />
        <div class="form-footer">
          <el-input
            v-model="apiKey"
            placeholder="请输入OpenAI API密钥"
            show-password
            style="width: 300px; margin-right: 10px;"
          />
          <el-button
            type="primary"
            @click="handleAsk"
            :loading="asking"
            :disabled="!question || !apiKey"
          >
            提问
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
&lt;/template>

&lt;script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { askQuestion, getQAHistory } from '@/api/qa'

const props = defineProps({
  videoId: {
    type: [Number, String],
    required: true
  }
})

// 状态
const question = ref('')
const apiKey = ref('')
const qaHistory = ref([])
const loading = ref(false)
const asking = ref(false)
const qaMode = ref('video')  // 问答模式：'video' 或 'chat'

// 方法
const formatTime = (isoString) => {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN')
}

const loadQAHistory = async () => {
  if (qaMode.value !== 'video') return
  
  loading.value = true
  try {
    const response = await getQAHistory(props.videoId)
    qaHistory.value = response.data
  } catch (error) {
    ElMessage.error('获取问答历史失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleAsk = async () => {
  if (!question.value || !apiKey.value) return
  
  asking.value = true
  try {
    const response = await askQuestion({
      video_id: qaMode.value === 'video' ? props.videoId : null,
      question: question.value,
      api_key: apiKey.value,
      mode: qaMode.value
    })
    
    // 添加新问答到历史记录
    if (qaMode.value === 'video') {
      qaHistory.value.unshift(response.data)
    } else {
      qaHistory.value.unshift({
        id: Date.now(),
        content: question.value,
        answer: response.data.answer,
        created_at: new Date().toISOString()
      })
    }
    
    // 清空问题输入
    question.value = ''
    
    ElMessage.success('回答成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '提问失败')
    console.error(error)
  } finally {
    asking.value = false
  }
}

// 监听问答模式变化
watch(qaMode, (newMode) => {
  qaHistory.value = []  // 清空历史记录
  if (newMode === 'video') {
    loadQAHistory()  // 加载视频问答历史
  }
})

// 生命周期
onMounted(() => {
  if (qaMode.value === 'video') {
    loadQAHistory()
  }
})
&lt;/script>

&lt;style scoped>
.video-qa {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}

.qa-history {
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 20px;
}

.qa-item {
  margin-bottom: 10px;
}

.qa-item h4 {
  margin: 0 0 10px 0;
  color: #409EFF;
}

.qa-item p {
  margin: 0;
  white-space: pre-wrap;
}

.ask-form {
  border-top: 1px solid #EBEEF5;
  padding-top: 20px;
}

.form-footer {
  display: flex;
  align-items: center;
  margin-top: 10px;
}
&lt;/style>
