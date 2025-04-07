<template>
  <div class="profile-container">
    <!-- 顶部个人资料卡片 -->
    <div class="profile-hero-section">
      <div class="hero-overlay"></div>
      <div class="hero-container">
        <div class="profile-header">
          <h1 class="main-title">我的个人资料</h1>
          <p class="subtitle">查看和管理您的个人信息和学习记录</p>
        </div>
      </div>
    </div>
    
    <div class="profile-content">
      <el-row :gutter="30">
        <!-- 左侧个人信息卡片 -->
        <el-col :xs="24" :sm="24" :md="8" :lg="6" :xl="6">
          <el-card class="profile-card" shadow="hover">
            <div class="avatar-container">
              <el-avatar :size="100" :src="userInfo.avatar || defaultAvatar">
                {{ userInfo.username ? userInfo.username.charAt(0).toUpperCase() : 'U' }}
              </el-avatar>
              <h2 class="username">{{ userInfo.username }}</h2>
              <p class="user-email">{{ userInfo.email }}</p>
            </div>
            
            <div class="user-info">
              <div class="info-item" v-if="userInfo.gender">
                <el-icon><User /></el-icon>
                <span>性别：{{ userInfo.gender }}</span>
              </div>
              <div class="info-item" v-if="userInfo.education">
                <el-icon><School /></el-icon>
                <span>学历：{{ userInfo.education }}</span>
              </div>
              <div class="info-item" v-if="userInfo.occupation">
                <el-icon><Briefcase /></el-icon>
                <span>职业：{{ userInfo.occupation }}</span>
              </div>
              <div class="info-item" v-if="userInfo.learning_direction">
                <el-icon><Compass /></el-icon>
                <span>学习方向：{{ userInfo.learning_direction }}</span>
              </div>
              <div class="info-item">
                <el-icon><Calendar /></el-icon>
                <span>注册时间：{{ formatDate(userInfo.created_at) }}</span>
              </div>
              <div class="info-item">
                <el-icon><Clock /></el-icon>
                <span>上次登录：{{ formatDate(userInfo.last_login) }}</span>
              </div>
            </div>
            
            <div class="user-bio" v-if="userInfo.bio">
              <h3>个人简介</h3>
              <p>{{ userInfo.bio }}</p>
            </div>
            
            <div class="profile-actions">
              <el-button type="primary" @click="showEditDialog" class="action-btn">
                <el-icon><Edit /></el-icon> 编辑资料
              </el-button>
              <el-button type="danger" @click="handleLogout" class="action-btn">
                <el-icon><SwitchButton /></el-icon> 退出登录
              </el-button>
            </div>
          </el-card>
        </el-col>
        
        <!-- 右侧内容区域 -->
        <el-col :xs="24" :sm="24" :md="16" :lg="18" :xl="18">
          <el-card class="tabs-card" shadow="hover">
            <el-tabs v-model="activeTab" class="profile-tabs">
              <!-- 个人信息标签页 -->
              <el-tab-pane label="个人信息" name="info">
                <div class="tab-header">
                  <h3>个人资料详情</h3>
                </div>
                
                <el-descriptions :column="2" border class="info-descriptions">
                  <el-descriptions-item label="用户名">{{ userInfo.username }}</el-descriptions-item>
                  <el-descriptions-item label="邮箱">{{ userInfo.email }}</el-descriptions-item>
                  <el-descriptions-item label="性别">{{ userInfo.gender || '未设置' }}</el-descriptions-item>
                  <el-descriptions-item label="学历">{{ userInfo.education || '未设置' }}</el-descriptions-item>
                  <el-descriptions-item label="职业">{{ userInfo.occupation || '未设置' }}</el-descriptions-item>
                  <el-descriptions-item label="学习方向">{{ userInfo.learning_direction || '未设置' }}</el-descriptions-item>
                  <el-descriptions-item label="注册时间">{{ formatDate(userInfo.created_at) }}</el-descriptions-item>
                  <el-descriptions-item label="上次登录">{{ formatDate(userInfo.last_login) }}</el-descriptions-item>
                  <el-descriptions-item label="个人简介" :span="2">
                    {{ userInfo.bio || '未设置个人简介' }}
                  </el-descriptions-item>
                </el-descriptions>
              </el-tab-pane>
              
              <!-- 笔记管理标签页 -->
              <el-tab-pane label="笔记管理" name="notes">
                <div class="tab-header">
                  <h3>我的笔记</h3>
                </div>
                
                <div class="empty-placeholder" v-if="!notes.length">
                  <el-empty description="暂无笔记记录">
                    <el-button type="primary">去创建笔记</el-button>
                  </el-empty>
                </div>
                
                <el-table v-else :data="notes" style="width: 100%">
                  <el-table-column prop="title" label="标题" width="180"></el-table-column>
                  <el-table-column prop="video_title" label="关联视频" width="180"></el-table-column>
                  <el-table-column prop="created_at" label="创建时间"></el-table-column>
                  <el-table-column label="操作" width="150">
                    <template #default="scope">
                      <el-button size="small" @click="viewNote(scope.row)">查看</el-button>
                      <el-button size="small" type="danger" @click="deleteNote(scope.row)">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </el-tab-pane>
              
              <!-- 总结记录标签页 -->
              <el-tab-pane label="总结记录" name="summaries">
                <div class="tab-header">
                  <h3>我的总结</h3>
                </div>
                
                <div class="empty-placeholder" v-if="!summaries.length">
                  <el-empty description="暂无总结记录">
                    <el-button type="primary">去创建总结</el-button>
                  </el-empty>
                </div>
                
                <el-table v-else :data="summaries" style="width: 100%">
                  <el-table-column prop="title" label="标题" width="180"></el-table-column>
                  <el-table-column prop="video_title" label="关联视频" width="180"></el-table-column>
                  <el-table-column prop="created_at" label="创建时间"></el-table-column>
                  <el-table-column label="操作" width="150">
                    <template #default="scope">
                      <el-button size="small" @click="viewSummary(scope.row)">查看</el-button>
                      <el-button size="small" type="danger" @click="deleteSummary(scope.row)">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </el-tab-pane>
              
              <!-- 学习知识点标签页 -->
              <el-tab-pane label="学习知识点" name="knowledge">
                <div class="tab-header">
                  <h3>我的知识点</h3>
                </div>
                
                <div class="empty-placeholder" v-if="!knowledgePoints.length">
                  <el-empty description="暂无知识点记录">
                    <el-button type="primary">去学习</el-button>
                  </el-empty>
                </div>
                
                <el-timeline v-else>
                  <el-timeline-item
                    v-for="(point, index) in knowledgePoints"
                    :key="index"
                    :timestamp="formatDate(point.created_at)"
                    placement="top"
                  >
                    <el-card>
                      <h4>{{ point.title }}</h4>
                      <p>{{ point.content }}</p>
                      <p class="knowledge-source">来源视频：{{ point.video_title }}</p>
                    </el-card>
                  </el-timeline-item>
                </el-timeline>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </el-col>
      </el-row>
    </div>
    
    <!-- 编辑个人信息对话框 -->
    <el-dialog
      title="编辑个人信息"
      v-model="editDialogVisible"
      width="500px"
    >
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="editForm.username"></el-input>
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email"></el-input>
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="editForm.gender" placeholder="请选择性别" style="width: 100%">
            <el-option label="男" value="男"></el-option>
            <el-option label="女" value="女"></el-option>
            <el-option label="其他" value="其他"></el-option>
            <el-option label="不愿透露" value="不愿透露"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="学历">
          <el-select v-model="editForm.education" placeholder="请选择学历" style="width: 100%">
            <el-option label="高中及以下" value="高中及以下"></el-option>
            <el-option label="专科" value="专科"></el-option>
            <el-option label="本科" value="本科"></el-option>
            <el-option label="硕士" value="硕士"></el-option>
            <el-option label="博士" value="博士"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="职业">
          <el-select v-model="editForm.occupation" placeholder="请选择职业" style="width: 100%">
            <el-option label="学生" value="学生"></el-option>
            <el-option label="教师" value="教师"></el-option>
            <el-option label="IT/互联网" value="IT/互联网"></el-option>
            <el-option label="金融" value="金融"></el-option>
            <el-option label="医疗" value="医疗"></el-option>
            <el-option label="其他" value="其他"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="学习方向">
          <el-select v-model="editForm.learning_direction" placeholder="请选择学习方向" style="width: 100%">
            <el-option label="高等数学" value="高等数学"></el-option>
            <el-option label="线性代数" value="线性代数"></el-option>
            <el-option label="英语" value="英语"></el-option>
            <el-option label="计算机科学" value="计算机科学"></el-option>
            <el-option label="物理" value="物理"></el-option>
            <el-option label="化学" value="化学"></el-option>
            <el-option label="生物" value="生物"></el-option>
            <el-option label="经济学" value="经济学"></el-option>
            <el-option label="其他" value="其他"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="个人简介">
          <el-input 
            v-model="editForm.bio" 
            type="textarea" 
            placeholder="请简单介绍一下自己" 
            :rows="3"
          ></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="updateUserInfo" :loading="updating">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import authStore from '../store/auth'
import { 
  User, School, Briefcase, Compass, Calendar, Clock, 
  Edit, SwitchButton 
} from '@element-plus/icons-vue'

const router = useRouter()
const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'

// 用户信息
const userInfo = ref({})
const editDialogVisible = ref(false)
const updating = ref(false)
const editForm = reactive({
  username: '',
  email: '',
  gender: '',
  education: '',
  occupation: '',
  learning_direction: '',
  bio: ''
})

// 标签页
const activeTab = ref('info')

// 模拟数据
const notes = ref([])
const summaries = ref([])
const knowledgePoints = ref([])

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const response = await axios.get('/api/auth/user')
    if (response.data.success) {
      // 确保所有字段都有默认值
      userInfo.value = {
        username: '',
        email: '',
        gender: '',
        education: '',
        occupation: '',
        learning_direction: '',
        bio: '',
        created_at: null,
        last_login: null,
        ...response.data.user
      }
    } else {
      ElMessage.error(response.data.message || '获取用户信息失败')
      router.push('/login')
    }
  } catch (error) {
    console.error('获取用户信息错误:', error)
    ElMessage.error('获取用户信息失败，请重新登录')
    router.push('/login')
  }
}

// 显示编辑对话框
const showEditDialog = () => {
  // 复制当前用户信息到编辑表单
  Object.keys(editForm).forEach(key => {
    editForm[key] = userInfo.value[key] || ''
  })
  editDialogVisible.value = true
}

// 更新用户信息
const updateUserInfo = async () => {
  if (!editForm.username || !editForm.email) {
    ElMessage.warning('用户名和邮箱不能为空')
    return
  }
  
  updating.value = true
  
  try {
    const response = await axios.put('/api/auth/user', editForm)
    
    if (response.data.success) {
      // 更新本地用户信息
      userInfo.value = {
        ...userInfo.value,
        ...editForm
      }
      
      ElMessage.success('个人信息更新成功')
      editDialogVisible.value = false
    } else {
      ElMessage.error(response.data.message || '更新失败')
    }
  } catch (error) {
    console.error('更新用户信息错误:', error)
    ElMessage.error(error.response?.data?.message || '更新失败，请稍后再试')
  } finally {
    updating.value = false
  }
}

// 退出登录
const handleLogout = () => {
  ElMessageBox.confirm(
    '确定要退出登录吗？',
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        const response = await axios.post('/api/auth/logout')
        
        if (response.data.success) {
          // 清除本地存储的用户信息
          authStore.clearAuth()
          
          ElMessage.success('退出成功')
          router.push('/login')
        } else {
          ElMessage.error(response.data.message || '退出失败')
        }
      } catch (error) {
        console.error('退出登录错误:', error)
        ElMessage.error('退出失败，请稍后再试')
      }
    })
    .catch(() => {
      // 取消退出
    })
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '未知'
  
  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return dateString
  }
}

// 笔记相关方法
const viewNote = (note) => {
  // 查看笔记的实现
  console.log('查看笔记', note)
}

const deleteNote = (note) => {
  ElMessageBox.confirm('确定要删除这条笔记吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    // 删除笔记的实现
    console.log('删除笔记', note)
  })
}

// 总结相关方法
const viewSummary = (summary) => {
  // 查看总结的实现
  console.log('查看总结', summary)
}

const deleteSummary = (summary) => {
  ElMessageBox.confirm('确定要删除这条总结吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    // 删除总结的实现
    console.log('删除总结', summary)
  })
}

// 页面加载时获取用户信息
onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
/* 基本样式 */
.profile-container {
  min-height: 100vh;
  background-color: #f5f8fa;
}

/* 顶部英雄区域 */
.profile-hero-section {
  position: relative;
  padding: 60px 20px;
  background-image: url('https://public.readdy.ai/ai/img_res/b2856a465ee244a4bb2ffa4b39614527.jpg');
  background-size: cover;
  background-position: center;
  color: #fff;
  overflow: hidden;
}

.hero-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.hero-container {
  position: relative;
  z-index: 2;
  max-width: 1200px;
  margin: 0 auto;
}

.profile-header {
  text-align: center;
  margin-bottom: 1rem;
}

.main-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  letter-spacing: -0.5px;
  line-height: 1.2;
  animation: fadeInDown 1s ease-out;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.subtitle {
  font-size: 1.25rem;
  margin-bottom: 1.5rem;
  line-height: 1.6;
  max-width: 700px;
  margin-left: auto;
  margin-right: auto;
  animation: fadeInUp 1s ease-out 0.3s both;
}

/* 内容区域 */
.profile-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
  margin-top: -40px;
  position: relative;
  z-index: 10;
}

/* 个人信息卡片 */
.profile-card {
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  overflow: hidden;
  margin-bottom: 20px;
}

.profile-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
}

.avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
  border-bottom: 1px solid #f0f0f0;
}

.username {
  margin: 15px 0 5px;
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
}

.user-email {
  color: #666;
  font-size: 0.9rem;
  margin: 0;
}

.user-info {
  padding: 20px;
}

.info-item {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  color: #555;
}

.info-item .el-icon {
  margin-right: 10px;
  color: #667eea;
}

.user-bio {
  padding: 0 20px 20px;
  border-top: 1px solid #f0f0f0;
}

.user-bio h3 {
  font-size: 1.1rem;
  color: #333;
  margin: 15px 0 10px;
}

.user-bio p {
  color: #666;
  line-height: 1.6;
  margin: 0;
}

.profile-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0 20px 20px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 40px;
  transition: all 0.3s ease;
}

.action-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

/* 标签页卡片 */
.tabs-card {
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.profile-tabs {
  padding: 20px;
}

.tab-header {
  margin-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 10px;
}

.tab-header h3 {
  font-size: 1.2rem;
  color: #333;
  margin: 0;
}

.info-descriptions {
  margin-top: 20px;
}

.empty-placeholder {
  padding: 40px 0;
  text-align: center;
}

.knowledge-source {
  font-size: 0.85rem;
  color: #999;
  margin-top: 10px;
}

/* 动画效果 */
@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
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

/* 响应式调整 */
@media (max-width: 768px) {
  .profile-hero-section {
    padding: 40px 15px;
  }
  
  .main-title {
    font-size: 2rem;
  }
  
  .subtitle {
    font-size: 1rem;
  }
  
  .profile-content {
    padding: 20px 15px;
  }
}
</style>
